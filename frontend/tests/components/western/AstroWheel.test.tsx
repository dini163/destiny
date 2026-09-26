/**
 * `AstroWheel`（天球黄道命盘轮图）的挂载测：盘面几何不自相矛盾（Task 8B 判据 3）。
 *
 * 为什么值得钉：轮图是本任务里唯一「前端自己把经度画成坐标」的地方，也是唯一画不出
 * 度数文本的组件——`AstroWheel.tsx:43-44` 的 docstring 明写 "Exact degrees live in the
 * ephemeris table"，所以度数的对拍住在 `PlanetTable.test.tsx`，这里只审几何。
 * 三条断言由弱到强：① 十颗行星标记确实画在两个交替半径上（不是全挤在圆心或半径写死）；
 * ② `wheelAngle` 的单调序与 DOM 上实际角度的单调序一致（把「排序用的角度」与「落笔用的角度」
 * 钉成同一个）；③ 两两之间的屏面角差等于其黄经差（mod 360）——这条**只用 DOM 坐标与响应的
 * `longitude`**，不引 `wheelAngle`，于是「旋转用错了字段」（例如拿 `houses[0].longitude`
 * 或 `axes[1]` 当上升）这类错误无法靠同一支函数自证清白。
 *
 * 复测口径（2026-09-27 全绿，4 项）：
 *   cd frontend && npx vitest run tests/components/western/AstroWheel.test.tsx
 * 上升经度与十颗标记半径的来路：
 *   cd frontend && node -e "const c=require('./tests/fixtures/western-natal.json');console.log(c.axes.map(a=>a.name+':'+a.longitude).join(' '))"
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { AstroWheel } from '../../../src/components/western/AstroWheel';
import { wheelAngle } from '../../../src/lib/astro';
import type { WesternChart } from '../../../src/types/western';
import { readFixture } from '../../lib/readFixture';

const natal = readFixture('western-natal') as WesternChart;

// 组件里的画布常量（`AstroWheel.tsx:13-14`）：viewBox 600×600，圆心 (300, 300)。
const CENTER = 300;

afterEach(cleanup);

/** 屏面角：SVG 的 y 轴向下，故「逆时针自 3 点方向」= atan2(圆心y − y, x − 圆心x)。 */
function screenAngle(x: number, y: number): number {
  const degrees = (Math.atan2(CENTER - y, x - CENTER) * 180) / Math.PI;
  return ((degrees % 360) + 360) % 360;
}

/** 十颗行星标记：组件里唯一的 `r=13` 圆，顺序与 `planets` 数组一致。 */
function markers(container: HTMLElement): Array<{ x: number; y: number; radius: number }> {
  return Array.from(container.querySelectorAll('svg circle[r="13"]')).map((circle) => {
    const x = Number(circle.getAttribute('cx'));
    const y = Number(circle.getAttribute('cy'));
    return { x, y, radius: Math.hypot(x - CENTER, y - CENTER) };
  });
}

describe('AstroWheel 的盘面几何（Task 8B 判据 3）', () => {
  it('十颗标记落在两个交替半径上，且半径就在宫头环内侧', () => {
    const view = render(
      <AstroWheel planets={natal.planets} axes={natal.axes} houses={natal.houses} aspects={natal.aspects} />,
    );
    const points = markers(view.container);
    expect(natal.planets).toHaveLength(10);
    expect(points).toHaveLength(10);
    // R_PLANET_A = 196 / R_PLANET_B = 174（AstroWheel.tsx:23-24 的错峰半径）。
    points.forEach((point) => {
      expect([174, 196]).toContain(Math.round(point.radius));
    });
    expect(points.filter((point) => Math.round(point.radius) === 196)).toHaveLength(5);
  });

  it('wheelAngle 的单调序与 DOM 实际角度的单调序一模一样', () => {
    const view = render(
      <AstroWheel planets={natal.planets} axes={natal.axes} houses={natal.houses} aspects={natal.aspects} />,
    );
    const asc = natal.axes.filter((axis) => axis.name === 'ASC')[0].longitude;
    const points = markers(view.container);
    expect(points).toHaveLength(natal.planets.length);

    const byFunction = natal.planets.map((planet, index) => ({ index, angle: wheelAngle(planet.longitude, asc) % 360 }));
    const byDom = points.map((point, index) => ({ index, angle: screenAngle(point.x, point.y) }));
    const order = (rows: Array<{ index: number; angle: number }>) =>
      [...rows].sort((a, b) => a.angle - b.angle).map((row) => row.index);
    expect(order(byDom)).toEqual(order(byFunction));
    // 相邻两颗的最小角距实测 8.48°（把 `western-natal.json` 的十曜经度代进本文件的
    // `screenAngle` 即可复现），故上一条的排序不会因接近平局而随机翻面。
    const sorted = [...byDom].sort((a, b) => a.angle - b.angle).map((row) => row.angle);
    const gaps = sorted.slice(1).map((angle, i) => angle - sorted[i]);
    expect(Math.min(...gaps)).toBeGreaterThan(1);
  });

  it('两两屏面角差等于黄经差：轮面是刚性均匀投影，旋转只是把上升搬到 9 点方向', () => {
    const view = render(
      <AstroWheel planets={natal.planets} axes={natal.axes} houses={natal.houses} aspects={natal.aspects} />,
    );
    const points = markers(view.container);
    expect(points).toHaveLength(natal.planets.length);

    const pairs: string[] = [];
    for (let a = 0; a < natal.planets.length; a += 1) {
      for (let b = a + 1; b < natal.planets.length; b += 1) {
        const measured = (screenAngle(points[b].x, points[b].y) - screenAngle(points[a].x, points[a].y) + 360) % 360;
        const zodiacal =
          (((natal.planets[b].longitude - natal.planets[a].longitude) % 360) + 360) % 360;
        if (Math.abs(measured - zodiacal) > 1e-6) {
          pairs.push(`${natal.planets[a].name}→${natal.planets[b].name}: DOM ${measured} / 黄经 ${zodiacal}`);
        }
      }
    }
    expect(pairs).toEqual([]);
  });

  it('上升与下降两枚角标落在同一水平直径的两端（ASC 在 9 点、DES 在 3 点）', () => {
    const view = render(
      <AstroWheel planets={natal.planets} axes={natal.axes} houses={natal.houses} aspects={natal.aspects} />,
    );
    const badges = ['ASC', 'DES'].map((name) => {
      const text = view.getByText(name);
      return { name, x: Number(text.getAttribute('x')), y: Number(text.getAttribute('y')) };
    });
    const [asc, des] = badges;
    // R_AXIS_BADGE = 202：上升角标在圆心正左方，下降在正右方。
    expect(asc.x).toBeCloseTo(CENTER - 202, 6);
    expect(asc.y).toBeCloseTo(CENTER, 6);
    expect(des.x).toBeCloseTo(CENTER + 202, 6);
    expect(des.y).toBeCloseTo(CENTER, 6);
    expect(screenAngle(asc.x, asc.y)).toBeCloseTo(180, 6);
    expect(screenAngle(des.x, des.y)).toBeCloseTo(0, 6);
  });
});
