import { useState } from 'react';
import { resetSession, useSession } from './api';
import { BattleList } from './components/BattleList';
import { DamageChart } from './components/DamageChart';
import { MetricCards } from './components/MetricCards';
import { VehicleTable } from './components/VehicleTable';
import { battlesWord, formatDuration, formatTime } from './format';

export function App() {
  const { data, offline, refresh } = useSession();
  const [confirming, setConfirming] = useState(false);

  if (!data) {
    return <div className="placeholder">{offline ? 'Нет связи с игрой' : 'Загрузка…'}</div>;
  }

  const count = data.battles.length;
  const onReset = async () => {
    setConfirming(false);
    await resetSession();
    refresh();
  };

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1 className="header__title">Итоги сессии</h1>
          <div className="header__subtitle">
            с {formatTime(data.startedAt)} · {formatDuration(Date.now() / 1000 - data.startedAt)} · {count}{' '}
            {battlesWord(count)}
            {offline && <span className="badge">нет связи с игрой</span>}
          </div>
        </div>
        {confirming ? (
          <div className="header__actions">
            <span className="muted">Начать новую сессию?</span>
            <button className="button button--danger" onClick={onReset}>
              Да
            </button>
            <button className="button" onClick={() => setConfirming(false)}>
              Нет
            </button>
          </div>
        ) : (
          <button className="button" onClick={() => setConfirming(true)} disabled={!count}>
            Сбросить
          </button>
        )}
      </header>

      {count ? (
        <>
          <MetricCards metrics={data.metrics} />
          <DamageChart battles={data.battles} />
          <VehicleTable vehicles={data.vehicles} />
          <BattleList battles={data.battles} />
        </>
      ) : (
        <div className="placeholder">Сыграйте бой - статистика появится здесь</div>
      )}
    </div>
  );
}
