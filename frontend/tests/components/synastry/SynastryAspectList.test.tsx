/**
 * `SynastryAspectList`（合盘「人对人相位」表）的挂载测——判据 5 的「计数口径不骗人」。
 *
 * 为什么值得钉：这个组件唯一会自己改变数字的地方是筛选：`useState<Filter>('counted')`
 * 默认只显示 `counted` 为真的行，而计数器印的是 `{shown.length} / {aspects.length} 条`。
 * 两个数都来自 props 数组的真实长度，只要有一处改成写死、改成 `filter` 之后再 `slice`、
 * 或者单位从「条」漂到「对」，页面就会用一个好看的分数骗用户。所以三条腿一起钉：
 * ① 默认 8 行、逐格等于后端字段；② 切到「全部」变 56 行、切回变 8 行，且筛选只是删行
 * （不改行内容也不改行序）；③ 计数器的两个数与 props 长度、与账本行数三者对得上。
 *
 * 「56 条相位」与「47 对星名」的关系值得一并钉死，因为它是用户最容易误读的单位：
 * 56 行里 `(point_a, point_b)` 有序对恰好 56 个（无一重复），而把星名当作**无序**一对去
 * 重只剩 47 个——差的 9 对是同一组星名在两个方向上各检出一次（例：甲木星对乙天王星
 * 与甲天王星对乙木星，各自的容许度不同）。它们是两条真实不同的相位（端点不同、方向不同），
 * 谁要是按无序去重「顺手修一下重复」，就会当场少掉 9 条相位并少算分。
 *
 * 另外两处现状钉（不是缺陷，改了就红）：
 * - 相位种类中文名（合相/六合/刑相/拱相/冲相）是前端 `aspectStyle`（`src/lib/astro.ts:38-44`）
 *   给的，后端只给英文 `type` 与 `glyph`，没有对家可比；但性质中文名后端**也给**
 *   （`nature_zh`），前端却仍用自己的 `natureStyle(...).label`（`src/lib/transit.ts:55-59`）——
 *   两套表今天逐字相同（融合/和谐/挑战），第 1 条把相等钉住，分叉即红。
 * - 计入的 8 条**不是**全表最紧的 8 条（最紧的 0.05° 是未计入的「冥王星 六合 天王星」）：
 *   `counted` 只看端点是否个人 POINT，与容许度无关。这条是页面「计入相契度」这句话的
 *   真语义，第 3 条按子序列而不是按前缀来比，就是为了不把这条误当成排序。
 *
 * 复测口径（2026-09-27 全绿，6 项）：
 *   cd frontend && npx vitest run tests/components/synastry/SynastryAspectList.test.tsx
 * 56 / 8 / 2（核心）/ 有序 56 / 无序 47 / 最紧一条的容许度原文：
 *   cd frontend && node -e "const c=require('./tests/fixtures/synastry.json');const a=c.synastry_aspects;const u=x=>[x.point_a,x.point_b].sort().join(String.fromCharCode(126));console.log(a.length,a.filter(x=>x.counted).length,a.filter(x=>x.core_bond).length,new Set(a.map(x=>x.point_a+String.fromCharCode(62)+x.point_b)).size,new Set(a.map(u)).size,Math.min(...a.map(x=>x.orb)),JSON.stringify(a.find(x=>x.counted).orb))"
 */
import { cleanup, fireEvent, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SynastryAspectList } from '../../../src/components/synastry/SynastryAspectList';
import { aspectStyle } from '../../../src/lib/astro';
import { natureStyle } from '../../../src/lib/transit';
import type { SynastryChart } from '../../../src/types/synastry';
import { readFixture } from '../../lib/readFixture';

const synastry = readFixture('synastry') as SynastryChart;
const aspects = synastry.synastry_aspects;
const counted = aspects.filter((aspect) => aspect.counted);

// vitest 未开 globals，RTL 的自动 cleanup 注册不上（它探测的是全局 afterEach），故显式装。
afterEach(cleanup);

function itemsOf(container: HTMLElement): HTMLElement[] {
  return within(container).getAllByRole('listitem');
}

function textOf(container: HTMLElement): string[] {
  return itemsOf(container).map((item) => item.textContent ?? '');
}

function counterOf(container: HTMLElement): string {
  // 计数器是只含文本节点的 span，RTL 按直接文本子节点取文，故整串逐字匹配。
  return within(container).getByText(/\d+ \/ \d+ 条/).textContent ?? '';
}

