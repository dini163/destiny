/**
 * 塔罗综合结论卡片（verdict）：真实夹具渲染 + 页面挂点源码扫。
 *
 * 渲染凭据管 DOM：档位词、星级排、结论句、要点、建议逐字来自后端 `Verdict`；
 * 源码扫凭据管挂点：`SpreadSummary` 之后、「综合解读」原卡之前挂 `<VerdictCard>`
 * （结论先行，与 ZhouyiPage 的 Summary → VerdictCard → plain 同形）。夹具由
 * `scripts/record_frontend_fixtures.py` 打真实后端重录（AGENTS §9，不手写假响应）。
 *
 * 复测：cd frontend && npx vitest run tests/components/tarot/VerdictCard.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { TarotSpreadResponse } from '../../../src/types/tarot';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';

const PAGE = '../../../src/pages/TarotPage.tsx';

const spread = readFixture('tarot') as TarotSpreadResponse;

afterEach(cleanup);

describe('塔罗综合结论卡片', () => {
  it('档位词、星级排、结论句、要点与建议逐字进 DOM', () => {
    const { verdict } = spread;
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

  it('页面把结论卡片挂在 SpreadSummary 之后、综合解读原卡之前', () => {
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    pinLiteralOrder(page, [
      '<SpreadSummary spread={spread} />',
      '<VerdictCard verdict={spread.verdict} />',
      'title="综合解读"',
    ]);
  });
});
