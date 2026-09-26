# -*- coding: utf-8 -*-
import time
from collections import OrderedDict, namedtuple

WIN, LOSS, DRAW = 'win', 'loss', 'draw'

COUNTERS = ('damage', 'assist', 'blocked', 'kills', 'spotted',
            'shots', 'hits', 'piercings', 'xp', 'credits')

Vehicle = namedtuple('Vehicle', 'cd name tier kind')
UNKNOWN_VEHICLE = Vehicle(0, u'?', 0, '')


class Totals(object):
    """Сумма показателей по нескольким боям. Складывается через +, поэтому работает sum()."""

    __slots__ = ('battles', 'wins', 'losses', 'draws') + COUNTERS

    def __init__(self, **values):
        for name in self.__slots__:
            setattr(self, name, values.pop(name, 0))
        if values:
            raise TypeError('unknown fields: %s' % ', '.join(sorted(values)))

    def __add__(self, other):
        if not isinstance(other, Totals):
            return NotImplemented
        return Totals(**dict((name, getattr(self, name) + getattr(other, name))
                             for name in self.__slots__))

    def __radd__(self, other):
        # sum() начинает с 0
        if other == 0:
            return self
        return self.__add__(other)

    def __eq__(self, other):
        if not isinstance(other, Totals):
            return NotImplemented
        return self.as_dict() == other.as_dict()

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    __hash__ = None

    def __repr__(self):
        return 'Totals(battles=%d, wins=%d, damage=%d)' % (self.battles, self.wins, self.damage)

    def as_dict(self):
        return dict((name, getattr(self, name)) for name in self.__slots__)


class BattleRecord(object):

    def __init__(self, arena_id, started_at, result, vehicle, map_name=u'', **counters):
        self.arena_id = arena_id
        self.started_at = started_at
        self.result = result
        self.vehicle = vehicle
        self.map_name = map_name
        self.counters = dict((name, counters.get(name, 0)) for name in COUNTERS)

    @property
    def totals(self):
        return Totals(battles=1,
                      wins=int(self.result == WIN),
                      losses=int(self.result == LOSS),
                      draws=int(self.result == DRAW),
                      **self.counters)

    def to_dict(self):
        data = {
            'arenaId': str(self.arena_id),
            'startedAt': self.started_at,
            'result': self.result,
            'map': self.map_name,
            'vehicle': self.vehicle._asdict(),
        }
        data.update(self.counters)
        return data

    @classmethod
    def from_dict(cls, data):
        counters = dict((name, data.get(name, 0)) for name in COUNTERS)
        return cls(int(data['arenaId']), data['startedAt'], data['result'],
                   Vehicle(**data['vehicle']), data.get('map', u''), **counters)


class Session(object):

    def __init__(self, started_at=None):
        self.started_at = started_at or int(time.time())
        self._records = OrderedDict()

    def __len__(self):
        return len(self._records)

    def __iter__(self):
        return iter(self._records.values())

    def __contains__(self, arena_id):
        return arena_id in self._records

    def __iadd__(self, record):
        self.add(record)
        return self

    def add(self, record):
        if record.arena_id in self._records:
            return False
        self._records[record.arena_id] = record
        return True

    @property
    def totals(self):
        return sum((r.totals for r in self), Totals())

    @property
    def last_battle_at(self):
        if not self._records:
            return None
        return max(r.started_at for r in self)

    def by_vehicle(self):
        groups = OrderedDict()
        for record in self:
            vehicle, totals = groups.get(record.vehicle.cd, (record.vehicle, Totals()))
            groups[record.vehicle.cd] = (vehicle, totals + record.totals)
        return groups

    def is_stale(self, now, max_idle):
        """Сессия считается закончившейся, если игрок долго не играл."""
        last = self.last_battle_at or self.started_at
        return now - last > max_idle

    def summary(self, metrics):
        totals = self.totals
        vehicles = []
        for vehicle, vehicle_totals in self.by_vehicle().values():
            item = vehicle._asdict()
            item['metrics'] = dict((m.key, m.value(vehicle_totals)) for m in metrics)
            vehicles.append(item)
        vehicles.sort(key=lambda v: v['metrics'].get('battles', 0), reverse=True)
        return {
            'startedAt': self.started_at,
            'metrics': [m.to_dict(totals) for m in metrics],
            'vehicles': vehicles,
            'battles': [r.to_dict() for r in reversed(list(self))],
        }

    def dump(self):
        return {'startedAt': self.started_at, 'battles': [r.to_dict() for r in self]}

    @classmethod
    def load(cls, data):
        session = cls(data['startedAt'])
        for item in data.get('battles', ()):
            session.add(BattleRecord.from_dict(item))
        return session
