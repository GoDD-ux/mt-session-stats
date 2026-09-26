import { winRateColor } from '../format';
import type { Metric } from '../types';

// Крупно показываем то, на что игрок смотрит в первую очередь
const MAIN_KEYS = ['battles', 'winRate', 'avgDamage', 'avgAssist'];

export function MetricCards({ metrics }: { metrics: Metric[] }) {
  const main = metrics.filter((m) => MAIN_KEYS.includes(m.key));
  const rest = metrics.filter((m) => !MAIN_KEYS.includes(m.key));

  return (
    <>
      <div className="cards">
        {main.map((metric) => (
          <div className="card" key={metric.key}>
            <div
              className="card__value"
              style={metric.key === 'winRate' && metric.value ? { color: winRateColor(metric.value) } : undefined}
            >
              {metric.text}
            </div>
            <div className="card__title">{metric.title}</div>
          </div>
        ))}
      </div>
      <div className="details">
        {rest.map((metric) => (
          <div className="details__item" key={metric.key}>
            <span className="details__title">{metric.title}</span>
            <span className="details__value">{metric.text}</span>
          </div>
        ))}
      </div>
    </>
  );
}
