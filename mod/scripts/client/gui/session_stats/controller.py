# -*- coding: utf-8 -*-
import json
import logging
import os
import time
from functools import partial
from Queue import Empty, Queue

import AccountCommands
import ArenaType
import BigWorld
import ResMgr
from PlayerEvents import g_playerEvents
from chat_shared import SYS_MESSAGE_TYPE
from gui import SystemMessages
from helpers import dependency, i18n
from messenger.proto.events import g_messengerEvents
from skeletons.gui.shared import IItemsCache

from .metrics import METRICS
from .models import Session, Vehicle
from .parser import arena_start_time, parse_results
from .server import ApiServer

logger = logging.getLogger('session_stats')

MOD_ID = 'godd.session_stats'
CONFIG_DIR = os.path.join('mods', 'configs', 'session_stats')
UI_ROOT = 'gui/session_stats'
ICON = 'gui/maps/session_stats/icon.png'

DEFAULT_CONFIG = {
    'port': 16150,
    # если не играл дольше - при запуске начинается новая сессия
    'sessionIdleHours': 4,
    'notifyAfterBattle': True,
}

# сколько раз и с какой паузой пробовать забрать результаты, если кэш занят клиентом
FETCH_DELAY = 3.0
FETCH_ATTEMPTS = 5


class SessionController(object):
    itemsCache = dependency.descriptor(IItemsCache)

    def __init__(self):
        self.config = dict(DEFAULT_CONFIG)
        self.session = None
        self.commands = Queue()
        self.server = None
        self._snapshot = b'{}'
        self._tickID = None
        self._pending = set()

    def start(self):
        self.config.update(self._readJson('config.json') or {})
        self._writeJson('config.json', self.config)
        self.session = self._restoreSession()
        self._refreshSnapshot()

        self.server = ApiServer(lambda: self._snapshot, self.commands, _loadStaticFiles(UI_ROOT))
        try:
            self.server.start(self.config['port'])
            logger.info('ui is available at %s', self.server.url)
        except Exception:
            logger.exception('cannot start http server')
            self.server = None

        g_messengerEvents.serviceChannel.onChatMessageReceived += self._onChatMessage
        g_playerEvents.onAccountShowGUI += self._onAccountShowGUI
        self._registerInModsList()
        self._tick()

    def stop(self):
        g_messengerEvents.serviceChannel.onChatMessageReceived -= self._onChatMessage
        g_playerEvents.onAccountShowGUI -= self._onAccountShowGUI
        if self._tickID is not None:
            BigWorld.cancelCallback(self._tickID)
            self._tickID = None
        if self.server is not None:
            self.server.stop()
            self.server = None

    def openPanel(self):
        if self.server is None:
            SystemMessages.pushMessage(u'Итоги сессии: не удалось запустить локальный сервер, '
                                       u'подробности в python.log', type=SystemMessages.SM_TYPE.Error)
            return
        # встроенный браузер клиента пускает только адреса из своего списка (на остальные отдаёт 418),
        # поэтому панель открывается в обычном браузере
        BigWorld.openWebBrowser(self.server.url)

    def resetSession(self):
        self.session = Session()
        self._pending.clear()
        self._onSessionChanged()

    # --- результаты боёв ---

    def _onChatMessage(self, _, message):
        if message.type != SYS_MESSAGE_TYPE.battleResults.index():
            return
        arenaID = (message.data or {}).get('arenaUniqueID')
        if not arenaID or arenaID in self.session or arenaID in self._pending:
            return
        # при входе в игру сервер присылает старые сообщения - их не считаем
        if arena_start_time(arenaID) < self.session.started_at:
            return
        self._pending.add(arenaID)
        # клиент в этот момент сам запрашивает результаты, даём ему закончить,
        # тогда наш запрос возьмёт их из локального кэша
        BigWorld.callback(FETCH_DELAY, partial(self._fetch, arenaID, 1))

    def _fetch(self, arenaID, attempt):
        if arenaID not in self._pending:
            return
        cache = getattr(BigWorld.player(), 'battleResultsCache', None)
        if cache is None:
            # игрок уже в следующем бою, заберём результаты по возвращении в ангар
            return
        cache.get(arenaID, partial(self._onResults, arenaID, attempt))

    def _onResults(self, arenaID, attempt, code, results):
        if code in (AccountCommands.RES_STREAM, AccountCommands.RES_CACHE) and results:
            self._pending.discard(arenaID)
            try:
                record = parse_results(results, self._describeVehicle, _mapName)
            except Exception:
                logger.exception('cannot parse results of %s', arenaID)
                return
            if record is not None and self.session.add(record):
                self._onSessionChanged()
                self._notify()
            return
        self._retry(arenaID, attempt, 'code %s' % code)

    def _retry(self, arenaID, attempt, reason):
        if attempt >= FETCH_ATTEMPTS:
            self._pending.discard(arenaID)
            logger.warning('gave up on battle %s: %s', arenaID, reason)
            return
        BigWorld.callback(FETCH_DELAY * attempt, partial(self._fetch, arenaID, attempt + 1))

    def _onAccountShowGUI(self, *_):
        for arenaID in self._pending:
            BigWorld.callback(FETCH_DELAY, partial(self._fetch, arenaID, 1))

    def _describeVehicle(self, intCD):
        item = self.itemsCache.items.getItemByCD(intCD)
        if item is None:
            return None
        return Vehicle(intCD, item.shortUserName, item.level, item.type)

    # --- состояние ---

    def _onSessionChanged(self):
        self._writeJson('session.json', self.session.dump())
        self._refreshSnapshot()

    def _refreshSnapshot(self):
        # сервер читает только эту строку, поэтому гонок с основным потоком нет
        self._snapshot = json.dumps(self.session.summary(METRICS))

    def _restoreSession(self):
        data = self._readJson('session.json')
        if data:
            try:
                session = Session.load(data)
            except Exception:
                logger.exception('broken session.json, starting new session')
            else:
                if not session.is_stale(time.time(), self.config['sessionIdleHours'] * 3600):
                    return session
        return Session()

    def _tick(self):
        # команды из http-потока выполняем в основном потоке игры
        self._tickID = BigWorld.callback(0.5, self._tick)
        while True:
            try:
                command = self.commands.get_nowait()
            except Empty:
                break
            if command == 'reset':
                self.resetSession()

    # --- уведомления и кнопка ---

    def _notify(self):
        if not self.config['notifyAfterBattle']:
            return
        metrics = dict((m['key'], m['text']) for m in self.session.summary(METRICS)['metrics'])
        text = (u'<font color="#E9C46A"><b>Итоги сессии</b></font><br>'
                u'Боёв: {battles}, побед: {winRate}<br>'
                u'Средний урон: {avgDamage}, ассист: {avgAssist}').format(**metrics)
        SystemMessages.pushMessage(text, type=SystemMessages.SM_TYPE.Information)

    def _registerInModsList(self):
        try:
            from gui.modsListApi import g_modsListApi
        except ImportError:
            logger.info('modsListApi is not installed, panel button is disabled')
            return
        g_modsListApi.addModification(
            id=MOD_ID,
            name=u'Итоги сессии',
            description=u'Статистика боёв с момента входа в игру',
            icon=ICON,
            enabled=True,
            login=False,
            lobby=True,
            callback=self.openPanel)

    def _readJson(self, name):
        path = os.path.join(CONFIG_DIR, name)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, 'rb') as f:
                return json.load(f)
        except ValueError:
            logger.warning('cannot read %s', path)
            return None

    def _writeJson(self, name, data):
        if not os.path.isdir(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        path = os.path.join(CONFIG_DIR, name)
        with open(path + '.tmp', 'wb') as f:
            json.dump(data, f, indent=2, sort_keys=True)
        # на windows os.rename не перезаписывает файл
        if os.path.exists(path):
            os.remove(path)
        os.rename(path + '.tmp', path)


def _mapName(arenaTypeID):
    arenaType = ArenaType.g_cache.get(arenaTypeID)
    if arenaType is None:
        return u''
    return i18n.makeString(arenaType.name)


def _loadStaticFiles(root):
    """Файлы интерфейса лежат внутри .mtmod, читаем их через ResMgr один раз при старте."""
    files = {}

    def walk(path, prefix):
        section = ResMgr.openSection(path)
        if section is None:
            return
        for name in section.keys():
            fullPath = path + '/' + name
            if ResMgr.isFile(fullPath):
                files[prefix + name] = ResMgr.openSection(fullPath).asBinary
            else:
                walk(fullPath, prefix + name + '/')

    walk(root, '')
    if 'index.html' not in files:
        logger.error('ui files not found in %s', root)
    return files


g_controller = SessionController()
