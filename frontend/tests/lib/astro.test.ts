/**
 * `src/lib/astro.ts` 里两条纯函数腿：座内度数的显示口径（`formatDegreeInSign`）与
 * 命盘轮的几何（`wheelAngle`）。
 *
 * 为什么值得钉：西洋三页的全部信任都压在「前端不复算天文，只复算显示口径」这句话上。
 * 后端（`app/engines/western.py`）给出 `longitude` 与 `degree_text` 两份口径，页面平日
 * 只印后者；唯一的例外是北/南交点——响应只给经度（`NodeInfo` 没有 `degree_text`），
 * `PlanetTable.tsx:50`、`:61` 于是必须自己格式化。那一处一旦与后端分叉，页面就会印出
 * 一个星历上根本不存在的角度，而对拍测不到（同一行旁边的 `sign_zh` 仍是后端给的）。
 * 把「逐字相等」钉成可复测的断言，就是在钉这条链条。
 *
 * 入参说明：本文件的算术入参（29.9917、-0.5 之类）不是伪造的后端响应，AGENTS §9 的
 * 先例是 `tests/lib/smoke.test.ts` 直接写 `HehunSides` 字面量；响应数据一律来自
 * `tests/fixtures/`。
 *
 * 复测口径（2026-09-27 全绿，10 项）：
 *   cd frontend && npx vitest run tests/lib/astro.test.ts
 * 行数（26/58/78）的来路，数字改一次就要重跑一次：
 *   cd frontend && node -e "const f=require('fs'),r=(n)=>JSON.parse(f.readFileSync('tests/fixtures/'+n+'.json','utf8'));const c=(o,a)=>{if(Array.isArray(o))o.forEach((v)=>c(v,a));else if(o&&typeof o==='object'){if(typeof o.degree_text==='string')a.push(o);Object.values(o).forEach((v)=>c(v,a));}return a;};for(const n of ['western-natal','transit','synastry'])console.log(n,c(r(n),[]).length)"
 */
import { describe, expect, it } from 'vitest';

import { formatDegreeInSign, wheelAngle } from '../../src/lib/astro';
import type { SynastryChart } from '../../src/types/synastry';
import type { TransitChart } from '../../src/types/transit';
import type { AxisPoint, HouseCusp, PlanetPlacement, WesternChart } from '../../src/types/western';
import { readFixture } from './readFixture';

/** 一个带经度的响应条目：`PlanetPlacement`/`AxisPoint`/`HouseCusp`/`MovingPoint`/`AnglePoint` 皆符合。 */
interface LongitudeRow {
  longitude: number;
  degree_text: string;
}

/** 一张盘的三组度数：本命盘与组合盘共用这个形状（`types/synastry.ts` 复用同一批接口）。 */
type ChartRows = Pick<WesternChart, 'planets' | 'axes' | 'houses'>;

const natal = readFixture('western-natal') as WesternChart;
const transit = readFixture('transit') as TransitChart;
const synastry = readFixture('synastry') as SynastryChart;

/** 本命盘的 26 条：10 曜 + 4 轴 + 12 宫头。 */
function chartDegreeRows(chart: ChartRows): LongitudeRow[] {
  const rows: (PlanetPlacement | AxisPoint | HouseCusp)[] = [...chart.planets, ...chart.axes, ...chart.houses];
  return rows;
}

const natalRows = chartDegreeRows(natal);
const transitNatalRows = chartDegreeRows(transit.natal);
const transitMovingRows: LongitudeRow[] = [
  ...transit.transit_positions,
  ...transit.progression.positions,
  ...transit.solar_arc.positions,
  ...transit.progression.angles,
];
const synastryRows: LongitudeRow[] = [
  ...chartDegreeRows(synastry.person_a),
  ...chartDegreeRows(synastry.person_b),
  ...chartDegreeRows(synastry.composite),
];

