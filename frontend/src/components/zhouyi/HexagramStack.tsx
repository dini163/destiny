import type { HexagramInfo, ZhouyiLine } from '../../types/zhouyi';
import { wuxingText } from '../../lib/wuxing';
import { lineValueMeta, liushenColor } from '../../lib/zhouyi';
import { Icon } from '../ui/Icon';
import { LineBar } from './LineBar';

interface HexagramStackProps {
  /** 本卦 — the primary hexagram (identity for the column header). */
  ben: HexagramInfo;
  /** 变卦 — after moving lines change; null when every line is static. */
  bian: HexagramInfo | null;
  /** The six dressed lines of the primary hexagram, bottom-to-top. */
  lines: ZhouyiLine[];
}

/**
 * Shared column grid for the header captions and every najia row, so the 六神 /
 * 爻题 / 纳甲 / 六亲 / 本卦 / 世应 / 变卦 columns line up down the matrix.
 */
const MATRIX_GRID =
  'grid grid-cols-[3.5rem_2.75rem_4.5rem_2.75rem_minmax(4.5rem,1fr)_3.25rem_minmax(4.5rem,1fr)] items-center gap-x-2';

/** The six rows displayed top (上爻) to bottom (初爻). */
const TOP_DOWN = [6, 5, 4, 3, 2, 1] as const;

/**
 * The najia matrix (纳甲六亲盘) — the analytical centrepiece of a Liuyao reading.
 *
 * Each row is one dressed line of the primary hexagram rendered top-to-bottom in
 * the classical orientation, carrying the real engine fields only: 六神 (coloured
 * by spirit), 爻题, 纳甲干支 + 五行 (coloured by element), 六亲, the yao bar with
 * its ○/× moving marker, the 世/应/动 badges, and — aligned beside it — the
 * corresponding line of the 变卦. The mockup's invented 用神/伏神/神煞/旺衰
 * annotations are omitted because the engine does not compute them (no-mock rule).
 */
export function HexagramStack({ ben, bian, lines }: HexagramStackProps) {
  const byPosition = new Map(lines.map((line) => [line.position, line]));
  const movingCount = lines.filter((line) => line.moving).length;

  return (
    <div className="flex flex-col gap-3">
      <TransformStrip ben={ben} bian={bian} movingCount={movingCount} />

      <div className="overflow-x-auto">
        <div className="flex min-w-[620px] flex-col gap-1">
          <div className={`${MATRIX_GRID} px-2 pb-0.5`}>
            <span className="label-caps">六神</span>
            <span className="label-caps">爻题</span>
            <span className="label-caps">纳甲</span>
            <span className="label-caps">六亲</span>
            <span className="label-caps text-center">本卦</span>
            <span className="label-caps text-center">世应</span>
            <span className="label-caps text-center">{bian ? '变卦' : '无变'}</span>
          </div>

          {TOP_DOWN.map((position) => {
            const line = byPosition.get(position);
            if (!line) {
              return null;
            }
            return <NajiaRow key={position} line={line} bian={bian} />;
          })}
        </div>
      </div>

      <Legend />
    </div>
  );
}

