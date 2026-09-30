/**
 * 五格卡的阅读顺序与降级支路（spec §10 清单类就地嵌）。
 *
 * 两份夹具都是真实响应：`name.json`（李/明，五格齐全）与 `name-unresolved.json`
 * （张/𠀋，名在语料外，四格算不出数）。后者是唯一能测「未核定」支路的东西——手写一份
 * 假响应就是伪造后端输出（AGENTS.md §9），所以它进了录制脚本（Task 5 Step 10）。
 *
 * 定位一律按卡（`<article>`）划定范围：`FiveGrids` 的卡片序与 `grids` 同序（该文件头注），
 * 而两格同数理时判语逐字相同（实测 `李/明` 的人格与总格都是数理 15），全站全文定位会
 * 抓到前一张卡那句。判语顺序这条断言说的是**一张卡内部**谁先读到，所以范围也照卡收。
 * 复测：cd frontend && npx vitest run tests/components/name/FiveGrids.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { FiveGrids } from '../../../src/components/name/FiveGrids';
import type { NameAnalysis } from '../../../src/types/name';
import { paragraphByExactIn, precedes } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const full = readFixture('name') as NameAnalysis;
const degraded = readFixture('name-unresolved') as NameAnalysis;

afterEach(cleanup);

/** 卡面与 `grids` 同序；件本身不排序，所以这里按序配对是组件的既有契约而不是测试假设。 */
function cardsOf(grids: typeof full.grids): Element[] {
  const { container } = render(<FiveGrids grids={grids} />);
  const cards = [...container.querySelectorAll('article')];
  expect(cards.length).toBe(grids.length);
  return cards;
}

describe('FiveGrids 白话区块', () => {
  it('每一格的白话段排在这一格的专业判语之前', () => {
    const cards = cardsOf(full.grids);
    full.grids.forEach((grid, index) => {
      if (grid.verdict === null) throw new Error('李/明 五格应全部核定，夹具有变');
      // 空白的 plain 也能被下面的定位满足，先按语料契约（每条 ≥40 字）钉住它说了话。
      expect(grid.plain.length).toBeGreaterThan(40);
      const card = cards[index];
      expect(precedes(paragraphByExactIn(card, grid.plain), paragraphByExactIn(card, grid.verdict))).toBe(
        true,
      );
    });
  });

  it('未核定的一格搬受控的那一句，页面不再自造文案', () => {
    const pending = degraded.grids.map((grid, index) => ({ grid, index })).filter((one) => one.grid.value === null);
    expect(pending.length).toBe(4);
    const cards = cardsOf(degraded.grids);
    for (const { grid, index } of pending) {
      expect(grid.plain.length).toBeGreaterThan(40);
      expect(paragraphByExactIn(cards[index], grid.plain).textContent).toBe(grid.plain);
      expect(document.body.textContent).not.toContain('笔画未核定，本格不出断语');
    }
  });
});
