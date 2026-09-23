import type { BirthInputValues } from '../components/ui/InputBar';
import { ROUTES } from '../nav';
import type { HehunSide } from '../types/baziHehun';
import type { Gender } from '../types/common';

/**
 * 岁运、流日、流时与合婚这四条下钻链接。
 *
 * 两端并置一处：拼串在 `BaziNatalPage` 的大运区块、`BaziTransitPage` 的月卡、
 * `BaziLiuriPage` 的聚焦卡与 `BaziLiushiPage` 的页头（后一条是上钻），拆串在
 * `BaziTransitPage`、`BaziLiuriPage` 与 `BaziLiushiPage` 挂载时，键名一旦漂移，症状是
 * "点进去要手填"这种没人会立刻报牌的退化，所以它们必须同生同老。
 *
 * 走查询串而不是 `location.state`：`state` 刷新即丢，而推演的结论必须可分享、可回访
 * （spec §8）。`name` 只在合婚这一节进串（`m_name` / `f_name`）—— 称谓在前三页只是主命盘
 * 的回显，那些页既不收也不显示；而合婚是两造各自填的，它进请求，因此也进"URL 是唯一
 * 状态源"这条纪律。
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

// ---------------------------------------------------------------- 合婚（双人）

/** 一造的链接半份：一份可直接提交的命盘输入 + 该造自己的校正开关 + 称谓。 */
export interface HehunSideLink {
  values: BirthInputValues;
  /** 各造一份，不共用（spec §5.1）—— 所以它挂在这一半上，不在整条链接上。 */
  applyTrueSolarTime: boolean;
  /**
   * 称谓。它不进计算，但它是请求状态，而本页的纪律是"URL 是唯一状态源"，
   * 所以它跟着进串（`m_name` / `f_name`）。§8 的示例串没列它，计划记为有意补全。
   */
  name: string | null;
}

/** 两半，任一半可为空：只带 `m_*` 的预填链接是合法状态，不是残缺。 */
export interface HehunSides {
  male: HehunSideLink | null;
  female: HehunSideLink | null;
}

/** 合婚链接：两半 + 轴的那两个整数（`axis_start` / `axis_years`）。 */
export interface HehunLink extends HehunSides {
  axisStartYear: number | null;
  axisYears: number | null;
}

/**
 * 两半的键前缀。
 *
 * 用 `m_` / `f_` 而不是把 `gender` 写进串里当第 8 个键：一造一份参数表，两造共用一个
 * `gender` 键会自相矛盾，而前缀让"这一半是谁"在地址栏里就说得清。
 */
const SIDE_PREFIX: Record<HehunSide, string> = { male: 'm_', female: 'f_' };

/** 轴长 1–30，与后端 `Field(ge=1, le=30)` 同一取值面。 */
const AXIS_YEARS_PATTERN = /^([1-9]|[12][0-9]|30)$/;

/** 称谓长度上限，与后端 `HehunProfile.name` 的 `max_length` 同一条。 */
const NAME_LIMIT = 40;

/**
 * 一造 → 带前缀的参数表。
 *
 * 生辰那半段整块走 {@link birthParams}（它多写一个 `gender`，这里删掉 —— 造向由前缀
 * 承载），于是四个推演页的字段清单只有一处。前缀是最后才加上去的，因为
 * `birthParams` 不认识前缀，两处各拼一半就会有两处能漂移。
 */
function sideParams(side: HehunSide, link: HehunSideLink): URLSearchParams {
  const params = birthParams(link.values, {
    gender: side,
    applyTrueSolarTime: link.applyTrueSolarTime,
  });
  params.delete('gender');
  if (link.name) {
    params.set('name', link.name);
  }
  const prefixed = new URLSearchParams();
  for (const [key, value] of params) {
    prefixed.set(`${SIDE_PREFIX[side]}${key}`, value);
  }
  return prefixed;
}

/**
 * 去前缀后整块交给 {@link parseTransitLink}，再补称谓。
 *
 * 一半作废不牵动另一半：预填链接本来就只有一张盘（`以此造合婚` 那一条）。`name` 的
 * 长度校验放在这里而不是 `parseTransitLink` 里，因为那一半只管生辰，多一个键就多一处
 * 它替别人做的决定。空串按"没给"处理（拼串时不写，手改留空也不拦）。
 */
