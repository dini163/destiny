/**
 * `SynastryScoreRing`（相契度环 + 可展开赋分账本）的挂载测——判据 5 的「账本自洽」。
 *
 * 为什么值得钉：这一页的立身之处是「环好看，账本可核」——总分必须由一行行能加回去的
 * 增量撑着。可核有三条各自的通道，断在一处不算断全：
 * ① 同一个总分在页面上出现两次（环中心 + 账本行），两处必须同值同档名；
 * ② 账本每一行的增量走 `src/lib/scoring.ts::formatDelta`——AGENTS §2 全库唯一的一位小数
 *    带符号印刷器，`conventions.test.ts` 不变式 5 管着它。本测**自己不再写 toFixed**，
 *    而是 import 它，否则测试就成了第二支口径，页面与测试各错一半也不会红；
 * ③ 两种口径都要加得回去：原始 delta 之和 == `value`（后端保证，`types/scoring.ts` 的
 *    契约），把页面上印出来的一位小数逐行读回来相加也得等于印出来的总分。
 *
 * 46.41 这条夹具的两处现状钉（数字改了要重跑下面的复测）：
 * - 基准行 50 不带符号，其余 8 行带符号；8 行之和 −3.59，50 − 3.59 = 46.41。
 * - 逐行印刷值加起来正好也是 46.4，靠的是「−3.15 印成 −3.1」——`3.15` 在二进制里是
 *   `3.1499…`，`toFixed(1)` 往下取。这不是四舍五入出错，而是浮点表示；但这条相加等式
 *   **对舍入方向敏感**（若那行印成 −3.2，逐行和就变 46.3，与总分的 46.4 差一角），
 *   所以第 4 条把它钉住：谁改了口径，这里先红，而不是留给用户一个加不平的账本。
 * - 页面那句「四档：… 45–59 中和可处 …」是硬编码在组件里的（`SynastryScoreRing.tsx:79`），
 *   而分数来自后端。第 2 条按**当前档名**去那句话里找出它自己的区间再验分数落在里面：
 *   后端换档、或前端把区间写错位，都会红。
 *
 * 复测口径（2026-09-27 全绿，5 项）：
 *   cd frontend && npx vitest run tests/components/synastry/SynastryScoreRing.test.tsx
 * 总分、档名、9 行、逐行印刷串与两种求和：
 *   cd frontend && node -e "const s=require('./tests/fixtures/synastry.json').score;const f=(d,b)=>{const t=Math.abs(d).toFixed(1);return b?t:(d<0?'-'+t:'+'+t)};const p=s.factors.map((x,i)=>f(x.delta,i===0));console.log(s.value,s.tier,s.factors.length,'|',p.join(' '),'| printedSum',p.reduce((a,x)=>a+Number(x),0),'| rawSum',s.factors.reduce((a,x)=>a+x.delta,0),'| nonBase',s.factors.slice(1).reduce((a,x)=>a+x.delta,0))"
 */
import { cleanup, fireEvent, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SynastryScoreRing, synastryTierLook } from '../../../src/components/synastry/SynastryScoreRing';
import { formatDelta } from '../../../src/lib/scoring';
import type { SynastryChart } from '../../../src/types/synastry';
import { readFixture } from '../../lib/readFixture';

const synastry = readFixture('synastry') as SynastryChart;
const score = synastry.score;

// vitest 未开 globals，RTL 的自动 cleanup 注册不上（它探测的是全局 afterEach），故显式装。
afterEach(cleanup);

/** 展开账本，返回它的九行（`ScoreLedger` 折叠时整张表不渲染）。 */
function openLedger(container: HTMLElement): HTMLElement[] {
  const scope = within(container);
  fireEvent.click(scope.getByRole('button', { name: '展开赋分账本' }));
  return within(scope.getByRole('table')).getAllByRole('row');
}

function deltaCells(row: HTMLElement): HTMLElement[] {
  return within(row).getAllByRole('cell');
}

