import type { BirthInputValues } from '../components/ui/InputBar';
import { ROUTES } from '../nav';
import type { Gender } from '../types/common';

/**
 * 主命盘 → 岁运推演的那一条链接。
 *
 * 两端并置一处：拼串在 `BaziNatalPage` 的大运区块，拆串在 `BaziTransitPage` 挂载时，
 * 键名一旦漂移，症状是"点进去要手填"这种没人会立刻报牌的退化，所以它们必须同生同老。
 *
 * 走查询串而不是 `location.state`：`state` 刷新即丢，而岁运的结论必须可分享、可回访
 * （spec §8）。`name` 不在其列 —— 称谓只是主命盘的回显，岁运页既不收也不显示。
 */

/** 拆开的链接：一份可直接提交的命盘输入，加上岁运页的两项本地状态。 */
export interface TransitLink {
  values: BirthInputValues;
  gender: Gender;
  applyTrueSolarTime: boolean;
}

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const TIME_PATTERN = /^\d{2}:\d{2}$/;

/**
 * 拼出 `/bazi-transit?birth_date=…&…&tst=1`。
 *
 * 空值一律不写进串里（没选城市就没有 `city`），因此链接短且可读；缺省项由
 * {@link parseTransitLink} 补成与主命盘同一口径的默认值。
 */
export function buildTransitHref(
  values: BirthInputValues,
  options: { gender: Gender; applyTrueSolarTime: boolean },
): string {
  const params = new URLSearchParams();
  const wanted: Record<string, string | number | null | undefined> = {
    birth_date: values.birth_date,
    birth_time: values.birth_time,
    calendar: values.calendar,
    city: values.city,
    latitude: values.latitude,
    longitude: values.longitude,
    gender: options.gender,
    tst: options.applyTrueSolarTime ? '1' : '0',
  };
  for (const [key, value] of Object.entries(wanted)) {
    if (value !== null && value !== undefined && value !== '') {
      params.set(key, String(value));
    }
  }
  return `${ROUTES.baziTransit}?${params.toString()}`;
}

/**
 * 把查询串还原成一次请求，任一不合格即整体返回 `null`。
 *
 * 宁可退回手填：半份来路不明的数据不该自动发出请求（spec §8）。经度是硬要求，与
 * `InputBar` 自己的 `ready` 闸同一口径 —— 只给城市名的手改链接会停在"参数不完整"，
 * 免得出现"自动提交发得出、手动提交按不动"的错位。`calendar` 与 `gender` 缺失时取
 * 默认值，值不合法才作废。
 */
export function parseTransitLink(params: URLSearchParams): TransitLink | null {
  const birthDate = params.get('birth_date');
  const birthTime = params.get('birth_time');
  if (!birthDate || !DATE_PATTERN.test(birthDate)) return null;
  if (!birthTime || !TIME_PATTERN.test(birthTime)) return null;

  const calendar = params.get('calendar');
  if (calendar !== null && calendar !== 'solar' && calendar !== 'lunar') return null;

  const gender = params.get('gender');
  if (gender !== null && gender !== 'male' && gender !== 'female') return null;

  const longitude = parseCoordinate(params.get('longitude'), 180);
  if (longitude === null) return null;

  const city = params.get('city');
  return {
    values: {
      birth_date: birthDate,
      birth_time: birthTime,
      calendar: calendar ?? 'solar',
      city: city && city.trim() !== '' ? city : null,
      latitude: parseCoordinate(params.get('latitude'), 90),
      longitude,
    },
    gender: gender ?? 'male',
    applyTrueSolarTime: params.get('tst') !== '0',
  };
}

/** 坐标：可解析且在范围内才算数，越界的经度会让服务端定不出地方。 */
function parseCoordinate(raw: string | null, limit: number): number | null {
  if (raw === null || raw.trim() === '') {
    return null;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) && Math.abs(parsed) <= limit ? parsed : null;
}
