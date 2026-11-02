/**
 * Paid report product line (v2.1 §3A) — mirrors backend/app/schemas/report.py.
 *
 * snake_case end-to-end: the backend speaks snake_case JSON, so these types are
 * declared against the response shape directly (AGENTS.md §3).
 */

/** Report product: r1 双人关系说明书 / r2 本命使用说明书 / r3 未来12个月时间地图. */
export type ReportProduct = 'r1' | 'r2' | 'r3';

/** Section type, ordered by the template roster (summary → chapters → boundary). */
export type ReportSectionKind = 'summary' | 'chapter' | 'action' | 'evidence' | 'boundary';

/** Compatible evidence categories: model ledger / traditional interpretation / practical observation. */
export type EvidenceConfidence = 'high' | 'medium' | 'low';

/** One evidence card: a claim + its chart fact + source + how it could be falsified. */
export interface ReportEvidenceCard {
  claim_id: string;
  claim: string;
  chart_fact: string;
  source: string;
  confidence: EvidenceConfidence;
  falsifier: string;
}

/** One report chapter: title + paragraphs + bullets + that chapter's evidence cards. */
export interface ReportSection {
  id: string;
  title: string;
  kind: ReportSectionKind;
  body: string[];
  bullets: string[];
  evidence_cards: ReportEvidenceCard[];
}

/** Free preview: one-page summary + a few key points (no payment/trial in v1). */
export interface ReportPreview {
  product: ReportProduct;
  title: string;
  tagline: string;
  version: string;
  generated_date: string;
  input_summary: string;
  summary: string[];
  key_points: string[];
  section_count: number;
  notice: string;
  can_generate: boolean;
}

/** Full report + internal credentials or a manually issued fixed snapshot identity. */
export interface ReportDocument {
  order_id: string;
  product: ReportProduct;
  title: string;
  tagline: string;
  version: string;
  generated_date: string;
  input_summary: string;
  sections: ReportSection[];
  boundary: string;
  token: string;
  expires_at: string;
}

/** Session-storage key holding the pending report input for a product. */
export function reportInputKey(product: ReportProduct): string {
  return `report_input_${product}`;
}
