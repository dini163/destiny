/**
 * Shared API types mirroring `backend/app/schemas/common.py`.
 *
 * Field names stay snake_case to match the JSON contract exactly, so responses are
 * consumed without a mapping layer. Python `date`/`time` arrive as ISO strings.
 */

/** Calendar system of the supplied birth date. */
export type CalendarType = 'solar' | 'lunar';

/** Subject gender; required by systems whose luck pillars depend on it. */
export type Gender = 'male' | 'female';

/** Common birth-data input shared by the natal-chart systems. */
export interface BirthInput {
  /** Birth date, ISO `yyyy-mm-dd`. */
  birth_date: string;
  /** Birth time, `HH:MM` or `HH:MM:SS`. */
  birth_time: string;
  calendar?: CalendarType;
  city?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  gender?: Gender | null;
}

/** True Solar Time preview shown in the input console. */
export interface TrueSolarTimeResponse {
  standard_time: string;
  true_solar_time: string;
  offset_minutes: number;
  longitude: number;
}

/** A geocoded city returned by the location picker. */
export interface City {
  name: string;
  province: string;
  latitude: number;
  longitude: number;
}

/** Liveness probe response from `GET /health`. */
export interface HealthResponse {
  status: string;
  service: string;
}

/** 一份被引用的数据表，镜像 `schemas/common.py:ProvenanceTable`（系统无关）。 */
export interface ProvenanceTable {
  name: string;
  version: string;
  source: string;
}

/** 白话详解的一个小节，镜像 `backend/app/schemas/common.py:PlainSection`（系统无关）。
 *  `title` 取自各系统 content 的小节名册，不是引擎现编的词；`text` 是引擎拼好的整段——
 *  开篇句与逐条判语以 `\n` 分行，请求时一个字也不生成。 */
export interface PlainSection {
  title: string;
  text: string;
}
