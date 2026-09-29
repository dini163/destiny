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

/**
 * 段落定位一律取全文相等，不留子串查找那条路：白话段与判语段各自就是一个 `<p>` 的
 * `textContent`，整段比一次就把「渲染的是全文而不是首行」一并钉死；子串版要靠
 * 「前 12 字在夹具里唯一」这条夹具事实才不错位，语料一改就可能配错 `<p>` 而静默变绿。
 * 总论那一条更是只能用全文：`PLAIN_SUMMARY_FRAME` 把 `summary` 原句嵌在白话总论里
 * （实测 `plain_summary.includes(summary)` → true），子串查找会先命中前者的 `<p>`，
 * 于是拿同一个元素和自己比 DOM 序，`compareDocumentPosition` 返回 0，断言必假红。
 * 复测：`cd frontend && node -e "const c=require('./tests/fixtures/bazi-natal.json'); console.log(c.interpretation.plain_summary.includes(c.interpretation.summary))"`
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
