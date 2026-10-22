/**
 * 八字合婚结论卡片（verdict-card spec §6）：档位词、星级、加/抵合计分项与建议逐字来自夹具
 * verdict，headline 是现成档位句。输入只来自录制夹具（AGENTS §9：不手写假响应）。
 * 复测口径：`cd frontend && npx vitest run tests/components/hehun/HehunVerdict.test.tsx`。
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { BaziHehunResult } from '../../../src/types/baziHehun';
import { readFixture } from '../../lib/readFixture';

const result = readFixture('bazi-hehun') as BaziHehunResult;

afterEach(cleanup);

describe('合婚结论卡片', () => {
  it('档位词、星级、加/抵分项与建议按夹具 verdict 渲染', () => {
    const verdict = result.verdict;
    if (!verdict) throw new Error('夹具缺 verdict');
    render(<VerdictCard verdict={verdict} />);
    const body = document.body.textContent ?? '';
    expect(body).toContain(verdict.grade);
    expect(body).toContain('★'.repeat(verdict.stars));
    for (const point of verdict.points) {
      expect(body).toContain(point);
    }
    expect(body).toContain(verdict.advice);
    // headline 是现成档位句，逐字进 DOM。
    expect(body).toContain(verdict.headline);
  });
});
