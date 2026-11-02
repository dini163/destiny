import type { ReportDocument, ReportProduct } from '../types/report';
import { ROUTES } from '../nav';

export function isReportProduct(
  value: string | undefined,
): value is ReportProduct {
  return value === 'r1' || value === 'r2' || value === 'r3';
}

export const REPORT_ENTRIES = {
  r1: { path: ROUTES.baziHehun, label: '八字合婚' },
  r2: { path: ROUTES.baziNatal, label: '八字命理' },
  r3: { path: ROUTES.baziTransit, label: '八字岁运' },
};

export function reportHighlights(doc: ReportDocument): string[] {
  const summary = doc.sections.find((section) => section.kind === 'summary');
  const bullets = summary?.bullets ?? [];
  if (doc.product === 'r2') {
    const chosen = bullets.filter((line) =>
      /^(先看重点|压力模式|最值得练习的一件事)：/.test(line),
    );
    if (chosen.length >= 3) return chosen.slice(0, 3);
  }
  return bullets.slice(0, 3);
}

export function reportAction(doc: ReportDocument): string | undefined {
  const section =
    doc.sections.find(
      (item) => item.id === 'experiments' || item.kind === 'action',
    ) ?? doc.sections.find((item) => item.id === 'scripts');
  return section?.bullets[0] ?? section?.body[0];
}

export function deliveryLink(doc: ReportDocument): string {
  const fragment = new URLSearchParams({
    delivery: doc.order_id,
    token: doc.token,
  });
  return `${location.origin}/report/${doc.product}#${fragment}`;
}
