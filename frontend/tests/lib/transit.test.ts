/**
 * `src/lib/transit.ts` 的行运口径腿：三层数据的取法、周岁印刷，以及**响应自身**的
 * 两处标量一致性（次限日期 ↔ 儒略日、太阳弧度 ↔ 度分串）。
 *
 * 为什么值得钉：行运页没有可挂载的导出组件来印这些标量（`TransitPage.tsx:236-242`、
 * `:262`、`:291-292` 三处住在页面私有组件里，整页挂载要发真实 HTTP，本轮不测——见简报
 * 「已知不可达面 ①」），页面对外只剩 `formatAgeYears` / `modeData` / `natalLongitudeByName`
 * 三支纯函数与一份响应。于是行运页能被机器核对的就剩两件事：
 * ① 三层数据各取各的、不共用一份；② 印在页眉的那几个数**互相不自相矛盾**。
 * ②的两条都只做「响应内部一致」的换算（日期差、度分进制），不重算任何推运——
 * 重算推运是后端的职责（AGENTS §6：历法/星历不自算），前端复现它反而会把两套实现
 * 的分叉洗成「测试绿、页面错」。
 *
 * 复测口径（2026-09-27 全绿，5 项）：
 *   cd frontend && npx vitest run tests/lib/transit.test.ts
 * 标量原文（改夹具就要重跑）：
 *   cd frontend && node -e "const c=require('./tests/fixtures/transit.json');console.log(c.target_date,c.natal.utc_datetime,c.natal.julian_day,c.progression.progressed_date,c.progression.progressed_julian_day,c.progression.age_years,c.solar_arc.arc_degrees,JSON.stringify(c.solar_arc.arc_text))"
 */
import { describe, expect, it } from 'vitest';

import { formatAgeYears, modeData, natalLongitudeByName } from '../../src/lib/transit';
import type { TransitChart } from '../../src/types/transit';
import { readFixture } from './readFixture';

const transit = readFixture('transit') as TransitChart;

/**
 * 把后端的度分串拆成整数。拆不动就抛错，而不是 `expect(… ).not.toBeNull()`：
 * 后者在 strict 模式下仍给 `parsed` 留 null，读代码的人得自己确认 narrowing。
 */
function parseDegreeText(text: string, label: string): { degrees: number; minutes: number } {
  const parsed = /^(\d+)°(\d{2})'$/.exec(text);
  if (parsed === null) throw new Error(`${label} 不是后端的度分串口径: ${text}`);
  return { degrees: Number(parsed[1]), minutes: Number(parsed[2]) };
}

describe('行运三层的取法（Task 8B 判据 4）', () => {
  it('modeData 把三个层各归各的数组，长度都是十，且互不是同一份数据', () => {
    const layers = (['transit', 'progression', 'solarArc'] as const).map((mode) => modeData(transit, mode));
    layers.forEach((layer) => expect(layer.positions).toHaveLength(10));
    expect(layers[0].positions).toBe(transit.transit_positions);
    expect(layers[1].positions).toBe(transit.progression.positions);
    expect(layers[2].positions).toBe(transit.solar_arc.positions);

    const keys = layers.map((layer) => layer.positions.map((point) => `${point.name}:${point.degree_text}`).join('|'));
    expect(new Set(keys).size).toBe(3);
  });

  it('每一层的相位表与本命查表对得上：moving 名在运动层里，natal 名在本命盘里', () => {
    const movingNames = new Set(transit.transit_positions.map((point) => point.name));
    expect(movingNames.size).toBe(10);
    expect(transit.transit_aspects.length).toBeGreaterThan(0);
    // 字面量条数钉：36 是录制快照 `tests/fixtures/transit.json` 的事实，夹具重录必须同步此数。
    // 复测：cd frontend && node -e "console.log(require('./tests/fixtures/transit.json').transit_aspects.length)"
    expect(transit.transit_aspects).toHaveLength(36);
    transit.transit_aspects.forEach((aspect) => expect(movingNames.has(aspect.moving)).toBe(true));

    // `natalLongitudeByName` 就是页面给相位线找终点用的那张表（10 曜 + 4 轴 = 14 项）。
    const lookup = natalLongitudeByName(transit.natal);
    expect(lookup.size).toBe(14);
    const unmatched = transit.transit_aspects
      .filter((aspect) => !lookup.has(aspect.natal))
      .map((aspect) => `${aspect.moving}→${aspect.natal}`);
    expect(unmatched, `相位指向了本命盘里没有的点: ${unmatched.join(', ')}`).toEqual([]);
    // 查表的值确实是响应给的经度，不是前端复算的。
    transit.natal.planets.forEach((planet) => expect(lookup.get(planet.name)).toBe(planet.longitude));
  });
});

describe('行运页眉的两个标量口径（Task 8B 判据 4）', () => {
  it('周岁按页面口径印成两位小数：26.7329 → 26.73（单位由页面本地化）', () => {
    expect(transit.progression.age_years).toBe(26.7329);
    expect(formatAgeYears(transit.progression.age_years)).toBe('26.73');
  });

  it('次限日期与 age_years 是同一次推进：ΔJD 等于周岁数，且该 JD 落在那个日历日', () => {
    const { natal, progression } = transit;
    expect(natal.julian_day).toBeGreaterThan(0);
    // 「一日当一年」写在响应自己身上：推进天数就是周岁数（后端各留 5 位与 4 位小数）。
    expect(Math.abs(progression.progressed_julian_day - natal.julian_day - progression.age_years)).toBeLessThan(1e-4);

    // 只把 JD 换算回日历日（不做任何星历计算）：以响应给的 UTC 生时为锚点。
    const birthUtc = new Date(`${natal.utc_datetime.replace(' ', 'T')}:00Z`);
    expect(Number.isNaN(birthUtc.getTime()), `natal.utc_datetime 不是可解析的 "YYYY-MM-DD HH:MM"`).toBe(false);
    const landed = new Date(birthUtc.getTime() + (progression.progressed_julian_day - natal.julian_day) * 86400000);
    // 本锚点在正午生时夹具（natal.utc_datetime = "2000-01-01 12:00"）下无日界风险：落点距当日
    // 两端各留半天，精确比字符串是安全的。换用近午夜生时的夹具时必须改为 ±1 日容差，否则会
    // 被时区/推进小数位造成的日界抖动误报成推运错。
    // 复测：cd frontend && node -e "console.log(require('./tests/fixtures/transit.json').natal.utc_datetime)"
    expect(landed.toISOString().slice(0, 10)).toBe(progression.progressed_date);
  });

  it('太阳弧的两种印刷同值：27°13′ 与 27.2233 在两位小数口径下都是 27.22', () => {
    const { arc_degrees, arc_text } = transit.solar_arc;
    const { degrees, minutes } = parseDegreeText(arc_text, 'solar_arc.arc_text');
    const decimal = degrees + minutes / 60;
    // 一分 = 1/60°：两个读数之差必须小于一半分度，否则页面上下两行讲的是两个数。
    expect(Math.abs(decimal - arc_degrees)).toBeLessThan(0.5 / 60);
    expect(arc_degrees.toFixed(2)).toBe(decimal.toFixed(2));
  });
});
