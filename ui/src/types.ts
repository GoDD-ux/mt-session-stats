// Формат ответа /api/session, см. Session.summary() в mod/.../models.py

export type BattleResult = 'win' | 'loss' | 'draw';

export interface Metric {
  key: string;
  title: string;
  value: number;
  text: string;
}

export interface VehicleInfo {
  cd: number;
  name: string;
  tier: number;
  kind: string;
}

export interface VehicleRow extends VehicleInfo {
  metrics: Record<string, number>;
}

export interface Battle {
  arenaId: string;
  startedAt: number;
  result: BattleResult;
  map: string;
  vehicle: VehicleInfo;
  damage: number;
  assist: number;
  blocked: number;
  kills: number;
  spotted: number;
  shots: number;
  hits: number;
  piercings: number;
  xp: number;
  credits: number;
}

export interface SessionSummary {
  startedAt: number;
  metrics: Metric[];
  vehicles: VehicleRow[];
  battles: Battle[];
}
