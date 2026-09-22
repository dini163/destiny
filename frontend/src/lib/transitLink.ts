import type { BirthInputValues } from '../components/ui/InputBar';
import { ROUTES } from '../nav';
import type { Gender } from '../types/common';

/**
 * 岁运、流日与流时这三条下钻链接。
 *
 * 两端并置一处：拼串在 `BaziNatalPage` 的大运区块、`BaziTransitPage` 的月卡、
 * `BaziLiuriPage` 的聚焦卡与 `BaziLiushiPage` 的页头（后一条是上钻），拆串在
 * `BaziTransitPage`、`BaziLiuriPage` 与 `BaziLiushiPage` 挂载时，键名一旦漂移，症状是
 * "点进去要手填"这种没人会立刻报牌的退化，所以它们必须同生同老。
 *
 * 走查询串而不是 `location.state`：`state` 刷新即丢，而推演的结论必须可分享、可回访
 * （spec §8）。`name` 不在其列 —— 称谓只是主命盘的回显，三个推演页既不收也不显示。
 */

/** 拆开的链接：一份可直接提交的命盘输入，加上岁运页的两项本地状态。 */
export interface TransitLink {
  values: BirthInputValues;
  gender: Gender;
  applyTrueSolarTime: boolean;
  /**
   * 要聚焦的流年，取自流日页那一份 `result.year`（立春为界，故 2028-01-26 是 2027）。
   *
   * 只有上钻回岁运时才有值；下钻的三条链接不写这个键，`null` 即"进页按参考日开窗、
   * 不聚焦任何一年"，与直接空手进页面完全同形。
   */
  year: number | null;
}

const DATE_PATTERN = /^\d{4}-\d{2}-\d{2}$/;
const TIME_PATTERN = /^\d{2}:\d{2}$/;
/** 四位整数年，与 `schema` 那边 `start_year` 的取值面一致；区间由服务端再校一轮。 */
const YEAR_PATTERN = /^\d{4}$/;

/**
 * 拼出 `/bazi-transit?birth_date=…&…&tst=1`，上钻时再带 `&year=2027`。
 *
 * 空值一律不写进串里（没选城市就没有 `city`），因此链接短且可读；缺省项由
 * {@link parseTransitLink} 补成与主命盘同一口径的默认值。
 */
export function buildTransitHref(
  values: BirthInputValues,
  options: { gender: Gender; applyTrueSolarTime: boolean; year?: number },
): string {
  const params = birthParams(values, options);
  if (options.year !== undefined) {
    params.set('year', String(options.year));
  }
  return `${ROUTES.baziTransit}?${params.toString()}`;
}

/**
 * 生辰 + 造向 + 校正开关 → 查询参数。
 *
 * 岁运、流日与流时三条链接共用这一份，后两条只在它上面再 `set` 自己的键 —— 少一次
 * "复制粘贴字段清单"就少一处能漂移的地方。
 */
