/**
 * `PlanetTable`（星历表：十曜 + 北南交点）的挂载测。
 *
 * 为什么值得钉：这张表是西洋本命页里唯一把每个字段都印全的地方（`name_zh`/`sign_zh`/
 * `sign`/`degree_text`/宫位/逆行），因此是「透传腿」最好的落点——真实 JSON 灌进组件后，
 * 渲染文本与响应字段必须逐字相等。走查（`docs/superpowers/plans/2026-09-26-fullstack-test-walkthrough.md`
 * Task 8 本命盘节 项 6）当时是 ≥33 处字面逐项对一次真实响应，本文件把那次人工比对变成机器断言。
 *
 * 交点两行走的是另一条腿：响应只有 `north_node_longitude`/`south_node_longitude`，没有
 * `degree_text`，所以那两格的度数文本是前端自己格式化的（口径与分叉面见
 * `tests/lib/astro.test.ts` 的 F-A1-12 现状钉）。这里同时钉两件事：渲染值等于同一口径的
 * 函数结果，也等于夹具经度的字面读数；而同一行的 `sign_zh` 仍来自后端——同一行两格口径
 * 自此分叉，正是 F-A1-12 写「出一次就是给用户看一个不存在的角度」的那处危害面。
 *
 * 复测口径（2026-09-27 全绿，3 项）：
 *   cd frontend && npx vitest run tests/components/western/PlanetTable.test.tsx
 */
import { cleanup, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { PlanetTable } from '../../../src/components/western/PlanetTable';
import { formatDegreeInSign } from '../../../src/lib/astro';
import type { WesternChart } from '../../../src/types/western';
import { readFixture } from '../../lib/readFixture';

const natal = readFixture('western-natal') as WesternChart;

// vitest 未开 globals，RTL 的自动 cleanup 注册不上（它探测的是全局 afterEach），故显式装。
afterEach(cleanup);

/** 表头一行，其后每行对应 `planets` 的一条，最后两行是北/南交点。 */
function rowsOf(view: ReturnType<typeof render>): HTMLElement[] {
  return view.getAllByRole('row');
}

function cellsOf(row: HTMLElement): HTMLElement[] {
  return within(row).getAllByRole('cell');
}

describe('PlanetTable 的透传腿（Task 8B 判据 1）', () => {
  it('十曜逐行：星体名、星座中英、度数、宫位、逆行标记五格全是响应字段本身', () => {
    const view = render(<PlanetTable planets={natal.planets} nodes={natal.nodes} />);
    expect(natal.planets).toHaveLength(10);
    const rows = rowsOf(view);
    expect(rows).toHaveLength(13); // 1 表头 + 10 曜 + 2 交点

    natal.planets.forEach((planet, index) => {
      const cells = cellsOf(rows[index + 1]);
      expect(cells).toHaveLength(5);
      expect(cells[0]).toHaveTextContent(planet.glyph);
      expect(cells[0]).toHaveTextContent(planet.name_zh);
      expect(cells[1]).toHaveTextContent(planet.sign_zh);
      expect(cells[1]).toHaveTextContent(planet.sign);
      expect(cells[2].textContent).toBe(planet.degree_text);
      expect(cells[3].textContent).toBe(`第 ${planet.house} 宫`);
      expect(cells[4].textContent).toBe(planet.retrograde ? '℞ 逆行' : '顺行');
    });
  });

  it('逆行列按整表对账：℞ 的条数与 retrograde 为真的条数相等，且落在同名那一行', () => {
    const view = render(<PlanetTable planets={natal.planets} nodes={natal.nodes} />);
    const retrograde = natal.planets.filter((planet) => planet.retrograde);
    expect(retrograde).not.toHaveLength(0);
    expect(retrograde).toHaveLength(1); // 本命夹具：土星一星逆行

    const marks = rowsOf(view)
      .slice(1)
      .map((row) => cellsOf(row)[4].textContent);
    expect(marks).toEqual([
      ...natal.planets.map((planet) => (planet.retrograde ? '℞ 逆行' : '顺行')),
      '平交点',
      '平交点',
    ]);
  });

  it('北/南交点两行：度数走自制腿且等于字面读数，同一行的星座中文名仍来自后端', () => {
    const view = render(<PlanetTable planets={natal.planets} nodes={natal.nodes} />);
    const rows = rowsOf(view);
    const north = cellsOf(rows[11]);
    const south = cellsOf(rows[12]);

    expect(north[0]).toHaveTextContent('北交点');
    expect(south[0]).toHaveTextContent('南交点');
    // 自制腿：响应没有 degree_text，前端只能自己算——口径与字面读数一起钉住。
    expect(north[2].textContent).toBe(formatDegreeInSign(natal.nodes.north_node_longitude));
    expect(north[2].textContent).toBe("5°02'");
    expect(south[2].textContent).toBe(formatDegreeInSign(natal.nodes.south_node_longitude));
    expect(south[2].textContent).toBe("5°02'");
    // 后端腿：两交点相差半圈（夹具里北交点 125.0406°、南交点 305.0406°），座名必然不同，
    // 而页面只能取响应给的那两个。
    expect(Math.abs(natal.nodes.north_node_longitude - natal.nodes.south_node_longitude)).toBeCloseTo(180, 4);
    expect(natal.nodes.north_node_sign_zh).not.toBe(natal.nodes.south_node_sign_zh);
    expect(north[1]).toHaveTextContent(natal.nodes.north_node_sign_zh);
    expect(north[1]).toHaveTextContent(natal.nodes.north_node_sign);
    expect(south[1]).toHaveTextContent(natal.nodes.south_node_sign_zh);
    expect(south[1]).toHaveTextContent(natal.nodes.south_node_sign);
    expect(north[3].textContent).toBe(`第 ${natal.nodes.north_node_house} 宫`);
    expect(south[3].textContent).toBe(`第 ${natal.nodes.south_node_house} 宫`);
  });
});
