import { useEffect, useMemo, useRef } from 'react';
import { useReport } from './useReport';
import { reportInputKey, type ReportProduct } from '../types/report';

export function useReportReading(
  product: ReportProduct,
  sample: boolean,
  fragment: string,
  startDate?: string,
  stage?: string,
) {
  const report = useReport();
  const attempted = useRef(false);
  const delivery = useMemo(() => {
    const params = new URLSearchParams(fragment.replace(/^#/, ''));
    const id = params.get('delivery');
    const token = params.get('token');
    return id && token ? { id, token } : null;
  }, [fragment]);
  const input = useMemo(() => {
    if (delivery) return undefined;
    try {
      const raw = sessionStorage.getItem(reportInputKey(product));
      const value: unknown = raw ? JSON.parse(raw) : undefined;
      if (product === 'r1' && stage && value && typeof value === 'object')
        return { ...value, relationship_stage: stage };
      if (product === 'r3' && startDate && value && typeof value === 'object')
        return { ...value, start_date: startDate };
      return value;
    } catch {
      return undefined;
    }
  }, [product, delivery, startDate, stage]);
  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;
    if (delivery) report.fetchDelivery(product, delivery.id, delivery.token);
    else if (sample) report.fetchSample(product);
    else if (input) report.requestPreview(product, input);
  }, [delivery, sample, product, input, report]);
  return { ...report, input, delivered: delivery !== null, sample };
}
