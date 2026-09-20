import type { City, HealthResponse, TrueSolarTimeResponse } from '../types/common';
import { apiGet } from './client';

/**
 * Query parameters for the True Solar Time preview.
 *
 * A type alias (not an interface) so it carries an implicit index signature and is
 * assignable to the client's `QueryParams` record.
 */
export type TrueSolarTimeParams = {
  /** ISO date, e.g. `1988-02-15`. */
  date: string;
  /** `HH:MM` local standard time, e.g. `23:30`. */
  time: string;
  /** Longitude in degrees east. */
  longitude: number;
};

/** Search geocoded cities for the location picker. */
export function searchCities(q: string, signal?: AbortSignal): Promise<City[]> {
  return apiGet<City[]>('/meta/cities', { q }, signal);
}

/** Preview the True Solar Time correction for a standard-time moment. */
export function getTrueSolarTime(
  params: TrueSolarTimeParams,
  signal?: AbortSignal,
): Promise<TrueSolarTimeResponse> {
  return apiGet<TrueSolarTimeResponse>('/meta/true-solar-time', params, signal);
}

/** Liveness probe for the computation backend. */
export function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiGet<HealthResponse>('/health', undefined, signal);
}
