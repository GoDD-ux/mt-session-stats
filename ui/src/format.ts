const NBSP = ' ';

export function formatNumber(value: number): string {
  return Math.round(value)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, NBSP);
}

// Привычная игрокам шкала цветов для процента побед
const WIN_RATE_COLORS: [number, string][] = [
  [47, 'var(--rating-bad)'],
  [49, 'var(--rating-below)'],
  [52, 'var(--rating-avg)'],
  [57, 'var(--rating-good)'],
  [64, 'var(--rating-great)'],
];

export function winRateColor(percent: number): string {
  for (const [limit, color] of WIN_RATE_COLORS) {
    if (percent < limit) return color;
  }
  return 'var(--rating-unicum)';
}

const KIND_LABELS: Record<string, string> = {
  lightTank: 'ЛТ',
  mediumTank: 'СТ',
  heavyTank: 'ТТ',
  'AT-SPG': 'ПТ',
  SPG: 'САУ',
};

export function kindLabel(kind: string): string {
  return KIND_LABELS[kind] ?? '';
}

const ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'];

export function tierLabel(tier: number): string {
  return ROMAN[tier] ?? String(tier);
}

export function formatDuration(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds / 60));
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  return hours ? `${hours} ч ${minutes} мин` : `${minutes} мин`;
}

export function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function battlesWord(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return 'бой';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'боя';
  return 'боёв';
}
