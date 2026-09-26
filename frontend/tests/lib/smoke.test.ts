import { describe, expect, it } from 'vitest';

import { buildHehunHref, parseHehunLink } from '../../src/lib/transitLink';
import type { HehunSides } from '../../src/lib/transitLink';

const SIDES: HehunSides = {
  male: {
    values: { birth_date: '2000-08-16', birth_time: '12:00', calendar: 'solar', city: '北京', latitude: 39.9042, longitude: 116.4074 },
    applyTrueSolarTime: true,
    name: '乾',
  },
  female: {
    values: { birth_date: '2000-09-08', birth_time: '20:15', calendar: 'solar', city: '上海', latitude: 31.2304, longitude: 121.4737 },
    applyTrueSolarTime: false,
    name: '坤',
  },
};

describe('测试管道', () => {
  it('合婚链接 build → parse 往返保住两造的生辰与开关（vitest 能 import src 运行代码）', () => {
    const href = buildHehunHref(SIDES, { axisStartYear: 2025, axisYears: 21 });
    const link = parseHehunLink(new URLSearchParams(href.split('?')[1]));

    expect(link).not.toBeNull();
    expect(link?.male?.values.birth_date).toBe('2000-08-16');
    expect(link?.female?.values.birth_time).toBe('20:15');
    expect(link?.male?.applyTrueSolarTime).toBe(true);
    expect(link?.female?.applyTrueSolarTime).toBe(false);
    expect(link?.axisYears).toBe(21);
  });
});
