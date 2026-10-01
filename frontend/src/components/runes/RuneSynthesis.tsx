import { ResultCard } from '../ui/ResultCard';
import type { AettCount } from '../../types/runes';

interface RuneSynthesisProps {
  /** 后端串接好的综合直读全文。 */
  synthesis: string;
  /** 四行组别配比：三组加空白符桶。`count` 为 0 的行也在里面。 */
  aettBalance: AettCount[];
}

/**
 * 综合直读 + 组别配比（spec §8、plan T7 Step 4）。
 *
 * **只保留 ætt 配比那一格**（决策 16）。设计稿在这一排还画了「元素协同性」与「决断时机
 * 窗口」两格，两格都不渲染：那三套元素归属彼此矛盾（决策 6），春分窗口也无从推导 ——
 * 本页不吃出生时间与地点，没有任何输入能推出一个日期（决策 10）。少画两格不是偷工，
 * 是那两格里没有一句能核的话。
 *
 * `synthesis` 逐字渲染：不拆句、不重排、也不在前端补一句领起。后端那一段已经把牌阵名与
 * 所问都领在最前面了（「以……铸石，所问：……」），逐枚句式的样本是「落得佩尔索（Perthro，
 * 正位）——」：中文牌名领衔、英文只待在括注里，前端再回显一次 `question` 就是把同一句
 * 话印两遍。同理不按句号切开分条 —— 那是让版式去猜内容的句子边界，猜错了没人看得出来。
 *
 * 配比四行**照后端下发的那四行画**，前端一个算术都不做（plan T6 Step 4）：`count` 直接印。
 * 前端再数一遍，就会在「后端说两枚、页面画三格」时无人能判断谁对。也因此这里**不画比例
 * 条** —— 条的长度得先除一个总数，那既是一次前端算术，又会被读成百分比，而本页一个百分比
 * 都不出（决策 7）。
 */
export function RuneSynthesis({ synthesis, aettBalance }: RuneSynthesisProps) {
  return (
    <ResultCard title="综合直读" eyebrow="SYNTHESIS" icon="compass">
      <p className="rounded-element border border-rim bg-[#0e111a] p-4 text-sm leading-loose text-ink-variant">
        {synthesis}
      </p>

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="label-caps text-gold-soft">AETTIR 组别配比</h3>
          <span className="label-caps text-ink-muted">计数，不是评分</span>
        </div>

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {aettBalance.map((row) => (
            <div
              key={row.key}
              className="flex flex-col gap-1 rounded-element border border-rim bg-surface p-3"
            >
              <span className="font-display text-sm text-ink">{row.name_zh}</span>
              <span className="label-caps text-ink-muted">{row.name}</span>
              <span className="numeric mt-1 text-2xl leading-none text-gold-bright">
                {row.count}
                <span className="ml-1 text-xs text-ink-muted">枚</span>
              </span>
            </div>
          ))}
        </div>

        <p className="text-xs leading-relaxed text-ink-muted">
          四行恒在。某一组这次一枚都没落到时，那个 0 是真实值，照样列出来 —— 少一行会让
          「没落到」与「引擎忘了算这一组」在页面上长得一样。第四行「不入三组」是空白符的
          去处：它不算三组里任何一组，可开着开关时它确实可能被抽到，那枚数总得有地方落。
        </p>
      </div>
    </ResultCard>
  );
}
