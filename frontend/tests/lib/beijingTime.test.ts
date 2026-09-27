/**
 * `src/lib/beijingTime.ts` 的时区口径腿：北京时间必须只看**时刻本身**，与访客机器的
 * 时区无关。
 *
 * 为什么值得钉：门户页的「北京时间」大字此前把 UTC 当北京时间印（访客机 GMT+8 时
 * 恰好慢 8 小时），而它同时是喂 `/meta/true-solar-time` 的 `date` + `time`
 * （契约要求「标准时」，`src/api/meta.ts:13`）——错 8 小时会把真太阳时和均时差
 * 一起带到别的时刻去，午夜前后还会连日期一起错。这类 bug 在 UTC 机器上写、在 UTC
 * 机器上测都不会红，所以断言必须在多个 `TZ` 下各跑一遍。
 *
 * 复测口径（2026-09-27）：
 *   cd frontend && npx vitest run tests/lib/beijingTime.test.ts
 */
import { afterEach, describe, expect, it } from 'vitest';

import { beijingTime } from '../../src/lib/beijingTime';

/** 访客机器时区不影响输出——这是本件的全部契约。 */
const VIEWER_ZONES = ['Asia/Shanghai', 'UTC', 'America/New_York', 'Asia/Kolkata'];

const ORIGINAL_TZ = process.env.TZ;

afterEach(() => {
  process.env.TZ = ORIGINAL_TZ;
});

describe('beijingTime', () => {
  it('reads the UTC+8 civil clock of an instant whatever the viewer timezone is', () => {
    for (const zone of VIEWER_ZONES) {
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
    for (const zone of VIEWER_ZONES) {
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
