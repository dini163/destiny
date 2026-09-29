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
import { readFixture } from '../../lib/readFixture';

const natal = readFixture('bazi-natal') as BaziChart;
const reading = natal.interpretation;

afterEach(cleanup);

/** 文档序：a 在 b 之前为真。 */
function precedes(a: Element, b: Element): boolean {
  return (
    a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING
  ) !== 0;
}

function paragraphByText(snippet: string): Element {
  const el = [...document.querySelectorAll('p')].find((p) =>
    p.textContent?.includes(snippet),
  );
  if (!el) throw new Error(`找不到含该文本的 <p>：${snippet.slice(0, 20)}`);
  return el;
}

/**
 * 全文相等的段落查找——总论那一条**只能**用它，不能用上面的子串版：
 * `PLAIN_SUMMARY_FRAME` 把 `summary` 原句嵌在白话总论里（实测
 * `plain_summary.includes(summary)` → true），子串查找会先命中前者的 <p>，
 * 于是拿同一个元素和自己比 DOM 序，`compareDocumentPosition` 返回 0，断言必假红。
 * 复测：cd frontend && node -e "const c=require('./tests/fixtures/bazi-natal.json');
 * console.log(c.interpretation.plain_summary.includes(c.interpretation.summary))"
 */
function paragraphByExact(text: string): Element {
  const el = [...document.querySelectorAll('p')].find((p) => p.textContent === text);
  if (!el) throw new Error(`找不到文本全等的 <p>：${text.slice(0, 20)}`);
  return el;
}

describe('DimensionGrid 白话区块', () => {
  it('每一维的白话段排在专业判语之前', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    for (const dimension of reading.six_dimensions) {
      const plain = paragraphByText(dimension.plain.split('\n')[0]);
      const narrative = paragraphByText(dimension.narrative.slice(0, 12));
      expect(precedes(plain, narrative)).toBe(true);
    }
  });

  it('白话段的每一行都进了 DOM，而不是只渲染首行', () => {
    if (!reading) throw new Error('夹具缺 interpretation');
    render(<DimensionGrid reading={reading} />);
    for (const dimension of reading.six_dimensions) {
      const plain = paragraphByText(dimension.plain.split('\n')[0]);
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