/** 逐字比较，并把分叉的条目原样报出来（报错行里同时看见后端串与前端串）。 */
function assertSameReading(rows: LongitudeRow[], label: string): void {
  expect(rows.length, `${label} 的条目数为 0：空集合会让下面的逐字断言白白通过`).toBeGreaterThan(0);
  const divergent = rows
    .filter((row) => formatDegreeInSign(row.longitude) !== row.degree_text)
    .map((row) => `${label} ${row.longitude} → 后端 ${row.degree_text} / 前端 ${formatDegreeInSign(row.longitude)}`);
  expect(divergent, `前端显示口径与后端 degree_text 分叉:\n${divergent.join('\n')}`).toEqual([]);
}

describe('度数链条的自制腿（Task 8B 判据 1）', () => {
  it('本命夹具的 10 曜 + 4 轴 + 12 宫头共 26 条：formatDegreeInSign 与后端 degree_text 逐字相等', () => {
    expect(natal.planets).toHaveLength(10);
    expect(natal.axes).toHaveLength(4);
    expect(natal.houses).toHaveLength(12);
    expect(natalRows).toHaveLength(26);
    assertSameReading(natalRows, 'western-natal');
  });

  it('行运夹具的 58 条（本命 26 + 三层运动点 30 + 推运轴 2）同样逐字相等', () => {
    expect(transitNatalRows).toHaveLength(26);
    expect(transit.transit_positions).toHaveLength(10);
    expect(transit.progression.positions).toHaveLength(10);
    expect(transit.solar_arc.positions).toHaveLength(10);
    expect(transit.progression.angles).toHaveLength(2);
    assertSameReading(transitNatalRows, 'transit.natal');
    assertSameReading(transitMovingRows, 'transit.moving');
  });

  it('合盘夹具的 78 条（甲乙两造各 26 + 组合盘 26）也在同一口径上', () => {
    expect(synastry.person_a.planets).toHaveLength(10);
    expect(synastry.person_b.houses).toHaveLength(12);
    expect(synastry.composite.planets).toHaveLength(10);
    expect(synastryRows).toHaveLength(78);
    assertSameReading(synastryRows, 'synastry');
  });

  it('162 个 degree_text 里没有一个走到后端的 30°00′，所以 29°60′ 至今没在页面上出现过', () => {
    // 这条为下面的 F-A1-12 定性：分叉窗口真实存在，但本次录制的三张盘没落进去——
    // 「今天没错」不等于「口径一致」，所以仍要用纯函数测钉住现状。
    // 总数 162 = 26+26+32+78，四个加数已由本文件上面三条夹具长度断言各自钉住，
    // 这里不再重复求和（修复轮 2 G3 删去 `expect(all).toHaveLength(162)` 空转断言）。
    const all = [...natalRows, ...transitNatalRows, ...transitMovingRows, ...synastryRows];
    expect(all.filter((row) => row.degree_text === "30°00'")).toEqual([]);
  });
});

