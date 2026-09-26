import { formatNumber } from '../format';
import type { Battle } from '../types';

const MAX_BARS = 30;

export function DamageChart({ battles }: { battles: Battle[] }) {
  // с сервера бои приходят от новых к старым, на графике время идёт слева направо
  const items = battles.slice(0, MAX_BARS).reverse();
  if (!items.length) return null;

  const max = Math.max(...items.map((b) => b.damage + b.assist), 1);
  const average = items.reduce((sum, b) => sum + b.damage, 0) / items.length;

  return (
    <section className="panel">
      <h2 className="panel__title">
        Урон и ассист по боям
        <span className="legend">
          <i className="legend__dot legend__dot--win" /> победа
          <i className="legend__dot legend__dot--loss" /> поражение
          <i className="legend__dot legend__dot--assist" /> ассист
        </span>
      </h2>
      <div className="chart">
        <div className="chart__average" style={{ bottom: `${(average / max) * 100}%` }}>
          <span>ср. {formatNumber(average)}</span>
        </div>
        {items.map((battle) => (
          <div
            className="chart__column"
            key={battle.arenaId}
            title={`${battle.vehicle.name}, ${battle.map}: ${formatNumber(battle.damage)} урона, ${formatNumber(battle.assist)} ассиста`}
          >
            <div className="chart__bar chart__bar--assist" style={{ height: `${(battle.assist / max) * 100}%` }} />
            <div
              className={`chart__bar chart__bar--${battle.result}`}
              style={{ height: `${(battle.damage / max) * 100}%` }}
            />
          </div>
        ))}
      </div>
    </section>
  );
}
