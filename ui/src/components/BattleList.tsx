import { formatNumber, formatTime } from '../format';
import type { Battle, BattleResult } from '../types';

const RESULT_LABELS: Record<BattleResult, string> = {
  win: 'Победа',
  loss: 'Поражение',
  draw: 'Ничья',
};

export function BattleList({ battles }: { battles: Battle[] }) {
  if (!battles.length) return null;

  return (
    <section className="panel">
      <h2 className="panel__title">Бои</h2>
      <div className="table">
        <div className="table__row table__row--head">
          <span className="col col--time">Время</span>
          <span className="col col--name">Машина / карта</span>
          <span className="col col--result">Итог</span>
          <span className="col">Урон</span>
          <span className="col">Ассист</span>
          <span className="col">Фраги</span>
          <span className="col">Опыт</span>
        </div>
        {battles.map((battle) => (
          <div className="table__row" key={battle.arenaId}>
            <span className="col col--time">{formatTime(battle.startedAt)}</span>
            <span className="col col--name">
              {battle.vehicle.name}
              <span className="muted"> · {battle.map}</span>
            </span>
            <span className={`col col--result result--${battle.result}`}>{RESULT_LABELS[battle.result]}</span>
            <span className="col">{formatNumber(battle.damage)}</span>
            <span className="col">{formatNumber(battle.assist)}</span>
            <span className="col">{battle.kills}</span>
            <span className="col">{formatNumber(battle.xp)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