function parseHehunSide(params: URLSearchParams, side: HehunSide): HehunSideLink | null {
  const prefix = SIDE_PREFIX[side];
  const bare = new URLSearchParams();
  for (const [key, value] of params) {
    if (key.startsWith(prefix)) {
      bare.set(key.slice(prefix.length), value);
    }
  }
  if ([...bare.keys()].length === 0) {
    return null;
  }
  const natal = parseTransitLink(bare);
  if (natal === null) {
    return null;
  }
  const name = bare.get('name');
  if (name !== null && name.length > NAME_LIMIT) {
    return null;
  }
  return {
    values: natal.values,
    applyTrueSolarTime: natal.applyTrueSolarTime,
    name: name && name !== '' ? name : null,
  };
}

/**
 * 两半 + 轴 → `URLSearchParams` 串（不含路径）。
 *
 * 与 {@link buildHehunHref} 分开是为了页面能把同一份参数写回地址栏（`setSearchParams`
 * 要的是串），与流时那条同一个理由。`null` 一律不写进串：缺省轴在 URL 上不留痕，
 * 于是"跟着参考日的默认轴"与直接进页面完全同形。
 */
export function buildHehunQuery(
  sides: HehunSides,
  options: { axisStartYear: number | null; axisYears: number | null },
): string {
  const merged = new URLSearchParams();
  for (const side of ['male', 'female'] as const) {
    const link = sides[side];
    if (!link) {
      continue;
    }
    for (const [key, value] of sideParams(side, link)) {
      merged.set(key, value);
    }
  }
  if (options.axisStartYear !== null) {
    merged.set('axis_start', String(options.axisStartYear));
  }
  if (options.axisYears !== null) {
    merged.set('axis_years', String(options.axisYears));
  }
  return merged.toString();
}

/** 拼出 `/bazi-hehun?m_birth_date=…&f_birth_date=…&axis_years=21`。 */
export function buildHehunHref(
  sides: HehunSides,
  options: { axisStartYear: number | null; axisYears: number | null },
): string {
  return `${ROUTES.baziHehun}?${buildHehunQuery(sides, options)}`;
}

/**
 * 主命盘页「以此造合婚」的落点：只带这一造的半份参数。
 *
 * 另一造留空等输入 —— 合婚没有"父盘"可以整体下钻（决策 10）。落在这一页时不自动提交
 * （{@link parseHehunLink} 的两半只有一张盘），也不显示"链接不完整"，因为这是**预填**
 * 而不是残缺。§8 说的是"预填乾造那一半"，这里按该命盘的造向取一侧：坤造命盘预填坤，
 * 同一条理由不需要第二个入口（计划记为一般化）。
 */
export function buildHehunPrefillHref(
  values: BirthInputValues,
  options: { side: HehunSide; applyTrueSolarTime: boolean; name: string | null },
): string {
  const link: HehunSideLink = {
    values,
    applyTrueSolarTime: options.applyTrueSolarTime,
    name: options.name,
  };
  const sides: HehunSides = {
    male: options.side === 'male' ? link : null,
    female: options.side === 'female' ? link : null,
  };
  return buildHehunHref(sides, { axisStartYear: null, axisYears: null });
}

/**
 * 解合婚链接。
 *
 * 三个落点，都从这一次判断里出来：① 两半皆废（或纯空串）→ `null`，页面显示"参数不完整"
 * 并等手填；② 只有一半成形 → 非 `null`，页面预填那一半、**不**自动提交、**不**报不完整
 * （这是 `以此造合婚` 的正常落点）；③ 两半俱在 → 自动提交一次。轴的两个键与日期同一条
 * 纪律：给了就必须合形，不合形整条作废 —— 一个 `axis_years=31` 换来的 pydantic 422 会
 * 盖住"这半份生辰本来就补不全"这件更该先说的事。
 */
export function parseHehunLink(params: URLSearchParams): HehunLink | null {
  const rawStart = params.get('axis_start');
  if (rawStart !== null && !YEAR_PATTERN.test(rawStart)) {
    return null;
  }
  const rawYears = params.get('axis_years');
  if (rawYears !== null && !AXIS_YEARS_PATTERN.test(rawYears)) {
    return null;
  }
  const male = parseHehunSide(params, 'male');
  const female = parseHehunSide(params, 'female');
  if (male === null && female === null) {
    return null;
  }
  return {
    male,
    female,
    axisStartYear: rawStart === null ? null : Number(rawStart),
    axisYears: rawYears === null ? null : Number(rawYears),
  };
}
