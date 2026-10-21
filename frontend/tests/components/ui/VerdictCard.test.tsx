/**
 * 结论卡片（verdict-card spec §6）：四要素逐字来自后端 `Verdict`，前端不增一字。
 *
 * 输入必须来自夹具（AGENTS §9：新前端测不手写假响应）——bazi-natal 夹具重录后自带
 * `interpretation.verdict`。星级以 ★/☆ 排渲染、颜色按星级派生，本测钉前者（后者是 class，
 * 随时可改的字符串，不参与判据）。
 *
 * 复测口径：
 *   cd frontend && npx vitest run tests/components/ui/VerdictCard.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { BaziChart } from '../../../src/types/bazi';
import { paragraphByExact } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const natal = readFixture('bazi-natal') as BaziChart;
const verdict = natal.interpretation?.verdict;

afterEach(cleanup);

describe('VerdictCard', () => {
  it('档位词与星级排按后端值渲染', () => {
    if (!verdict) throw new Error('夹具缺 interpretation.verdict');
    render(<VerdictCard verdict={verdict} />);
    const body = document.body.textContent ?? '';
    expect(body).toContain(verdict.grade);
    expect(body).toContain('★'.repeat(verdict.stars));
    expect(body).toContain('☆'.repeat(5 - verdict.stars));
  });

  it('headline、分项要点与建议逐字进 DOM，且 headline 在建议之前', () => {
    if (!verdict) throw new Error('夹具缺 interpretation.verdict');
    render(<VerdictCard verdict={verdict} />);
    const body = document.body.textContent ?? '';
    for (const point of verdict.points) {
      expect(body).toContain(point);
    }
    expect(body).toContain(verdict.advice);
    const headline = paragraphByExact(verdict.headline);
    const advice = paragraphByExact(verdict.advice);
    expect(headline.compareDocumentPosition(advice) & Node.DOCUMENT_POSITION_FOLLOWING).not.toBe(0);
  });
});
