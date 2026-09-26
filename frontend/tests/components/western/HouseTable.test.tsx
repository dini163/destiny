/**
 * `HouseTable`（十二宫头）的挂载测。
 *
 * 为什么值得钉：宫头是全表最容易「串行」的一块——十二张卡片形状完全相同，度数还成对重复
 * （本命夹具 1/7 宫同为 `24°16'`、4/10 宫同为 `9°37'`、2/8 与 3/9 亦然，对宫关系使然），
 * 一旦渲染把宫号与度数配错手，逐格文本仍然都是「响应里有的串」，只有按**同一张卡**断
 * 宫号 + 星座中英 + 度数三件套才能发现。走查 Task 8 合盘节 项 6 正是这样人工核对的
 * （「第 1/7 宫同为 23°37′、第 4/10 宫同为 4°19′，与 ASC/DES·MC/IC 对宫关系自洽」）。
 *
 * 复测口径（2026-09-27 全绿，2 项）：
 *   cd frontend && npx vitest run tests/components/western/HouseTable.test.tsx
 * 重复度数的来路（本段数字的依据）：
 *   cd frontend && node -e "const c=require('./tests/fixtures/western-natal.json').houses;console.log(c.map(h=>h.house+':'+h.degree_text).join(' '))"
 */
import { cleanup, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { HouseTable } from '../../../src/components/western/HouseTable';
import type { WesternChart } from '../../../src/types/western';
import { readFixture } from '../../lib/readFixture';

const natal = readFixture('western-natal') as WesternChart;

afterEach(cleanup);

/** 一张宫卡的根节点：卡面第一行是「第 N 宫」，其父元素即这张卡。 */
function cardsOf(view: ReturnType<typeof render>): HTMLElement[] {
  const labels = view.getAllByText(/^第 \d+ 宫$/);
  return labels.map((label) => label.parentElement as HTMLElement);
}

describe('HouseTable 的透传腿（Task 8B 判据 1）', () => {
  it('十二张卡逐卡三件套：宫号、星座中英、度数同卡对得上，重复度数不串', () => {
    const view = render(<HouseTable houses={natal.houses} />);
    expect(natal.houses).toHaveLength(12);
    const cards = cardsOf(view);
    expect(cards).toHaveLength(12);

    natal.houses.forEach((cusp, index) => {
      const card = cards[index];
      expect(within(card).getByText(`第 ${cusp.house} 宫`)).toBeInTheDocument();
      expect(within(card).getByText(cusp.sign_zh)).toBeInTheDocument();
      expect(within(card).getByText(cusp.sign)).toBeInTheDocument();
      expect(within(card).getByText(cusp.degree_text)).toBeInTheDocument();
    });
  });

  it('度数按宫号顺序透传，且 1/7、4/10 这些成对重复真的存在（上一条不是靠唯一性蒙对）', () => {
    const view = render(<HouseTable houses={natal.houses} />);
    const degrees = cardsOf(view).map((card) => within(card).getByText(/^\d+°\d{2}'$/).textContent);
    expect(degrees).toEqual(natal.houses.map((cusp) => cusp.degree_text));

    const duplicated = natal.houses
      .map((cusp) => cusp.degree_text)
      .filter((text, index, all) => all.indexOf(text) !== index);
    expect(duplicated).toEqual(["24°16'", "1°08'", "22°01'", "9°37'", "29°04'", "27°42'"]);
  });
});