/** One najia row: the full dressing of a single line beside its changed form. */
function NajiaRow({ line, bian }: { line: ZhouyiLine; bian: HexagramInfo | null }) {
  const meta = lineValueMeta(line.value);
  const yang = line.yin_yang === 'yang';
  const benBar = line.moving ? 'bg-gold-bright' : 'bg-ink-muted';
  const spiritColor = liushenColor(line.liushen);
  const bianBit = bian ? bian.lines[line.position - 1] : null;
  const bianBar = line.moving ? 'bg-gold-soft' : 'bg-gold-muted/60';

  const rowTone = line.moving
    ? 'bg-gold/10 ring-1 ring-inset ring-gold/25'
    : 'bg-[#0e111a]/60 hover:bg-surface-raised';

  return (
    <div className={`${MATRIX_GRID} rounded-element px-2 py-1.5 transition-colors ${rowTone}`}>
      {/* 六神 */}
      <span className="inline-flex items-center gap-1 rounded-element bg-surface px-1.5 py-0.5 text-[11px] font-medium">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: spiritColor }} />
        <span style={{ color: spiritColor }}>{line.liushen}</span>
      </span>

      {/* 爻题 */}
      <span
        className={`font-display text-sm ${line.moving ? 'font-semibold text-gold-bright' : 'text-ink-variant'}`}
      >
        {line.yao_name}
      </span>

      {/* 纳甲干支 + 五行 */}
      <span className={`numeric text-xs ${wuxingText(line.branch_element)}`}>
        {line.stem}
        {line.branch}
        {line.branch_element}
      </span>

      {/* 六亲 */}
      <span className={`text-xs ${line.moving ? 'font-medium text-gold-soft' : 'text-ink-variant'}`}>
        {line.liuqin}
      </span>

      {/* 本卦 yao bar */}
      <LineBar yang={yang} barClass={benBar} glow={line.moving} mark={meta.mark} />

      {/* 世 / 应 / 动 badges */}
      <span className="flex flex-wrap items-center justify-center gap-1">
        {line.is_shi ? (
          <span className="rounded bg-gold/20 px-1 py-0.5 text-[10px] font-bold text-gold-bright">世</span>
        ) : null}
        {line.is_ying ? (
          <span className="rounded bg-astral/20 px-1 py-0.5 text-[10px] font-bold text-astral">应</span>
        ) : null}
        {line.moving ? (
          <span className="rounded bg-wuxing-fire/20 px-1 py-0.5 text-[10px] font-bold text-wuxing-fire">动</span>
        ) : null}
      </span>

      {/* 变卦 yao bar (or a quiet placeholder when nothing moves) */}
      {bianBit != null ? (
        <LineBar yang={bianBit === 1} barClass={bianBar} />
      ) : (
        <span className="flex h-2.5 items-center text-center text-[11px] text-ink-muted">—</span>
      )}
    </div>
  );
}

/** The ben → bian headline that crowns the matrix. */
function TransformStrip({
  ben,
  bian,
  movingCount,
}: {
  ben: HexagramInfo;
  bian: HexagramInfo | null;
  movingCount: number;
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-3 rounded-element border border-rim-soft bg-surface px-3 py-2.5">
      <HexLabel hexagram={ben} caption="本卦" strong />
      <div className="flex items-center gap-1.5">
        <Icon name="arrowRight" size={18} className="text-gold" />
        <span className="label-caps whitespace-nowrap">{movingCount} 爻动</span>
      </div>
      {bian ? (
        <HexLabel hexagram={bian} caption="变卦" />
      ) : (
        <span className="font-display text-sm text-ink-muted">六爻安静 · 无变卦</span>
      )}
    </div>
  );
}

/** A hexagram identity chip: big Unicode glyph + name + King Wen number. */
function HexLabel({
  hexagram,
  caption,
  strong,
}: {
  hexagram: HexagramInfo;
  caption: string;
  strong?: boolean;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <span
        className={`font-display text-3xl leading-none ${strong ? 'text-gold-bright text-glow-gold' : 'text-gold'}`}
      >
        {hexagram.symbol}
      </span>
      <div className="flex flex-col">
        <span className="label-caps">{caption}</span>
        <span className={`font-display text-base ${strong ? 'font-semibold text-ink' : 'text-ink-variant'}`}>
          {hexagram.full_name_zh}
        </span>
        <span className="numeric text-[11px] text-ink-muted">第 {hexagram.number} 卦</span>
      </div>
    </div>
  );
}

/** Marker + colour key so the matrix reads without guesswork. */
function Legend() {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 rounded-element border border-rim-soft bg-surface px-3 py-2 text-[11px] text-ink-muted">
      <span className="flex items-center gap-1.5">
        <span className="font-numeric font-bold text-gold-bright">○</span> 老阳动爻（九）
      </span>
      <span className="flex items-center gap-1.5">
        <span className="font-numeric font-bold text-gold-bright">×</span> 老阴动爻（六）
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-6 rounded-full bg-ink-muted" /> 本卦静爻
      </span>
      <span className="flex items-center gap-1.5">
        <span className="h-2 w-6 rounded-full bg-gold-soft" /> 变卦动化
      </span>
      <span className="flex items-center gap-1.5">
        <span className="rounded bg-gold/20 px-1 font-bold text-gold-bright">世</span>
        <span className="rounded bg-astral/20 px-1 font-bold text-astral">应</span> 世应爻
      </span>
    </div>
  );
}