describe('F-A1-12 · 前端格式化器缺 60′ 进位（Task 8B 判据 2，钉现状）', () => {
  /**
   * `src/lib/astro.ts:121` 的 docstring 逐字写着 "matching the backend's `degree_text`"，
   * 而后端 `_format_degree`（`app/engines/western.py:84-92`）在分凑满 60 时进一度
   * （`if minutes == 60: degrees += 1; minutes = 0`），前端只有 `Math.round` 而没有那条
   * 分支。座内 ≥ 29.9917°（约 30 角秒）的窗口里两边分叉：后端 `30°00'`，前端 `29°60'`
   * ——一个黄道上不存在的角度。后端那条进位已由
   * `backend/tests/golden/test_western_golden.py:245` 钉住；本条钉**前端现状**，两条同时
   * 在场，任何一方被改动就红一条。
   *
   * 将来若给 `formatDegreeInSign` 补上进位分支（findings 的处置建议），**本条要按新行为
   * 重写**，并把 `astro.ts:121` 那句过度声称一并改掉（AGENTS §8）——不要反过来把这条测
   * 改成迁就 `29°60'`。
   *
   * 复测两条（原文见 `docs/superpowers/findings/2026-09-26-fullstack-test.md` 的 F-A1-12）：
   *   cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.western import _format_degree as f;print([f(v) for v in (29.9917,29.9949,29.9999,29.985,0.0)])"
   *   cd frontend && node -e "const f=(l)=>{const w=((l%30)+30)%30,d=Math.floor(w),m=Math.round((w-d)*60);return d+'°'+String(m).padStart(2,0)+'\\''};console.log([29.9917,29.9949,29.9999,29.985,0.0].map(f))"
   */
  it('进位窗口内前端印 29°60′，正是后端进位成 30°00′ 的那三个值', () => {
    expect(formatDegreeInSign(29.9917)).toBe("29°60'");
    expect(formatDegreeInSign(29.9949)).toBe("29°60'");
    expect(formatDegreeInSign(29.9999)).toBe("29°60'");
  });

  it('窗口两侧的正常读数逐字钉住（29.985°→29°59′、0° 与整 30°→0°00′）；座内 ≥29.9917° 的进位缺失与星座序号无关，狮子 149.9917° 仍印 29°60′', () => {
    expect(formatDegreeInSign(29.985)).toBe("29°59'");
    expect(formatDegreeInSign(0)).toBe("0°00'");
    expect(formatDegreeInSign(30)).toBe("0°00'");
    // 第四例不是「窗口外」：149.9917 的座内度数正是 29.9917，落在同一个进位缺失窗口
    // （后端此处进位成 30°00′）。它钉的是缺进位这条现状不随所在星座改变。
    expect(formatDegreeInSign(149.9917)).toBe("29°60'");
  });

  it('负经度先回绕到 [0,30) 再读数（交点经度的形状保证）', () => {
    expect(formatDegreeInSign(-0.5)).toBe("29°30'");
    expect(formatDegreeInSign(-30.25)).toBe("29°45'");
  });
});

describe('命盘轮几何（Task 8B 判据 3 的纯函数腿）', () => {
  const ascendant = natal.axes.filter((axis) => axis.name === 'ASC');

  it('上升点自己映射到 180°，即 SVG 的正左方（9 点方向）', () => {
    expect(ascendant).toHaveLength(1);
    expect(wheelAngle(ascendant[0].longitude, ascendant[0].longitude)).toBe(180);
  });

  it('经度差为负时在差值上 +360 回绕，返回值刻意留在 [180,540)', () => {
    // `wheelAngle` 不归一到 [0,360)：`polarToCartesian` 走 cos/sin，530° 与 170° 是同一点。
    // 这条钉的是「回绕发生在差值上而不是结果上」——把两步写反的实现（先加 180 再回绕）
    // 会让 9 点方向以西的行星掉到对称位置，而单看任何一个返回值都发现不了。
    expect(wheelAngle(0, 350)).toBe(190);
    expect(wheelAngle(350, 0)).toBe(530);
    expect(wheelAngle(350, 0) % 360).toBe(170);
    const asc = ascendant[0].longitude;
    expect(wheelAngle(asc + 20, asc)).toBeCloseTo(200, 10);
    expect(wheelAngle(asc - 10, asc)).toBeCloseTo(530, 10);
  });

  it('十曜的 wheelAngle 互不相等，故轮上没有重合的两点（几何测的立足前提）', () => {
    const asc = ascendant[0].longitude;
    const angles = natal.planets.map((planet) => wheelAngle(planet.longitude, asc));
    expect(angles).toHaveLength(10);
    angles.forEach((angle) => {
      expect(angle).toBeGreaterThanOrEqual(180);
      expect(angle).toBeLessThan(540);
    });
    expect(new Set(angles).size).toBe(10);
  });
});
