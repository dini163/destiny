import { RuneStone } from './RuneStone';
import type { DrawnRune, RuneSpreadId } from '../../types/runes';

interface RuneStoneGridProps {
  /** 本次是哪一种牌阵：决定摆位。 */
  spreadId: RuneSpreadId;
  /** 按牌阵位次序的那几枚。 */
  stones: DrawnRune[];
  /** 逆位判据全文，碑阵底下印一次。 */
  reversibleNote: string;
}

/**
 * 五石十字的格位：`position_key` → 3×3 网格里的那一格。
 *
 * 后端下发的次序是「中心、左、右、下、上」（读法次序：先看核心，再看四面），而十字要的是
 * 「上、左、中、右、下」的**视觉**次序，两者不同，故必须显式摆位而不是顺着数组画。
 *
 * 这份映射是版式，不是内容 —— 它不新增任何主张，只决定哪一块碑画在哪一格。但它确实认得
 * 语料里那五个 `position_key`，于是有漂移风险：语料改了键名，这里会静默摆不出十字。
 * 故下面 `crossCells` 先验一遍五个键认不认得，认不全就退回纵排 —— 退化的版式仍然把五块碑
 * 全画出来，好过画一个缺了一格的十字让人以为「这一阵本来只有四枚」。
 */
const CROSS_CELLS: Record<string, string> = {
  above: 'sm:col-start-2 sm:row-start-1',
  left: 'sm:col-start-1 sm:row-start-2',
  center: 'sm:col-start-2 sm:row-start-2',
  right: 'sm:col-start-3 sm:row-start-2',
  below: 'sm:col-start-2 sm:row-start-3',
};

function crossCells(stones: DrawnRune[]): Record<string, string> | null {
  const known = stones.every((stone) => stone.position_key in CROSS_CELLS);
  return known ? CROSS_CELLS : null;
}

/**
 * 铸石坛：按牌阵摆碑（spec §8、plan T7 Step 2）。
 *
 * 三石横排、五石十字、单枚居中；窄屏一律降级为纵排（`grid-cols-1` 起，十字的格位只在
 * `sm:` 以上生效）。碑阵背后那圈圣几何是纯装饰：`aria-hidden`、`pointer-events-none`，
 * 不含任何数据主张 —— 设计稿那个「24 Ray Axes」的注释只画了四条线，本页连这个数都不提。
 *
 * 碑阵底下印一次 `reversible_note`。它是「对称符为什么没有逆位」的判据全文（约两百字），
 * 逐块碑印一遍会把卡面压垮，只印在石碑卡上又太短说不清；而判据说的正是眼前这一片碑 ——
 * 转了 180° 的那几块与没转的那几块，读者当场就能对着核。
 */
export function RuneStoneGrid({ spreadId, stones, reversibleNote }: RuneStoneGridProps) {
  const cells = spreadId === 'five' ? crossCells(stones) : null;

  const layout =
    spreadId === 'five'
      ? cells === null
        ? // 认不全五个位次键：不猜十字，退回单列纵排（五块碑一块不少）。
          'grid grid-cols-1 gap-4'
        : 'grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-5'
      : spreadId === 'three'
        ? 'grid grid-cols-1 gap-4 lg:grid-cols-3 lg:gap-5'
        : 'flex flex-col items-center gap-4';

  return (
    <div className="relative">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.07]"
      >
        <svg
          viewBox="0 0 800 800"
          className="h-[520px] w-[520px] text-gold"
          fill="none"
          stroke="currentColor"
          strokeWidth={1}
        >
          <circle cx="400" cy="400" r="380" strokeDasharray="4 8" strokeOpacity="0.5" />
          <circle cx="400" cy="400" r="320" strokeOpacity="0.7" strokeWidth={1.5} />
          <circle cx="400" cy="400" r="260" strokeOpacity="0.35" strokeWidth="0.8" />
          <circle cx="400" cy="400" r="180" strokeDasharray="2 4" strokeOpacity="0.5" />
          <path d="M400 20 L400 780 M20 400 L780 400 M131 131 L669 669 M131 669 L669 131" strokeOpacity="0.3" strokeWidth="0.75" />
          <polygon points="400,80 677,240 677,560 400,720 123,560 123,240" strokeOpacity="0.25" strokeWidth="0.75" />
          <polygon points="400,140 625,270 625,530 400,660 175,530 175,270" strokeOpacity="0.25" strokeWidth="0.75" />
          <circle cx="400" cy="400" r="40" strokeOpacity="0.8" strokeWidth={1.5} />
          <path d="M380 400 L420 400 M400 380 L400 420" strokeOpacity="0.8" strokeWidth={1.5} />
        </svg>
      </div>

      <div className={`relative py-2 ${layout}`}>
        {stones.map((stone) => (
          <div
            key={stone.position_key}
            className={cells === null ? 'w-full sm:max-w-sm' : `w-full sm:max-w-sm ${cells[stone.position_key] ?? ''}`}
          >
            <RuneStone stone={stone} />
          </div>
        ))}
      </div>

      <p className="relative mt-4 rounded-element border border-rim bg-[var(--field-bg)] p-3 text-xs leading-relaxed text-ink-muted">
        <span className="label-caps mr-1.5 text-gold-soft">逆位判据</span>
        {reversibleNote}
      </p>
    </div>
  );
}
