/**
 * 六维卡的阅读顺序测：白话详解必须排在专业判语之前（白话 spec §6）。
 *
 * 钉的是「谁先读到」而不是样式——`plain` 与 `narrative` 都是 `<p>`，靠 class 断言等于
 * 断一个随时可改的字符串；这里用 `compareDocumentPosition` 钉 DOM 真实顺序，
 * 组件把两段换任何容器都照样有效。总论单独一条，防止它被顺手并进卡片里。
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

  it('六维卡之后另有总论段，且白话总论排在档位复述之前', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    const plainSummary = paragraphByExact(reading.plain_summary);
    const summary = paragraphByExact(reading.summary);
    expect(precedes(plainSummary, summary)).toBe(true);
  });
});