describe('SynastryScoreRing 的总分与档位（Task 8B 判据 5）', () => {
  it('同一个总分在环上与账本里各印一次且同值同档，弧长就是那个分数', () => {
    const { container } = render(<SynastryScoreRing score={score} />);
    const scope = within(container);

    expect(score.value).toBe(46.41);
    expect(score.tier).toBe('中和可处');
    expect(scope.getByRole('img', { name: '相契度 46.4 分，中和可处' })).toBeInTheDocument();
    expect(scope.getAllByText('46.4')).toHaveLength(2); // 环中心 + 账本右上
    expect(scope.getAllByText('中和可处')).toHaveLength(2);

    const svg = scope.getByRole('img');
    const arcs = Array.from(svg.querySelectorAll('circle'));
    expect(arcs).toHaveLength(2); // 底环 + 读数弧
    const arc = arcs[1];
    const radius = Number(arc.getAttribute('r'));
    expect(radius).toBeGreaterThan(0);
    const circumference = 2 * Math.PI * radius;
    expect(Number(arc.getAttribute('stroke-dasharray'))).toBeCloseTo(circumference, 6);
    // 弧占整圈的比例 == value/100：改成 /10 或把 offset 写反都会红。
    const offset = Number(arc.getAttribute('stroke-dashoffset'));
    expect(1 - offset / circumference).toBeCloseTo(score.value / 100, 6);
    // 弧色与档名同一张表查出来，两半不会各改一处。
    expect(arc.getAttribute('stroke')).toBe(synastryTierLook(score.tier).stroke);
    expect(synastryTierLook(score.tier)).not.toEqual(synastryTierLook('未知档名'));
  });

  it('硬编码那句档位说明罩得住当前分数：45–59 段就是中和可处', () => {
    const { container } = render(<SynastryScoreRing score={score} />);
    const blurb = within(container).getByText(/四档/).textContent ?? '';
    const segment = blurb
      .split('·')
      .map((part) => part.trim())
      .find((part) => part.includes(score.tier));
    expect(segment, `四档说明里找不到当前档 ${score.tier}: ${blurb}`).toBe('45–59 中和可处');
    const bounds = (segment ?? '').match(/\d+/g)?.map(Number) ?? [];
    expect(bounds).toEqual([45, 59]);
    expect(score.value).toBeGreaterThanOrEqual(bounds[0]);
    expect(score.value).toBeLessThanOrEqual(bounds[1]);
  });
});

describe('SynastryScoreRing 的赋分账本（Task 8B 判据 5）', () => {
  it('展开后九行逐格对账：标签、一位小数增量走全库唯一的 formatDelta、来源角标不带书名', () => {
    expect(score.factors).toHaveLength(9);
    const { container } = render(<SynastryScoreRing score={score} />);
    const scope = within(container);
    expect(scope.queryByText('基准分')).toBeNull(); // 折叠时账本不占版面
    expect(scope.getByRole('button', { name: '展开赋分账本' })).toHaveAttribute('aria-expanded', 'false');

    const rows = openLedger(container);
    expect(scope.getByRole('button', { name: '收起赋分账本' })).toHaveAttribute('aria-expanded', 'true');
    expect(rows).toHaveLength(9);
    expect(scope.getByText('相契度账本（50 分起算）的赋分账本')).toBeInTheDocument();

    score.factors.forEach((factor, index) => {
      const row = rows[index];
      expect(within(row).getByRole('rowheader')).toHaveTextContent(factor.label);
      const cells = deltaCells(row);
      expect(cells).toHaveLength(2);
      expect(cells[0].textContent).toBe(formatDelta(factor.delta, index === 0));
      // 无账可引的赋分必须显式声明：角标只印前半句，全文留在 title 里。
      const note = within(cells[1]).getByTitle(factor.source);
      expect(note.textContent).toBe('模型参数');
      expect(factor.source).toContain('非古籍赋分');
    });

    // 基准行不带符号，其余带符号（夹具原文逐字）：
    expect(deltaCells(rows[0])[0].textContent).toBe('50.0');
    expect(deltaCells(rows[1])[0].textContent).toBe('+2.8');
    expect(deltaCells(rows[2])[0].textContent).toBe('-2.3');
    expect(deltaCells(rows[4])[0].textContent).toBe('-3.1');
    // 总分在展开前后没有变化：账本不会自己另算一个数。
    expect(scope.getAllByText('46.4')).toHaveLength(2);
  });

  it('两种口径都加得回去：Σ 原始 delta = 46.41，Σ 页面印刷值 = 46.4', () => {
    expect(score.factors[0].rule).toBe('synastry.base');
    expect(score.factors[0].delta).toBe(50);
    expect(score.factors.slice(1).reduce((sum, factor) => sum + factor.delta, 0)).toBeCloseTo(-3.59, 6);
    expect(score.factors.reduce((sum, factor) => sum + factor.delta, 0)).toBeCloseTo(score.value, 6);

    const { container } = render(<SynastryScoreRing score={score} />);
    const printed = openLedger(container).map((row) => Number(deltaCells(row)[0].textContent));
    expect(printed).toHaveLength(9);
    printed.forEach((value, index) =>
      expect(Number.isNaN(value), `第 ${index} 行的增量印刷值读不回数字`).toBe(false),
    );
    expect(printed.reduce((sum, value) => sum + value, 0)).toBeCloseTo(46.4, 6);
    expect(within(container).getAllByText('46.4')).toHaveLength(2);
  });

  it('账本上带「核心」的两行正是那两条 core_bond 相位，规则串与点名对得上', () => {
    const coreRules = synastry.synastry_aspects
      .filter((aspect) => aspect.counted && aspect.core_bond)
      .map((aspect) => `synastry.${aspect.point_a}.${aspect.point_b}.${aspect.type}`);
    expect(coreRules).toHaveLength(2);
    expect(score.factors.filter((factor) => factor.label.endsWith('·核心')).map((factor) => factor.rule)).toEqual(
      coreRules,
    );
  });
});
