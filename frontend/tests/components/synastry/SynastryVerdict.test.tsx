/**
 * 合盘结论卡片（verdict-card spec §6）：档位词、星级、计入相位/核心羁绊分项与建议逐字来自
 * 夹具 verdict。输入只来自录制夹具（AGENTS §9：不手写假响应）。
 * 复测口径：`cd frontend && npx vitest run tests/components/synastry/SynastryVerdict.test.tsx`。
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { SynastryChart } from '../../../src/types/synastry';
import { readFixture } from '../../lib/readFixture';

const chart = readFixture('synastry') as SynastryChart;

afterEach(cleanup);

describe('合盘结论卡片', () => {
  it('档位词、星级、计入相位/核心羁绊分项与建议按夹具 verdict 渲染', () => {
    const verdict = chart.verdict;
    if (!verdict) throw new Error('夹具缺 verdict');
    render(<VerdictCard verdict={verdict} />);
    const body = document.body.textContent ?? '';
    expect(body).toContain(verdict.grade);
    expect(body).toContain('★'.repeat(verdict.stars));
    for (const point of verdict.points) {
      expect(body).toContain(point);
    }
    expect(body).toContain(verdict.advice);
  });
});
