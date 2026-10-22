/**
 * 吠陀综合结论卡片（verdict）：真实夹具渲染 + 页面挂点源码扫。
 *
 * 渲染凭据管 DOM：档位词、星级排、结论句、三条要点、建议逐字来自后端 `Verdict`；
 * 源码扫凭据管挂点：`SummaryStrip` 之后、`DashaTimeline` 之前挂 `<VerdictCard>`
 * （结论先行，与 ZiweiPage 的 Summary → VerdictCard → plain 同形）。夹具由
 * `scripts/record_frontend_fixtures.py` 打真实后端重录（AGENTS §9，不手写假响应）。
 *
 * 复测：cd frontend && npx vitest run tests/components/vedic/VerdictCard.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { VedicChart } from '../../../src/types/vedic';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';

const PAGE = '../../../src/pages/VedicPage.tsx';

const chart = readFixture('vedic') as VedicChart;

afterEach(cleanup);

describe('吠陀综合结论卡片', () => {
  it('档位词、星级排、结论句、要点与建议逐字进 DOM', () => {
    const { verdict } = chart;
    render(<VerdictCard verdict={verdict} />);
    const body = document.body.textContent ?? '';
    expect(body).toContain(verdict.grade);
    expect(body).toContain('★'.repeat(verdict.stars));
    expect(body).toContain('☆'.repeat(5 - verdict.stars));
    expect(body).toContain(verdict.headline);
    for (const point of verdict.points) {
      expect(body).toContain(point);
    }
    expect(body).toContain(verdict.advice);
  });

  it('页面把结论卡片挂在 SummaryStrip 之后、DashaTimeline 之前', () => {
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    pinLiteralOrder(page, [
      '<SummaryStrip chart={chart} />',
      '<VerdictCard verdict={chart.verdict} />',
      '<DashaTimeline vimshottari={chart.vimshottari} />',
    ]);
  });
});
