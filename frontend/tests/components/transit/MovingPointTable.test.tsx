/**
 * `MovingPointTable`（行运页的运动层星历表）的挂载测——三层各灌一次。
 *
 * 为什么值得钉：三张表（行运 / 次限 / 太阳弧）共用同一个组件，页面只靠
 * `modeData`（`src/lib/transit.ts:67-79`）在三个分支里选一个数组递进去
 * （`TransitPage.tsx:149` 取、`:203` 渲染）。选错数组时组件不会报错：三层都是
 * 十个同名同型的 `MovingPoint`，页面只是安静地把次限的读数标成「行运」。
 * 但**分层挂载钉不住选错数组**——变异实测（2026-09-27，把 `transit.ts:75/:77`
 * 的 `progression`/`solarArc` 两层 `positions` 互换）：本文件第 1、3 条仍绿，
 * 真变红的是第 2 条的 ℞ 条数字面量 `[4,0,1]` 与 `tests/lib/transit.test.ts:41-43`
 * 的 `toBe` 同一性断言。「跨层不串行」由那两处钉住；本文件三次挂载钉的是
 * **渲染映射**——该层的数组一旦递进来，每个单元格必须逐字印它自己的字段。
 * 这属于判据 1 的透传腿在行运页的对应面：真实 JSON 灌进去，渲染文本必须逐字
 * 等于响应字段。
 *
 * 一处刻意的「看起来像 bug 其实不是」：次限与太阳弧的**太阳**一行完全相同
 * （都是 水瓶座 7°36'、本命第 11 宫）。这正是太阳弧的定义——弧长就是次限太阳相对
 * 本命太阳走过的角度，参照点自己推进后必然落回次限太阳。第 3 条把它钉成「只有这一行
 * 重合」，将来别的行也开始重合（= 两层的推进互相串了）就会红。
 *
 * RTL 陷阱（本文件三次挂载，必踩）：`render()` 返回的查询绑定在 `baseElement`
 * （即 `document.body`）而不是 `view.container`，三个实例又挂在同一个 body 里，
 * 十个星体名还层间重复——不用 `within(view.container)` 收口，第一次挂载就能查到
 * 第三次的行。见 `tests/components/western/BigThree.test.tsx` 的同条记录。
 *
 * 复测口径（2026-09-27 全绿，3 项）：
 *   cd frontend && npx vitest run tests/components/transit/MovingPointTable.test.tsx
 * 三层行数与逆行条数（4/0/1）、以及「次限与太阳弧只有太阳一行重合」的来路：
 *   cd frontend && node -e "const c=require('./tests/fixtures/transit.json');const L=[c.transit_positions,c.progression.positions,c.solar_arc.positions];console.log(L.map(a=>[a.length,a.filter(p=>p.retrograde).length]));const k=(a,n)=>a[n].name+':'+a[n].degree_text+':'+a[n].natal_house;for(const p of [[0,1],[0,2],[1,2]])console.log(p.join('-'),L[p[0]].map((_,n)=>k(L[p[0]],n)===k(L[p[1]],n)?n:-1).filter(v=>v>=0))"
 */
import { cleanup, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { MovingPointTable } from '../../../src/components/transit/MovingPointTable';
import { modeData } from '../../../src/lib/transit';
import type { TransitChart, MovingPoint } from '../../../src/types/transit';
import type { TransitMode } from '../../../src/lib/transit';
import { readFixture } from '../../lib/readFixture';

const transit = readFixture('transit') as TransitChart;

// vitest 未开 globals，RTL 的自动 cleanup 注册不上（它探测的是全局 afterEach），故显式装。
afterEach(cleanup);

/** 一次挂载 = 一层。收口到该实例自己的 container，返回它拿到的数据与它的行。 */
function mountLayer(mode: TransitMode): { points: MovingPoint[]; rows: HTMLElement[] } {
  const points = modeData(transit, mode).positions;
  const view = render(<MovingPointTable points={points} />);
  return { points, rows: within(view.container).getAllByRole('row') };
}

/** 一行五格：星体、星座、黄经度、本命宫、逆行。 */
function cellsOf(row: HTMLElement): HTMLElement[] {
  return within(row).getAllByRole('cell');
}

function retroMark(cell: HTMLElement): '℞' | '—' {
  return cell.textContent === '℞' ? '℞' : '—';
}

describe('MovingPointTable 三层各自挂载（Task 8B 判据 4）', () => {
  const modes = ['transit', 'progression', 'solarArc'] as const;

  it('每一层单独灌：表头 + 10 行，五格全是该层响应字段本身', () => {
    modes.forEach((mode) => {
      const { points, rows } = mountLayer(mode);
      expect(points).toHaveLength(10);
      expect(rows).toHaveLength(11); // 1 表头 + 10 曜

      points.forEach((point, index) => {
        const cells = cellsOf(rows[index + 1]);
        expect(cells).toHaveLength(5);
        expect(cells[0]).toHaveTextContent(point.glyph);
        expect(cells[0]).toHaveTextContent(point.name_zh);
        expect(cells[1]).toHaveTextContent(point.sign_glyph);
        expect(cells[1]).toHaveTextContent(point.sign_zh);
        expect(cells[2].textContent).toBe(point.degree_text);
        expect(cells[3].textContent).toBe(String(point.natal_house));
        expect(cells[4].textContent).toBe(point.retrograde ? '℞' : '—');
      });
    });
  });

  it('逆行列按整表对账：三层 ℞ 的条数分别是 4、0、1，与 retrograde 为真的条数一致', () => {
    const expected = [4, 0, 1];
    modes.forEach((mode, index) => {
      const { points, rows } = mountLayer(mode);
      expect(points.filter((point) => point.retrograde)).toHaveLength(expected[index]);
      // 逐格的 ℞/— 相等已由第 1 条的 textContent 断言钉住（那条更强：直接比字面量，
      // 不经 `retroMark` 的「非 ℞ 即 —」折叠）。这里只留整表条数对账，不重复逐格比对。
      const marks = rows.slice(1).map((row) => retroMark(cellsOf(row)[4]));
      expect(marks.filter((mark) => mark === '℞')).toHaveLength(expected[index]);
    });
  });

  it('三层互不串行：星体名与本命宫的组合两两不等，唯有太阳一行次限与太阳弧重合', () => {
    const mounted = modes.map((mode) => mountLayer(mode));
    // 三层都是同一批星体名（页面靠行位置而不是名字区分层），故比对取「名 + 度数 + 本命宫」。
    const keys = mounted.map(({ points }) =>
      points.map((point) => `${point.name}:${point.degree_text}:${point.natal_house}`),
    );
    expect(new Set(keys.map((list) => list.join('|'))).size).toBe(3);

    // 逐行比对，只有次限/太阳弧的太阳（index 0）相同；其余 20 个跨层同行位置全不同。
    const coincidences: number[] = [];
    for (let index = 0; index < 10; index += 1) {
      if (keys[1][index] === keys[2][index]) coincidences.push(index);
      if (keys[0][index] === keys[1][index] || keys[0][index] === keys[2][index]) coincidences.push(index);
    }
    expect(coincidences).toEqual([0]);
    expect(transit.progression.positions[0].name).toBe('Sun');
    expect(transit.solar_arc.positions[0].name).toBe('Sun');
    expect(mounted[1].rows[1]).toHaveTextContent('7°36');
    expect(mounted[2].rows[1]).toHaveTextContent('7°36');
  });
});
