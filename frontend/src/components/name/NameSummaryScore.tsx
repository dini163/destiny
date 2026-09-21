import { ScoreLedger } from '../ui/ScoreLedger';
import type { NameAnalysis } from '../../types/name';

/**
 * 姓名综合气象指数。
 *
 * 分数与其账本一起出现，且账本行就是五格各一行——点开即可核对每一格贡献了多少
 * （spec §6.5；权重与等级分值都署 模型参数）。
 */
export function NameSummaryScore({ analysis }: { analysis: NameAnalysis }) {
  if (!analysis.score) {
    return (
      <p className="text-sm leading-relaxed text-ink-muted">
        笔画未完全核定，本次不出综合指数——缺数据时不给打折分（spec 决策八）。
      </p>
    );
  }
  return <ScoreLedger score={analysis.score} label="姓名综合气象指数（五格加权）" />;
}
