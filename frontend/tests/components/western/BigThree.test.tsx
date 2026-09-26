/**
 * `BigThree`（本命三巨头：日 / 月 / 升）的挂载测，夹具取合盘响应里的**两份**本命盘。
 *
 * 为什么值得钉：判据 5 的第一条——「合盘的两造不串行」。合盘页把 `person_a` 与 `person_b`
 * 两套 `planets`/`axes` 分别灌进同一个组件渲染两次（`pages/SynastryPage.tsx`），于是
 * 「甲的卡上印了乙的座名」这类事故的真实形状只有并排灌两份真盘才看得见；本命夹具只有一份盘，
 * 测不出一条串行。断言取**互斥**形式：甲的三个 `degree_text` 在乙的渲染里必须查不到，
 * 反向同理——串行的实现（两次渲染共用 state、或按索引而非按 `name` 取行）只会让其中一侧变红。
 *
 * 为什么按 `name` 取行而不是按位置：`BigThree.tsx:17-19` 用
 * `planets.find(name === 'Sun')` / `'Moon'` 与 `axes.find(name === 'ASC')`，夹具里两造的
 * 十曜顺序相同，按索引取在真盘上「碰巧对」，遇到后端换序就会静默错行——把度数逐字对上卡面，
 * 这条也一并钉住。
 *
 * RTL 陷阱（本仓库第一套 .tsx 测，实录一次以免后人重踩）：`render()` 返回的那组查询绑定的是
 * `baseElement`（默认 `document.body`）而**不是** `view.container`，所以同一个 `it` 里连挂
 * 两次时 `viewA.getByText(...)` 会同时看见乙的 DOM。跨渲染的对拍一律走
 * `within(view.container)`，否则负向断言是假的。
 *
 * 复测口径（2026-09-27 全绿，2 项）：
 *   cd frontend && npx vitest run tests/components/western/BigThree.test.tsx
 */
import { cleanup, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { BigThree } from '../../../src/components/western/BigThree';
import type { SynastryChart } from '../../../src/types/synastry';
import type { AxisPoint, PlanetPlacement, WesternChart } from '../../../src/types/western';
import { readFixture } from '../../lib/readFixture';

const synastry = readFixture('synastry') as SynastryChart;

afterEach(cleanup);

/** 把查询收窄到这一次渲染的子树（见上面的 RTL 陷阱）。 */
function scopeOf(view: ReturnType<typeof render>): ReturnType<typeof within> {
  return within(view.container);
}

/** 三巨头的一张卡：eyebrow 串（如 `太阳 ☉ SUN`）所在 span 的父元素即卡片。 */
function cardFor(scope: ReturnType<typeof within>, eyebrow: string): HTMLElement {
  return scope.getByText(eyebrow).parentElement as HTMLElement;
}

/** 一造的日 / 月 / 升三行——与组件内部同一套按 name 的取法。 */
function trinity(chart: WesternChart): Array<{ eyebrow: string; body: PlanetPlacement | AxisPoint }> {
  const sun = chart.planets.filter((planet) => planet.name === 'Sun')[0];
  const moon = chart.planets.filter((planet) => planet.name === 'Moon')[0];
  const asc = chart.axes.filter((axis) => axis.name === 'ASC')[0];
  expect(sun).toBeDefined();
  expect(moon).toBeDefined();
  expect(asc).toBeDefined();
  return [
    { eyebrow: '太阳 ☉ SUN', body: sun },
    { eyebrow: '月亮 ☽ MOON', body: moon },
    { eyebrow: '上升 ASC', body: asc },
  ];
}

describe('BigThree 的取行与两造互斥（Task 8B 判据 5）', () => {
  it('日 / 月 / 升三张卡逐卡对座名、英文名、度数与宫位，全部取自响应字段', () => {
    const view = render(<BigThree planets={synastry.person_a.planets} axes={synastry.person_a.axes} />);
    const scope = scopeOf(view);
    trinity(synastry.person_a).forEach(({ eyebrow, body }) => {
      const card = cardFor(scope, eyebrow);
      expect(within(card).getByText(body.sign_zh)).toBeInTheDocument();
      expect(within(card).getByText(body.sign)).toBeInTheDocument();
      expect(within(card).getByText(body.degree_text)).toBeInTheDocument();
      expect(within(card).getByText(`第 ${body.house} 宫`)).toBeInTheDocument();
    });
  });

  it('甲乙各灌一份：甲的三个度数在乙的渲染里查不到，反之亦然（座名集合本身互斥）', () => {
    const scopeA = scopeOf(render(<BigThree planets={synastry.person_a.planets} axes={synastry.person_a.axes} />));
    const scopeB = scopeOf(render(<BigThree planets={synastry.person_b.planets} axes={synastry.person_b.axes} />));
    const cardsA = trinity(synastry.person_a);
    const cardsB = trinity(synastry.person_b);
    const rowsA = cardsA.map(({ body }) => body);
    const rowsB = cardsB.map(({ body }) => body);

    // 负向断言的前提：两造这六个字段值互不相同，否则「查不到」毫无意义。
    const signsA = rowsA.map((row) => row.sign_zh);
    const signsB = rowsB.map((row) => row.sign_zh);
    expect(signsA).toHaveLength(3);
    expect(signsB).toHaveLength(3);
    expect(signsA.filter((sign) => signsB.includes(sign))).toEqual([]);
    const degreesA = rowsA.map((row) => row.degree_text);
    const degreesB = rowsB.map((row) => row.degree_text);
    expect(degreesA.filter((text) => degreesB.includes(text))).toEqual([]);

    rowsB.forEach((row) => {
      expect(scopeA.queryByText(row.degree_text)).toBeNull();
      expect(scopeA.queryByText(row.sign_zh)).toBeNull();
    });
    rowsA.forEach((row) => {
      expect(scopeB.queryByText(row.degree_text)).toBeNull();
      expect(scopeB.queryByText(row.sign_zh)).toBeNull();
    });
    // 各自的三张卡确实各自在场（排除「两侧都空所以互斥成立」这种假通过）。
    cardsA.forEach(({ eyebrow, body }) => {
      expect(within(cardFor(scopeA, eyebrow)).getByText(body.degree_text)).toBeInTheDocument();
    });
    cardsB.forEach(({ eyebrow, body }) => {
      expect(within(cardFor(scopeB, eyebrow)).getByText(body.degree_text)).toBeInTheDocument();
    });
  });
});
