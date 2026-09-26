import { formatNumber, kindLabel, tierLabel, winRateColor } from '../format';
import type { VehicleRow } from '../types';

export function VehicleTable({ vehicles }: { vehicles: VehicleRow[] }) {
  if (!vehicles.length) return null;

  return (
    <section className="panel">
      <h2 className="panel__title">Техника</h2>
      <div className="table">
        <div className="table__row table__row--head">
          <span className="col col--name">Машина</span>
          <span className="col">Бои</span>
          <span className="col">Победы</span>
          <span className="col">Урон</span>
          <span className="col">Ассист</span>
        </div>
        {vehicles.map((vehicle) => {
          const m = vehicle.metrics;
          return (
            <div className="table__row" key={vehicle.cd}>
              <span className="col col--name">
                <span className="tier">{tierLabel(vehicle.tier)}</span>
                <span className="kind">{kindLabel(vehicle.kind)}</span>
                {vehicle.name}
              </span>
              <span className="col">{m.battles}</span>
              <span className="col" style={{ color: winRateColor(m.winRate) }}>
                {m.winRate.toFixed(1)}%
              </span>
              <span className="col">{formatNumber(m.avgDamage)}</span>
              <span className="col">{formatNumber(m.avgAssist)}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