describe('SynastryAspectList 的逐格透传（Task 8B 判据 5）', () => {
  it('默认只看计入的 8 行：每格都是响应字段本身，性质中文与后端 nature_zh 逐字相同', () => {
    expect(aspects).toHaveLength(56);
    expect(counted).toHaveLength(8);

    const { container } = render(<SynastryAspectList aspects={aspects} />);
    const items = itemsOf(container);
    expect(items).toHaveLength(8);
    expect(counterOf(container)).toBe('8 / 56 条 · 按容许度排序');

    counted.forEach((aspect, index) => {
      const item = items[index];
      expect(item).toHaveTextContent('甲');
      expect(item).toHaveTextContent('乙');
      expect(item).toHaveTextContent(aspect.point_a_zh);
      expect(item).toHaveTextContent(aspect.point_a_glyph);
      expect(item).toHaveTextContent(aspect.point_b_zh);
      expect(item).toHaveTextContent(aspect.glyph);
      expect(item).toHaveTextContent(aspectStyle(aspect.type).label);
      expect(within(item).getByText(`容 ${aspect.orb.toFixed(2)}°`)).toBeInTheDocument();
      // 页面印的是前端表的标签，这里对一次后端给的同一个词——两套表必须逐字相同。
      expect(natureStyle(aspect.nature).label).toBe(aspect.nature_zh);
      expect(item).toHaveTextContent(aspect.nature_zh);
    });

    // 核心徽章只在后端标了 core_bond 的行上，且全表恰有两行（火星刑金星、月亮六合金星）。
    expect(counted.filter((aspect) => aspect.core_bond)).toHaveLength(2);
    expect(items.map((item) => /核心/.test(item.textContent ?? ''))).toEqual(
      counted.map((aspect) => aspect.core_bond),
    );
  });

  it('计入行中最紧的一条照原文钉住，容许度两位小数口径不会被悄悄改掉', () => {
    const { container } = render(<SynastryAspectList aspects={aspects} />);
    const items = itemsOf(container);
    // 夹具原文：计入行按容许度升序，第 1 行 月亮 △ 上升 1.19°，第 5 行 水星 ☍ 水星 4.03°。
    expect(counted[0].point_a_zh).toBe('月亮');
    expect(counted[0].point_b_zh).toBe('上升');
    expect(counted[0].type).toBe('trine');
    expect(counted[0].orb).toBe(1.19);
    expect(within(items[0]).getByText('容 1.19°')).toBeInTheDocument();
    expect(items[0]).toHaveTextContent('拱相');
    expect(items[0]).not.toHaveTextContent('核心');
    expect(counted[4].orb).toBe(4.03);
    expect(within(items[4]).getByText('容 4.03°')).toBeInTheDocument();
    // 「按容许度排序」这句页面声称：对 props 自身成立，前端没有再排一次。
    const orbs = aspects.map((aspect) => aspect.orb);
    expect([...orbs].sort((x, y) => x - y)).toEqual(orbs);
  });
});

describe('SynastryAspectList 的筛选与计数（Task 8B 判据 5）', () => {
  it('切到「全部」变 56 行、切回变 8 行，计数器两个数始终来自 props 长度', () => {
    const { container } = render(<SynastryAspectList aspects={aspects} />);
    const group = within(container).getByRole('radiogroup', { name: '相位筛选' });
    expect(within(group).getByRole('radio', { name: '计入相契度' })).toHaveAttribute('aria-checked', 'true');
    const countedRows = textOf(container);
    expect(countedRows).toHaveLength(8);
    expect(counterOf(container)).toBe('8 / 56 条 · 按容许度排序');

    fireEvent.click(within(group).getByRole('radio', { name: '全部' }));
    const allRows = textOf(container);
    expect(allRows).toHaveLength(56);
    expect(counterOf(container)).toBe('56 / 56 条 · 按容许度排序');
    expect(within(group).getByRole('radio', { name: '全部' })).toHaveAttribute('aria-checked', 'true');

    fireEvent.click(within(group).getByRole('radio', { name: '计入相契度' }));
    expect(textOf(container)).toEqual(countedRows);
    expect(counterOf(container)).toBe('8 / 56 条 · 按容许度排序');
  });

  it('筛选只是删行：计入的 8 行是全表 56 行的同序子序列，行文本一字未改', () => {
    const { container } = render(<SynastryAspectList aspects={aspects} />);
    fireEvent.click(within(container).getByRole('radio', { name: '全部' }));
    const allRows = textOf(container);
    expect(allRows).toHaveLength(56);
    fireEvent.click(within(container).getByRole('radio', { name: '计入相契度' }));
    const shownRows = textOf(container);
    expect(shownRows).toHaveLength(8);

    // 子序列判定（不是前缀）：计入的并非最紧的 8 条，按前缀比会把「counted = 排序」写进测里。
    let cursor = 0;
    shownRows.forEach((row) => {
      const found = allRows.slice(cursor).indexOf(row);
      expect(found, `计入的一行在「全部」里找不到同文行: ${row}`).toBeGreaterThanOrEqual(0);
      cursor += found + 1;
    });
    // 未计入的 48 行确实只是被隐藏：字面量 48 与上面的 56/8 对账（全表−计入=未计入
    // 这一差值不再单独断言——56、8、48 三个数都各自有钉，差值永不自立变红）。
    expect(aspects.filter((aspect) => !aspect.counted)).toHaveLength(48);
  });

  it('56 条 = 56 个有序点名对，无序去重只剩 47：差的 9 对是同一组星名的两个方向', () => {
    const ordered = aspects.map((aspect) => `${aspect.point_a}>${aspect.point_b}`);
    expect(ordered).toHaveLength(56);
    expect(new Set(ordered).size).toBe(56);
    const unordered = aspects.map((aspect) => [aspect.point_a, aspect.point_b].sort().join('~'));
    expect(new Set(unordered).size).toBe(47);
    const tally = new Map<string, number>();
    unordered.forEach((key) => tally.set(key, (tally.get(key) ?? 0) + 1));
    expect([...tally.values()].filter((count) => count === 2)).toHaveLength(9);
  });

  it('计入相契度的 8 条与账本除基准外的 8 行一一对应，规则串由点名与相位拼成', () => {
    const rulesFromAspects = counted.map(
      (aspect) => `synastry.${aspect.point_a}.${aspect.point_b}.${aspect.type}`,
    );
    const factors = synastry.score.factors;
    expect(factors).toHaveLength(9); // 1 基准 + 8 计入
    expect(factors[0].rule).toBe('synastry.base');
    expect(factors.slice(1).map((factor) => factor.rule)).toEqual(rulesFromAspects);
  });
});
