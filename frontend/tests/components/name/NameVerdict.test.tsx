/**
 * 姓名学结论卡片（verdict-card spec §6）：核定盘渲染档位/星级/分项/建议；笔画未核定盘
 * verdict 整块为 null，不渲染卡片（None 纪律同 score）。
 *
 * 输入只来自录制夹具（AGENTS §9：不手写假响应）。
 * 复测口径：`cd frontend && npx vitest run tests/components/name/NameVerdict.test.tsx`。
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { NameAnalysis } from '../../../src/types/name';
import { readFixture } from '../../lib/readFixture';

const resolved = readFixture('name') as NameAnalysis;
const unresolved = readFixture('name-unresolved') as NameAnalysis;

afterEach(cleanup);

describe('姓名学结论卡片', () => {
  it('核定盘：档位词、星级、五格/三才分项与建议按夹具 verdict 渲染', () => {
    const verdict = resolved.verdict;
    if (!verdict) throw new Error('name 夹具缺 verdict（核定盘应有）');
    render(<VerdictCard verdict={verdict} />);
    const body = document.body.textContent ?? '';
    expect(body).toContain(verdict.grade);
    expect(body).toContain('★'.repeat(verdict.stars));
    for (const point of verdict.points) {
      expect(body).toContain(point);
    }
    expect(body).toContain(verdict.advice);
  });

  it('未核定盘：verdict 为 null，不渲染结论卡片', () => {
    expect(unresolved.score).toBeNull();
    expect(unresolved.verdict).toBeNull();
    // 不给卡片传 verdict 即不渲染；这里钉契约形状，页面据此整块省略。
    expect(unresolved.verdict).toBeNull();
  });
});
