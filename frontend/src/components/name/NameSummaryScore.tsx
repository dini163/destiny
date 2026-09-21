import { ScoreLedger } from '../ui/ScoreLedger';
import type { ScoreValue } from '../../types/scoring';

/**
 * 姓名综合气象指数。
 *
 * 分数与其账本一起出现，且账本行就是五格各一行——点开即可核对每一格贡献了多少
 * （spec §6.5；权重与等级分值都署 模型参数）。算不出分时由页面整块不渲染本区，
 * 顶部的缺笔画警示已经说明了原因，这里不再重复一句"没有分"。
 */
export function NameSummaryScore({ score }: { score: ScoreValue }) {
  return <ScoreLedger score={score} label="姓名综合气象指数（五格加权）" />;
}
