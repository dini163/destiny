/**
 * 梅花结论卡片（verdict-card spec §6）：档位词、星级、四本账分项与建议逐字来自夹具 verdict。
 *
 * 输入只来自录制夹具（AGENTS §9：不手写假响应）；星级排按后端 stars 渲染。
 * 复测口径：`cd frontend && npx vitest run tests/components/meihua/MeihuaVerdict.test.tsx`。
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { MeihuaCast } from '../../../src/types/meihua';
import { readFixture } from '../../lib/readFixture';

const cast = readFixture('meihua') as MeihuaCast;

afterEach(cleanup);

describe('梅花结论卡片', () => {
  it('档位词、星级、四本账分项与建议按夹具 verdict 渲染', () => {
    const verdict = cast.verdict;
    if (!verdict) throw new Error('夹具缺 verdict');
    render(<VerdictCard verdict={verdict} />);
    const body = document.body.textContent ?? '';
    expect(body).toContain(verdict.grade);
    expect(body).toContain('★'.repeat(verdict.stars));
    for (const point of verdict.points) {
      expect(body).toContain(point);
    }
    expect(body).toContain(verdict.advice);
    // 四本账 label 都进了分项（体用生克/卦气旺衰/互卦(过程)/变卦(结局)）。
    expect(verdict.points).toHaveLength(cast.score_factors.length);
  });
});
