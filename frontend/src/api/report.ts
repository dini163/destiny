/**
 * Report product-line API (v2.1 §3A): preview, generate, signed fetch.
 *
 * Request bodies are the existing per-system inputs (r1=BaziHehunRequest,
 * r2=BaziNatalRequest, r3=BaziTransitRequest) — the report layer reuses the same
 * payloads the free charts already accept, so the entry buttons can hand over the
 * page's current form state verbatim.
 */

import { apiGet, apiPost } from './client';
import type { ReportDocument, ReportPreview, ReportProduct } from '../types/report';

/** Fetch the free preview for a product (one-page summary + key points). */
export function fetchReportPreview<TBody>(
  product: ReportProduct,
  body: TBody,
  signal?: AbortSignal,
): Promise<ReportPreview> {
  return apiPost<ReportPreview>(`/report/${product}/preview`, body, signal);
}

/** Generate the full report plus a signed delivery link (v1 manual fulfillment). */
export function fetchReportDocument<TBody>(
  product: ReportProduct,
  body: TBody,
  signal?: AbortSignal,
): Promise<ReportDocument> {
  return apiPost<ReportDocument>(`/report/${product}/generate`, body, signal);
}

/** Re-fetch a report by its signed link: order id + token + the matching input. */
export function fetchReportByLink<TBody>(
  product: ReportProduct,
  orderId: string,
  token: string,
  body: TBody,
  signal?: AbortSignal,
): Promise<ReportDocument> {
  return apiPost<ReportDocument>(
    `/report/${product}/${orderId}?token=${encodeURIComponent(token)}`,
    body,
    signal,
  );
}

export function fetchReportDelivery(product: ReportProduct, id: string, token: string): Promise<ReportDocument> {
  return apiPost<ReportDocument>(`/report/${product}/delivery/${encodeURIComponent(id)}`, { token });
}
export function fetchReportSample(product: ReportProduct): Promise<ReportDocument> {
  return apiGet<ReportDocument>(`/report/${product}/sample`);
}
