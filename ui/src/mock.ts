import type { Battle, BattleResult, SessionSummary, VehicleInfo } from './types';

// Данные для разработки без запущенной игры: открыть страницу с ?mock

const VEHICLES: VehicleInfo[] = [
  { cd: 7937, name: 'ИС-7', tier: 10, kind: 'heavyTank' },
  { cd: 12305, name: 'Об. 140', tier: 10, kind: 'mediumTank' },
  { cd: 6225, name: 'Grille 15', tier: 10, kind: 'AT-SPG' },
];
const MAPS = ['Прохоровка', 'Химмельсдорф', 'Малиновка', 'Рудники', 'Энск', 'Утёс', 'Степи'];

function randomInt(min: number, max: number) {
  return Math.floor(min + Math.random() * (max - min));
}

function makeBattle(index: number, startedAt: number): Battle {
  const vehicle = VEHICLES[index % VEHICLES.length];
  const roll = Math.random();
  const result: BattleResult = roll < 0.55 ? 'win' : roll < 0.97 ? 'loss' : 'draw';
  const shots = randomInt(6, 20);
  const hits = randomInt(Math.floor(shots / 2), shots);
  return {
    arenaId: String(1_000_000 + index),
    startedAt: startedAt + index * 480,
    result,
    map: MAPS[randomInt(0, MAPS.length)],
    vehicle,
    damage: randomInt(800, 6500),
    assist: randomInt(0, 2500),
    blocked: randomInt(0, 3000),
    kills: randomInt(0, 4),
    spotted: randomInt(0, 5),
    shots,
    hits,
    piercings: randomInt(Math.floor(hits / 2), hits),
    xp: randomInt(300, 2200),
    credits: randomInt(15000, 90000),
  };
}

export function makeMockSession(count = 14): SessionSummary {
  const startedAt = Math.floor(Date.now() / 1000) - count * 480 - 600;
  const battles = Array.from({ length: count }, (_, i) => makeBattle(i, startedAt));
  const sum = (list: Battle[], key: keyof Battle) => list.reduce((acc, b) => acc + (b[key] as number), 0);
  const avg = (list: Battle[], key: keyof Battle) => (list.length ? sum(list, key) / list.length : 0);
  const winRate = (list: Battle[]) => (list.filter((b) => b.result === 'win').length / list.length) * 100;

  const metric = (key: string, title: string, value: number, text: string) => ({ key, title, value, text });
  const n = (v: number) => Math.round(v).toLocaleString('ru-RU');

  return {
    startedAt,
    metrics: [
      metric('battles', 'Боёв', count, String(count)),
      metric('winRate', 'Побед', winRate(battles), `${winRate(battles).toFixed(1)}%`),
      metric('avgDamage', 'Средний урон', avg(battles, 'damage'), n(avg(battles, 'damage'))),
      metric('avgAssist', 'Средний ассист', avg(battles, 'assist'), n(avg(battles, 'assist'))),
      metric('avgBlocked', 'Заблокировано бронёй', avg(battles, 'blocked'), n(avg(battles, 'blocked'))),
      metric('avgKills', 'Уничтожено за бой', avg(battles, 'kills'), avg(battles, 'kills').toFixed(2)),
      metric('avgSpotted', 'Обнаружено за бой', avg(battles, 'spotted'), avg(battles, 'spotted').toFixed(2)),
      metric('hitRate', 'Попаданий', 0, `${((sum(battles, 'hits') / sum(battles, 'shots')) * 100).toFixed(1)}%`),
      metric('pierceRate', 'Пробитий', 0, `${((sum(battles, 'piercings') / sum(battles, 'hits')) * 100).toFixed(1)}%`),
      metric('xp', 'Опыт', sum(battles, 'xp'), n(sum(battles, 'xp'))),
      metric('credits', 'Кредиты', sum(battles, 'credits'), n(sum(battles, 'credits'))),
    ],
    vehicles: VEHICLES.map((vehicle) => {
      const own = battles.filter((b) => b.vehicle.cd === vehicle.cd);
      return {
        ...vehicle,
        metrics: { battles: own.length, winRate: winRate(own), avgDamage: avg(own, 'damage'), avgAssist: avg(own, 'assist') },
      };
    }),
    battles: battles.reverse(),
  };
}
