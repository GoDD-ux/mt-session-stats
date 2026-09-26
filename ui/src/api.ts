import { useCallback, useEffect, useRef, useState } from 'react';
import { makeMockSession } from './mock';
import type { SessionSummary } from './types';

const POLL_INTERVAL = 3000;
const isMock = new URLSearchParams(window.location.search).has('mock');

async function fetchSession(): Promise<SessionSummary> {
  const response = await fetch('api/session', { cache: 'no-store' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export async function resetSession(): Promise<void> {
  if (isMock) return;
  await fetch('api/reset', { method: 'POST' });
}

interface SessionState {
  data: SessionSummary | null;
  offline: boolean;
  refresh: () => void;
}

export function useSession(): SessionState {
  const [data, setData] = useState<SessionSummary | null>(() => (isMock ? makeMockSession() : null));
  const [offline, setOffline] = useState(false);
  const timer = useRef<number | undefined>(undefined);

  const load = useCallback(async () => {
    if (isMock) return;
    try {
      setData(await fetchSession());
      setOffline(false);
    } catch {
      // игра закрыта или мод перезапускается - показываем последние данные
      setOffline(true);
    }
  }, []);

  useEffect(() => {
    load();
    timer.current = window.setInterval(load, POLL_INTERVAL);
    return () => window.clearInterval(timer.current);
  }, [load]);

  return { data, offline, refresh: load };
}
