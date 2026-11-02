import { describe, expect, it } from 'vitest';
import {
  isReportProduct,
  reportHighlights,
  reportAction,
} from '../../src/lib/reportReading';
import { readFixture } from './readFixture';
import type { ReportDocument } from '../../src/types/report';

describe('报告路由与真实摘要', () => {
  it('拒绝未知产品而不是把字符串强转成合法产品', () => {
    expect(isReportProduct('unknown')).toBe(false);
    expect(isReportProduct(undefined)).toBe(false);
    expect(isReportProduct('r2')).toBe(true);
  });
  it('重点和小行动仅来自实际报告章节', () => {
    const doc = readFixture('report-r2') as ReportDocument;
    expect(reportHighlights(doc)).toHaveLength(3);
    expect(
      reportHighlights(doc).every((line) =>
        doc.sections[0].bullets.includes(line),
      ),
    ).toBe(true);
    expect(
      reportHighlights(doc).some((line) => line.startsWith('压力模式：')),
    ).toBe(true);
    expect(reportAction(doc)).toBe(
      doc.sections.find((row) => row.id === 'experiments')!.bullets[0],
    );
  });
});
