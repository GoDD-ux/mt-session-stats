# -*- coding: utf-8 -*-
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mod', 'scripts', 'client', 'gui'))

from session_stats.metrics import METRICS, Average, PreciseAverage, Ratio, Total  # noqa: E402
from session_stats.models import (BattleRecord, DRAW, LOSS, Session, Totals, Vehicle,  # noqa: E402
                                  WIN)
from session_stats.parser import arena_start_time, parse_results  # noqa: E402

IS_7 = Vehicle(1, u'ИС-7', 10, 'heavyTank')
STB = Vehicle(2, u'STB-1', 10, 'mediumTank')


def record(arena_id, result=WIN, vehicle=IS_7, **counters):
    return BattleRecord(arena_id, 1700000000 + arena_id, result, vehicle, u'Прохоровка', **counters)


class TotalsTest(unittest.TestCase):

    def test_add(self):
        total = Totals(battles=1, damage=100) + Totals(battles=2, damage=50)
        self.assertEqual(total, Totals(battles=3, damage=150))

    def test_sum_starts_from_zero(self):
        items = [Totals(battles=1, kills=2), Totals(battles=1, kills=1)]
        self.assertEqual(sum(items).kills, 3)

    def test_unknown_field(self):
        self.assertRaises(TypeError, Totals, dmg=1)

    def test_not_equal(self):
        self.assertTrue(Totals(battles=1) != Totals(battles=2))
        self.assertFalse(Totals() == object())


class SessionTest(unittest.TestCase):

    def test_duplicates_are_ignored(self):
        session = Session()
        session += record(1)
        session += record(1)
        self.assertEqual(len(session), 1)
        self.assertIn(1, session)

    def test_totals(self):
        session = Session()
        session += record(1, WIN, damage=3000)
        session += record(2, LOSS, damage=1000)
        session += record(3, DRAW, damage=2000)
        totals = session.totals
        self.assertEqual((totals.battles, totals.wins, totals.losses, totals.draws), (3, 1, 1, 1))
        self.assertEqual(totals.damage, 6000)

    def test_by_vehicle(self):
        session = Session()
        session += record(1, vehicle=IS_7, damage=100)
        session += record(2, vehicle=STB, damage=200)
        session += record(3, vehicle=IS_7, damage=300)
        groups = session.by_vehicle()
        self.assertEqual(groups[IS_7.cd][1].battles, 2)
        self.assertEqual(groups[IS_7.cd][1].damage, 400)
        self.assertEqual(groups[STB.cd][1].damage, 200)

    def test_is_stale(self):
        session = Session(started_at=1000)
        self.assertFalse(session.is_stale(now=1500, max_idle=600))
        self.assertTrue(session.is_stale(now=2000, max_idle=600))
        session += BattleRecord(5, 1900, WIN, IS_7)
        self.assertFalse(session.is_stale(now=2000, max_idle=600))

    def test_dump_and_load(self):
        session = Session(started_at=42)
        session += record(1, damage=10, xp=500)
        session += record(2, LOSS, vehicle=STB)
        # проверяем, что переживает сохранение в json
        restored = Session.load(json.loads(json.dumps(session.dump())))
        self.assertEqual(restored.started_at, 42)
        self.assertEqual(len(restored), 2)
        self.assertEqual(restored.totals, session.totals)
        self.assertEqual([r.vehicle for r in restored], [IS_7, STB])

    def test_summary_newest_battle_first(self):
        session = Session()
        session += record(1)
        session += record(2, vehicle=STB)
        session += record(3, vehicle=STB)
        summary = session.summary(METRICS)
        self.assertEqual([b['arenaId'] for b in summary['battles']], ['3', '2', '1'])
        self.assertEqual(summary['vehicles'][0]['name'], u'STB-1')
        json.dumps(summary)


class MetricsTest(unittest.TestCase):
    totals = Totals(battles=4, wins=3, damage=10000, kills=5, shots=20, hits=15, piercings=12)

    def test_values(self):
        self.assertEqual(Total('battles', u'').value(self.totals), 4)
        self.assertEqual(Average('avg', u'', 'damage').value(self.totals), 2500)
        self.assertEqual(Ratio('wr', u'', 'wins', 'battles').value(self.totals), 75)
        self.assertEqual(Ratio('pr', u'', 'piercings', 'hits').value(self.totals), 80)

    def test_empty_session(self):
        empty = Totals()
        for metric in METRICS:
            self.assertEqual(metric.value(empty), 0, metric)

    def test_format(self):
        self.assertEqual(Average('a', u'', 'damage').format(2345.6), u'2 346')
        self.assertEqual(PreciseAverage('a', u'', 'kills').format(1.255), u'1.25')
        self.assertEqual(Ratio('r', u'', 'wins', 'battles').format(52.345), u'52.3%')

    def test_keys_are_unique(self):
        keys = [m.key for m in METRICS]
        self.assertEqual(len(keys), len(set(keys)))


def full_results(winner_team=1, team=1, **vehicle):
    data = {'team': team, 'damageDealt': 2500, 'damageAssistedRadio': 300,
            'damageAssistedTrack': 200, 'kills': 2, 'xp': 900, 'credits': 45000}
    data.update(vehicle)
    arena_id = (123 << 32) | 1700000000
    return {
        'arenaUniqueID': arena_id,
        'common': {'winnerTeam': winner_team, 'arenaTypeID': 5, 'arenaCreateTime': 1700000000},
        'personal': {'avatar': {'team': team}, 7937: data},
    }


class ParserTest(unittest.TestCase):

    def test_parse(self):
        rec = parse_results(full_results(), describe_vehicle=lambda cd: IS_7,
                            describe_map=lambda arena_type: u'Химмельсдорф')
        self.assertEqual(rec.result, WIN)
        self.assertEqual(rec.counters['damage'], 2500)
        self.assertEqual(rec.counters['assist'], 500)
        self.assertEqual(rec.counters['kills'], 2)
        self.assertEqual(rec.vehicle, IS_7)
        self.assertEqual(rec.map_name, u'Химмельсдорф')
        self.assertEqual(rec.started_at, 1700000000)

    def test_loss_and_draw(self):
        self.assertEqual(parse_results(full_results(winner_team=2)).result, LOSS)
        self.assertEqual(parse_results(full_results(winner_team=0)).result, DRAW)

    def test_unknown_vehicle_keeps_cd(self):
        rec = parse_results(full_results())
        self.assertEqual(rec.vehicle.cd, 7937)

    def test_none_values(self):
        rec = parse_results(full_results(damageDealt=None))
        self.assertEqual(rec.counters['damage'], 0)

    def test_without_own_vehicle(self):
        self.assertIsNone(parse_results({'common': {}, 'personal': {'avatar': {}}}))

    def test_arena_start_time(self):
        self.assertEqual(arena_start_time((77 << 32) | 1234), 1234)


if __name__ == '__main__':
    unittest.main()
