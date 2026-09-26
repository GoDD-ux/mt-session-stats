# -*- coding: utf-8 -*-
"""Разбор полной формы результатов боя (BattleResultsCache.convertToFullForm).

Модуль не зависит от клиента: имена техники и карт передаются снаружи,
поэтому его можно тестировать обычным pytest/unittest.
"""
from .models import BattleRecord, UNKNOWN_VEHICLE, WIN, LOSS, DRAW

# поле в результатах -> наш счётчик
_FIELDS = {
    'damageDealt': 'damage',
    'damageBlockedByArmor': 'blocked',
    'kills': 'kills',
    'spotted': 'spotted',
    'shots': 'shots',
    'directHits': 'hits',
    'piercings': 'piercings',
    'xp': 'xp',
    'credits': 'credits',
}
_ASSIST_FIELDS = ('damageAssistedRadio', 'damageAssistedTrack', 'damageAssistedStun')


def arena_start_time(arena_id):
    # младшие 32 бита arenaUniqueID - время создания арены
    return arena_id & 0xFFFFFFFF


def battle_result(team, winner_team):
    if not winner_team:
        return DRAW
    return WIN if winner_team == team else LOSS


def parse_results(results, describe_vehicle=None, describe_map=None):
    """Возвращает BattleRecord или None, если в результатах нет своей техники."""
    common = results.get('common') or {}
    personal = results.get('personal') or {}
    own = [(cd, data) for cd, data in personal.items() if cd != 'avatar' and data]
    if not own:
        return None

    counters = dict.fromkeys(list(_FIELDS.values()) + ['assist'], 0)
    for _, data in own:
        for field, name in _FIELDS.items():
            counters[name] += data.get(field) or 0
        counters['assist'] += sum(data.get(field) or 0 for field in _ASSIST_FIELDS)

    # в обычном бою техника одна; в режимах с несколькими машинами берём первую для подписи
    cd, first = own[0]
    team = first.get('team') or (personal.get('avatar') or {}).get('team', 0)
    arena_id = results.get('arenaUniqueID', 0)

    vehicle = describe_vehicle(cd) if describe_vehicle else None
    map_name = describe_map(common.get('arenaTypeID', 0)) if describe_map else u''

    return BattleRecord(
        arena_id=arena_id,
        started_at=common.get('arenaCreateTime') or arena_start_time(arena_id),
        result=battle_result(team, common.get('winnerTeam', 0)),
        vehicle=vehicle or UNKNOWN_VEHICLE._replace(cd=cd),
        map_name=map_name,
        **counters
    )
