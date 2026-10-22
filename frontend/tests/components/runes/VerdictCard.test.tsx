/**
 * 卢恩综合结论卡片（verdict）：真实夹具渲染 + 页面挂点源码扫。
 *
 * 渲染凭据管 DOM：档位词、星级排、结论句、要点、建议逐字来自后端 `Verdict`；卡片无分数、
 * 无百分比（决策 7 仍然有效）。源码扫凭据管挂点：碑阵网格之后、`RuneSynthesis` 直读之前
 * 挂 `<VerdictCard>`（结论先行，与 ZhouyiPage 的 Summary → VerdictCard → plain 同形）。
 * 夹具由 `scripts/record_frontend_fixtures.py` 打真实后端重录（AGENTS §9，不手写假响应）。
 *
 * 复测：cd frontend && npx vitest run tests/components/runes/VerdictCard.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { RuneCastResponse } from '../../../src/types/runes';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';

const PAGE = '../../../src/pages/NorseRunesPage.tsx';

const cast = readFixture('runes') as RuneCastResponse;

afterEach(cleanup);

describe('卢恩综合结论卡片', () => {
  it('档位词、星级排、结论句、要点与建议逐字进 DOM', () => {
    const { verdict } = cast;
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

  it('页面把结论卡片挂在碑阵网格之后、RuneSynthesis 直读之前', () => {
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    pinLiteralOrder(page, [
      '<RuneStoneGrid',
      '<VerdictCard verdict={cast.verdict} />',
      '<RuneSynthesis',
    ]);
  });
});
