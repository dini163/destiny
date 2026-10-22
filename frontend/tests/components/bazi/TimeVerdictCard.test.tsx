/**
 * 岁运 / 流日 / 流时三页结论卡（verdict-card spec §6）：档位词、星级排、headline、分项要点、
 * 建议逐字来自后端 `verdict`，前端不增一字。
 *
 * 输入必须来自 `scripts/record_frontend_fixtures.py` 录制的真实夹具（AGENTS §9：新前端测不
 * 手写假响应）。星级以 ★/☆ 排渲染，本测钉星级个数与档位词；具体档位随录制快照浮动，故不
 * 写死档位字面量，只钉「五档词之一、stars 1–5、五星排与 stars 一致」。
 *
 * 复测口径：
 *   cd frontend && npx vitest run tests/components/bazi/TimeVerdictCard.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import type { BaziLiushiResult } from '../../../src/types/baziLiushi';
import type { BaziLiuriResult } from '../../../src/types/baziLiuri';
import type { BaziTransitResult } from '../../../src/types/baziTransit';
import type { Verdict } from '../../../src/types/common';
import { readFixture } from '../../lib/readFixture';

const GRADES = ['大吉', '吉', '平', '小凶', '凶'] as const;

const transit = readFixture('bazi-liuyue') as BaziTransitResult;
const liuri = readFixture('bazi-liuri-matrix') as BaziLiuriResult;
const liushi = readFixture('bazi-liushi-day') as BaziLiushiResult;

function expectCardRenders(verdict: Verdict, label: string) {
  render(<VerdictCard verdict={verdict} />);
  const body = document.body.textContent ?? '';
  expect(GRADES).toContain(verdict.grade);
  expect(verdict.stars).toBeGreaterThanOrEqual(1);
  expect(verdict.stars).toBeLessThanOrEqual(5);
  expect(body).toContain(verdict.grade);
  expect(body).toContain('★'.repeat(verdict.stars));
  expect(body).toContain('☆'.repeat(5 - verdict.stars));
  expect(body).toContain(verdict.headline);
  for (const point of verdict.points) {
    expect(body).toContain(point);
  }
  expect(body).toContain(verdict.advice);
  // 每个用例独立断言一次，失败信息带上页名
  expect(label).toBeTruthy();
}

afterEach(cleanup);

describe('岁运 / 流日 / 流时结论卡', () => {
  it('岁运夹具的 verdict 四要素进 DOM', () => {
    if (!transit.verdict) throw new Error('bazi-liuyue 夹具缺 verdict');
    expectCardRenders(transit.verdict, '岁运');
  });

  it('流日夹具（含聚焦日）的 verdict 四要素进 DOM', () => {
    if (!liuri.verdict) throw new Error('bazi-liuri-matrix 夹具缺 verdict');
    expect(liuri.focused).not.toBeNull();
    expectCardRenders(liuri.verdict, '流日');
  });

  it('流时夹具（含聚焦时辰）的 verdict 四要素进 DOM', () => {
    if (!liushi.verdict) throw new Error('bazi-liushi-day 夹具缺 verdict');
    expect(liushi.focused).not.toBeNull();
    expectCardRenders(liushi.verdict, '流时');
  });
});
