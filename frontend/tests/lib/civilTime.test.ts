/**
 * 门户授时面板的两支民事钟：`beijingTime`（术数钟面基准）与 `localClock`（访客本地钟）。
 *
 * 为什么值得钉：这类换算的失败模式是**只在某些访客机器上错**——UTC 偏移一项写错，
 * 在 UTC 机器上写、在 UTC 机器上测都不会红（本文件的前身就栽过一次，见
 * findings「七」）。所以每条断言都在多个 `process.env.TZ` 下各跑一遍。
 * 夏令时与半/刻时区是最容易错的两条路：`localClock` 的经线取**当下**偏移，
 * 纽约冬天 −75°、夏天 −60°，伦敦夏天 15°；尼泊尔 +5:45 要给 86.25°；
 * UTC+14 的莱恩群岛折算出 210°，地球上没有这条经线，只能如实说「无对应标准经线」。
 *
 * 时区名断言的是 `Intl` 的 zh-CN 长名（`中国标准时间`、`北美东部夏令时间`…），
 * 故意钉死而不是只断言非空：ICU 数据缺位时它会退回 IANA 原文
 * （`America/New_York`），那就是一行英文混在中文面板里，本测会红。
 * 复测口径（2026-09-27，10 项）：
 *   cd frontend && npx vitest run tests/lib/civilTime.test.ts
 */
import { afterEach, describe, expect, it } from 'vitest';

import { beijingTime, localClock } from '../../src/lib/civilTime';

/** 访客机器时区不影响 `beijingTime` 的输出——这是它的全部契约。 */
const BEIJING_ZONES = ['Asia/Shanghai', 'UTC', 'America/New_York', 'Asia/Kolkata'];

const ORIGINAL_TZ = process.env.TZ;

afterEach(() => {
  process.env.TZ = ORIGINAL_TZ;
});

describe('beijingTime', () => {
  it('reads the UTC+8 civil clock of an instant whatever the viewer timezone is', () => {
    for (const zone of BEIJING_ZONES) {
      process.env.TZ = zone;
      // 2026-09-27T08:42:54Z —— 北京 16:42:54，纽约凌晨 04:42，加尔各答 14:12。
      expect(beijingTime(new Date(Date.UTC(2026, 8, 27, 8, 42, 54))), zone).toEqual({
        date: '2026-09-27',
        minute: '16:42',
        clock: '16:42:54',
      });
    }
  });

  it('rolls the date forward when Beijing crosses midnight', () => {
    for (const zone of BEIJING_ZONES) {
      process.env.TZ = zone;
      // 2026-09-27T17:05:00Z 在 UTC 与纽约仍是 27 日，北京已是 28 日凌晨。
      expect(beijingTime(new Date(Date.UTC(2026, 8, 27, 17, 5, 0))), zone).toEqual({
        date: '2026-09-28',
        minute: '01:05',
        clock: '01:05:00',
      });
    }
  });
});

type LocalRow = {
  zone: string;
  instant: string;
  why: string;
  date: string;
  minute: string;
  clock: string;
  zoneLabel: string;
  offsetLabel: string;
  meridianLabel: string;
  sameAsBeijing: boolean;
};

const LOCAL_ROWS: LocalRow[] = [
  {
    zone: 'Asia/Shanghai',
    instant: '2026-01-15T16:05:00Z',
    why: '中国大陆全境一个时区，且与北京钟面重合',
    date: '2026-01-16',
    minute: '00:05',
    clock: '00:05:00',
    zoneLabel: '中国标准时间',
    offsetLabel: 'UTC+8',
    meridianLabel: '东经 120°',
    sameAsBeijing: true,
  },
  {
    zone: 'America/New_York',
    instant: '2026-01-15T16:05:00Z',
    why: '冬：标准偏移 −5 ⇒ 西经 75°',
    date: '2026-01-15',
    minute: '11:05',
    clock: '11:05:00',
    zoneLabel: '北美东部标准时间',
    offsetLabel: 'UTC−5',
    meridianLabel: '西经 75°',
    sameAsBeijing: false,
  },
  {
    zone: 'America/New_York',
    instant: '2026-07-15T16:05:00Z',
    why: '夏：夏令偏移 −4 ⇒ 西经 60°，钟面与经线必须一起走',
    date: '2026-07-15',
    minute: '12:05',
    clock: '12:05:00',
    zoneLabel: '北美东部夏令时间',
    offsetLabel: 'UTC−4',
    meridianLabel: '西经 60°',
    sameAsBeijing: false,
  },
  {
    zone: 'Europe/London',
    instant: '2026-01-15T16:05:00Z',
    why: '零偏移要给本初子午线，不是「东经 0°」',
    date: '2026-01-15',
    minute: '16:05',
    clock: '16:05:00',
    zoneLabel: '格林尼治标准时间',
    offsetLabel: 'UTC±0',
    meridianLabel: '本初子午线',
    sameAsBeijing: false,
  },
  {
    zone: 'Asia/Kolkata',
    instant: '2026-01-15T16:05:00Z',
    why: '半时区 +5:30 ⇒ 东经 82.5°',
    date: '2026-01-15',
    minute: '21:35',
    clock: '21:35:00',
    zoneLabel: '印度时间',
    offsetLabel: 'UTC+5:30',
    meridianLabel: '东经 82.5°',
    sameAsBeijing: false,
  },
  {
    zone: 'Asia/Kathmandu',
    instant: '2026-01-15T16:05:00Z',
    why: '刻时区 +5:45 ⇒ 东经 86.25°',
    date: '2026-01-15',
    minute: '21:50',
    clock: '21:50:00',
    zoneLabel: '尼泊尔时间',
    offsetLabel: 'UTC+5:45',
    meridianLabel: '东经 86.25°',
    sameAsBeijing: false,
  },
  {
    zone: 'Pacific/Kiritimati',
    instant: '2026-01-15T16:05:00Z',
    why: 'UTC+14 折出 210°，超出 ±180 只能如实说没有对应经线',
    date: '2026-01-16',
    minute: '06:05',
    clock: '06:05:00',
    zoneLabel: '莱恩群岛时间',
    offsetLabel: 'UTC+14',
    meridianLabel: '无对应标准经线',
    sameAsBeijing: false,
  },
  {
    zone: 'Asia/Singapore',
    instant: '2026-01-15T16:05:00Z',
    why: '偏移与北京相同 ⇒ 钟面读数相同，辅行该省',
    date: '2026-01-16',
    minute: '00:05',
    clock: '00:05:00',
    zoneLabel: '新加坡标准时间',
    offsetLabel: 'UTC+8',
    meridianLabel: '东经 120°',
    sameAsBeijing: true,
  },
];

describe('localClock', () => {
  it.each(LOCAL_ROWS)(
    '$zone · $instant 的钟面、偏移与标准经线（$why）',
    ({ zone, instant, date, minute, clock, zoneLabel, offsetLabel, meridianLabel, sameAsBeijing }) => {
      process.env.TZ = zone;
      expect(localClock(new Date(instant))).toEqual({
        date,
        minute,
        clock,
        zoneLabel,
        offsetLabel,
        meridianLabel,
        sameAsBeijing,
      });
    },
  );
});