export function birthParams(
  values: BirthInputValues,
  options: { gender: Gender; applyTrueSolarTime: boolean },
): URLSearchParams {
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
  return params;
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

  // `year` 与两个日期同一条纪律：给了就必须合形，不合形整条作废退回手填。半份来路不明
  // 的年份最坏的情况是发出一条 `focus_year` 落在区间之外的请求，那记 422 会盖住全表。
  const rawYear = params.get('year');
  if (rawYear !== null && !YEAR_PATTERN.test(rawYear)) return null;

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
    year: rawYear === null ? null : Number(rawYear),
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

/** 岁运月卡 → 流日矩阵：`anchor` 定段，`focus` 可选。缺 `anchor` 时页面按参考日开窗。 */
export interface LiuriLink extends TransitLink {
  anchor: string | null;
  focus: string | null;
}

/**
 * 拼出 `/bazi-liuri?birth_date=…&…&anchor=2028-01-06`。
 *
 * 两个方向共用它：岁运月卡往下钻时只给 `anchor`（那一段的交节日，不带 `focus`），流时页
 * 往回钻时 `anchor` 与 `focus` 给同一天（回到那一日的矩阵且那一日是展开的）。
 *
 * 生辰那半段整块走 {@link buildTransitHref} 的参数表，只在其后 `set` 两个日期键 ——
 * 两条链接的字段名因此不可能各改一半。
 */
export function buildLiuriHref(
  values: BirthInputValues,
  options: { gender: Gender; applyTrueSolarTime: boolean; anchor: string; focus?: string },
): string {
  const params = birthParams(values, options);
  params.set('anchor', options.anchor);
  if (options.focus) {
    params.set('focus', options.focus);
  }
  return `${ROUTES.baziLiuri}?${params.toString()}`;
}

/**
 * 解流日链接：生辰半段整块交给 {@link parseTransitLink}，再补两个日期。
 *
 * 两个日期都是「给了就必须合形」：空 → `null`（页面按参考日开窗），不合形 → 整条链接
 * 作废退回手填。作废与生辰半段作废是同一件事，前端只需要一个落点。
 */
export function parseLiuriLink(params: URLSearchParams): LiuriLink | null {
  const natal = parseTransitLink(params);
  if (!natal) {
    return null;
  }
  const anchor = params.get('anchor');
  const focus = params.get('focus');
  if (
    (anchor !== null && !DATE_PATTERN.test(anchor)) ||
    (focus !== null && !DATE_PATTERN.test(focus))
  ) {
    return null;
  }
  return { ...natal, anchor, focus };
}

const HOUR_BRANCH_PATTERN = /^[子丑寅卯辰巳午未申酉戌亥]$/;

/** 流时页的两条本地状态：哪一天、聚焦哪一支。 */
export interface LiushiLink extends TransitLink {
  date: string | null;
  hour: string | null;
}

/**
 * 生辰 + 造向 + 校正 + 那两键 → `URLSearchParams`（不含路径）。
 *
 * 与 {@link buildLiushiHref} 分开是为了页面能把同一份参数写回查询串：`setSearchParams` 要
 * 的是串而不是整链，两处各拼一遍字段清单就能各改一半。`date` / `hour` 空值不写进串，
 * 于是"缺省落参考日"这条状态在 URL 上是不留痕的，与直接进页面完全同形。
 */
export function buildLiushiQuery(
  values: BirthInputValues,
  options: {
    gender: Gender;
    applyTrueSolarTime: boolean;
    date: string | null;
    hour: string | null;
  },
): string {
  const params = birthParams(values, options);
  if (options.date) {
    params.set('date', options.date);
  }
  if (options.hour) {
    params.set('hour', options.hour);
  }
  return params.toString();
}

/**
 * 拼出 `/bazi-liushi?birth_date=…&…&date=2028-01-26&hour=辰`。
 *
 * 第一个参数收的是 `BirthInputValues`，而调用方手上通常是整份流日请求（多带 `gender` /
 * `apply_true_solar_time` / `reference_date` / `name`）—— 直接交过去即可，多余字段无害，
 * 因为 {@link birthParams} 只挑它认识的那七个键，调用点不必先 omit 一遍。
 */
export function buildLiushiHref(
  values: BirthInputValues,
  options: {
    gender: Gender;
    applyTrueSolarTime: boolean;
    date: string | null;
    hour: string | null;
  },
): string {
  return `${ROUTES.baziLiushi}?${buildLiushiQuery(values, options)}`;
}

/**
 * 解流时链接：生辰半段整块交给 {@link parseTransitLink}，再补那两键。
 *
 * 时辰只认十二支（`HOUR_BRANCHES` 那份白名单在这里是第二遍，但它拦的是"手改的链接"，
 * 引擎那侧拦的是"发出来的请求"，两处各司其职）：`?hour=十三` 这种整条作废退回手填，
 * 而不是把坏值交给服务端换一台机器码 —— 用户看到的会是两段毫不相干的话。
 */
export function parseLiushiLink(params: URLSearchParams): LiushiLink | null {
  const natal = parseTransitLink(params);
  if (!natal) {
    return null;
  }
  const date = params.get('date');
  const hour = params.get('hour');
  if (date !== null && !DATE_PATTERN.test(date)) {
    return null;
  }
  if (hour !== null && !HOUR_BRANCH_PATTERN.test(hour)) {
    return null;
  }
  return { ...natal, date, hour };
}
