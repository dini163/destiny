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
 * 失败时同样需要它，而且这一版页面上**够不着任何一条 422**：`RuneConsole` 给所问输入框上了
 * `maxLength={120}`，对齐后端 `question` 的 `max_length`，超长那条提交不出去（HTML 的 `maxLength`
 * 数的是 UTF-16 码元，pydantic 数的是码点，前者对 astral 字符更严，故不会漏放）；未知牌阵那条
 * 要绕过三选控件才踩得到，而三选只给三个字面值。于是真会走进 `error` 的是传输与服务器故障
 * （后端没起、5xx、断网）—— 那种时候留住上一次成功最要紧：读者不该因为一次网络抖动，就丢掉
 * 手里那份已经掷出来、本来好好的结果。
 */
export function useRunes() {
  return useLastSuccessMutation<RuneCastResponse, ApiError, RuneCastRequest>(fetchRuneCast);
}
