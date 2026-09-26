import { describe, expect, it } from 'vitest';
import { battlesWord, formatDuration, formatNumber, kindLabel, tierLabel, winRateColor } from './format';

describe('formatNumber', () => {
  it('groups thousands', () => {
    expect(formatNumber(1234567)).toBe('1 234 567');
    expect(formatNumber(999)).toBe('999');
  });

  it('rounds', () => {
    expect(formatNumber(2345.6)).toBe('2 346');
  });
});

describe('winRateColor', () => {
  it('uses bounds as exclusive', () => {
    expect(winRateColor(46.9)).toBe('var(--rating-bad)');
    expect(winRateColor(47)).toBe('var(--rating-below)');
    expect(winRateColor(80)).toBe('var(--rating-unicum)');
  });
});

describe('labels', () => {
  it('vehicle kind', () => {
    expect(kindLabel('AT-SPG')).toBe('ПТ');
    expect(kindLabel('unknown')).toBe('');
  });

  it('tier', () => {
    expect(tierLabel(10)).toBe('X');
    expect(tierLabel(0)).toBe('');
  });
});

describe('formatDuration', () => {
  it('shows hours only when needed', () => {
    expect(formatDuration(59 * 60)).toBe('59 мин');
    expect(formatDuration(2 * 3600 + 5 * 60)).toBe('2 ч 5 мин');
    expect(formatDuration(-10)).toBe('0 мин');
  });
});

describe('battlesWord', () => {
  it.each([
    [1, 'бой'],
    [3, 'боя'],
    [5, 'боёв'],
    [11, 'боёв'],
    [12, 'боёв'],
    [21, 'бой'],
    [22, 'боя'],
  ])('%i -> %s', (count, word) => {
    expect(battlesWord(count)).toBe(word);
  });
});
