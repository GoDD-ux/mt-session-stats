# -*- coding: utf-8 -*-
from __future__ import division


def _group_thousands(value):
    return u'{:,}'.format(int(round(value))).replace(u',', u' ')


class Metric(object):
    """Показатель, который считается из Totals. Чтобы добавить новый - достаточно
    дописать его в METRICS, интерфейс подхватит сам."""

    def __init__(self, key, title):
        self.key = key
        self.title = title

    def value(self, totals):
        raise NotImplementedError

    def format(self, value):
        return _group_thousands(value)

    def to_dict(self, totals):
        value = self.value(totals)
        return {'key': self.key, 'title': self.title, 'value': value, 'text': self.format(value)}

    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.key)


class Total(Metric):

    def __init__(self, key, title, field=None):
        super(Total, self).__init__(key, title)
        self.field = field or key

    def value(self, totals):
        return getattr(totals, self.field)


class Average(Total):

    def value(self, totals):
        if not totals.battles:
            return 0
        return getattr(totals, self.field) / totals.battles


class PreciseAverage(Average):

    def format(self, value):
        return u'{:.2f}'.format(value)


class Ratio(Metric):

    def __init__(self, key, title, numerator, denominator):
        super(Ratio, self).__init__(key, title)
        self.numerator = numerator
        self.denominator = denominator

    def value(self, totals):
        denominator = getattr(totals, self.denominator)
        if not denominator:
            return 0
        return getattr(totals, self.numerator) / denominator * 100

    def format(self, value):
        return u'{:.1f}%'.format(value)


METRICS = (
    Total('battles', u'Боёв'),
    Ratio('winRate', u'Побед', 'wins', 'battles'),
    Average('avgDamage', u'Средний урон', 'damage'),
    Average('avgAssist', u'Средний ассист', 'assist'),
    Average('avgBlocked', u'Заблокировано бронёй', 'blocked'),
    PreciseAverage('avgKills', u'Уничтожено за бой', 'kills'),
    PreciseAverage('avgSpotted', u'Обнаружено за бой', 'spotted'),
    Ratio('hitRate', u'Попаданий', 'hits', 'shots'),
    Ratio('pierceRate', u'Пробитий', 'piercings', 'hits'),
    Total('xp', u'Опыт'),
    Total('credits', u'Кредиты'),
)
