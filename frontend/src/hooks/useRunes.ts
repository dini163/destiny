import { fetchRuneCast } from '../api/runes';
import type { ApiError } from '../api/client';
import type { RuneCastRequest, RuneCastResponse } from '../types/runes';
import { useLastSuccessMutation } from './useLastSuccessMutation';

/**
 * 掷一次北欧卢恩。
 *
 * 两层理由，各自有先例，别混成一句：
 *
 * **是 mutation、不是按 key 复用的 query** —— 与 `useTarotSpread`、`useZhouyiCast` 同源。
 * 抽石走后端 `secrets`（OS 熵源 CSPRNG），同一份入参两次调用给出两批不同的石，故它只能
 * 在读者要它的时候真去跑一次；缓存命中或自动重放都等于把上一批石冒充成这一次的天意。
 *
 * **留住上一次成功** —— 与 `useBaziHehun`、`useNumerology` 同源。裸 `useMutation` 在
 * `pending` 与 `error` 两个 action 里都把 `data` 清成 `undefined`，而本页整份结果
 * （石阵、综合直读、ætt 配比、阴影参照、全典抽屉）都出自同一个响应，于是清一次就是整屏
 * 卸载、等响应回来再整屏挂回去。控制台上每一项改的都是下一次铸石的入参 —— 换牌阵换的是
 * 位次与抽几枚，开空白符把牌组从 24 变成 25，关逆位让所有石恒正位，改所问换掉直读的
 * 领起句 —— 也就是说任何一项都会换掉整批石。在途那一下读者该看见的，是上一批石还在
 * 屏上，而不是白板。
 *
 * 失败时同样需要它。这个端点两条 422 路径里，页面上真够得着的是 `question` 超过 120 字
 * （回 pydantic 的 `detail`）；未知牌阵那条（回统一的 `unsupported_method`）得绕过三选
 * 控件才踩得到。但两条的改正动作一样：改输入、再掷 —— 而改正时参照物最好还在眼前，
 * 这正是纯中文名吃 `numerology_no_latin_letters` 时留住上一份盘的同一条道理。
 */
export function useRunes() {
  return useLastSuccessMutation<RuneCastResponse, ApiError, RuneCastRequest>(fetchRuneCast);
}
