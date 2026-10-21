/**
 * 六维卡的阅读顺序测：结论卡片先行、白话详解排在专业判语之前（白话 spec §6、
 * 2026-10-21 verdict-card spec §6）。
 *
 * 钉的是「谁先读到」而不是样式——`plain` 与 `narrative` 都是 `<p>`，靠 class 断言等于
 * 断一个随时可改的字符串；这里用 `compareDocumentPosition` 钉 DOM 真实顺序，
 * 组件把两段换任何容器都照样有效。总论并入结论卡片 headline（`plain_summary` 与
 * `verdict.headline` 同串），不再单挂一段。
 *
 * 复测口径：
 *   cd frontend && npx vitest run tests/components/bazi/DimensionGrid.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { DimensionGrid } from '../../../src/components/bazi/DimensionGrid';
import type { BaziChart } from '../../../src/types/bazi';
import { paragraphByExact, precedes } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const natal = readFixture('bazi-natal') as BaziChart;
const reading = natal.interpretation;

afterEach(cleanup);

describe('DimensionGrid 白话区块', () => {
  it('结论卡片先行：headline 排在第一张六维卡的白话之前', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    const headline = paragraphByExact(reading.verdict.headline);
    const firstPlain = paragraphByExact(reading.six_dimensions[0].plain);
    expect(precedes(headline, firstPlain)).toBe(true);
  });

  it('结论卡片的档位、星级、分项要点与建议全部进 DOM', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    const body = document.body.textContent ?? '';
    expect(body).toContain(reading.verdict.grade);
    expect(body).toContain('★'.repeat(reading.verdict.stars));
    for (const point of reading.verdict.points) {
      expect(body).toContain(point);
    }
    expect(body).toContain(reading.verdict.advice);
  });

  it('每一维的白话段排在专业判语之前', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    for (const dimension of reading.six_dimensions) {
      const plain = paragraphByExact(dimension.plain);
      const narrative = paragraphByExact(dimension.narrative);
      expect(precedes(plain, narrative)).toBe(true);
    }
  });

  it('白话段的每一行都进了 DOM，而不是只渲染首行', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    for (const dimension of reading.six_dimensions) {
      const plain = paragraphByExact(dimension.plain);
      // 全等定位失败只说"找不到 <p>"，逐行这条才点名缺的是哪一行。
      for (const line of dimension.plain.split('\n')) {
        expect(plain.textContent).toContain(line);
      }
    }
  });

  it('六维卡之后仍有档位复述行，且排在最后一张卡的白话之后', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    const lastPlain = paragraphByExact(reading.six_dimensions[reading.six_dimensions.length - 1].plain);
    const summary = paragraphByExact(reading.summary);
    expect(precedes(lastPlain, summary)).toBe(true);
  });
});
