import type { ReactNode } from 'react';

import type { HexagramInfo } from '../../types/zhouyi';
import { wuxingChip } from '../../lib/wuxing';
import { HexagramGlyph } from '../ui/HexagramGlyph';
import { PlainProse } from '../ui/PlainProse';

interface HexagramCardProps {
  /** The hexagram to describe (变卦 or 互卦). */
  hexagram: HexagramInfo;
  /** Positions (1-6) that changed from the primary hexagram — 变卦 only. */
  moving?: number[];
  /** Short factual note under the caption (e.g. how the 互卦 is derived). */
  note?: string;
}

/**
 * A structural identity card for a derived hexagram (变卦 / 互卦).
 *
 * The backend supplies these as bare `HexagramInfo` — figure, name, palace,
 * 世应 and 卦辞 — but *without* per-line najia / 六亲 / 六神 dressing (only the
 * primary hexagram is dressed). This card therefore shows exactly what is real:
 * the six-line figure, King Wen number, palace + generation, trigram natures,
 * 世应 positions, the classical 卦辞 (plus 用九/用六 for 乾/坤) and the curated
 * vernacular retelling of each — the retelling comes from `content/zhouyi_plain.py`
 * on the same `HexagramInfo`, so 变卦 and 互卦 get the same table as 本卦 and this
 * component holds no second copy of it. No 卦德 gloss, 六冲/六合 tag or 错卦/综卦
 * is invented.
 */
export function HexagramCard({ hexagram, moving, note }: HexagramCardProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-start gap-3.5">
        <HexagramGlyph
          lines={hexagram.lines}
          moving={moving}
          barClass="bg-gold-soft"
          className="w-16 shrink-0"
        />
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex items-baseline gap-2">
            <span className="font-display text-2xl leading-none text-gold">{hexagram.symbol}</span>
            <span className="font-display text-lg font-semibold text-ink">{hexagram.full_name_zh}</span>
          </div>
          <span className="text-xs text-ink-muted">
            {hexagram.name_en} · {hexagram.pinyin}
          </span>
          {note ? <span className="mt-0.5 text-[11px] leading-snug text-ink-muted">{note}</span> : null}
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        <Chip>第 {hexagram.number} 卦</Chip>
        <Chip>
          {hexagram.palace_name_zh} · {hexagram.generation}
        </Chip>
        <span
          className={`inline-flex items-center rounded-element px-2 py-0.5 text-[11px] ${wuxingChip(hexagram.palace_element)}`}
        >
          宫属{hexagram.palace_element}
        </span>
        <Chip>
          世{hexagram.shi} · 应{hexagram.ying}
        </Chip>
        <Chip>
          下{hexagram.lower_name_zh}
          {hexagram.lower_nature_zh} · 上{hexagram.upper_name_zh}
          {hexagram.upper_nature_zh}
        </Chip>
      </div>

      <div className="gold-rule" />

      <div className="flex flex-col gap-1">
        <span className="label-caps">卦辞</span>
        <PlainProse text={hexagram.plain_gua_ci} />
        <p className="font-display text-sm leading-relaxed text-ink-muted">{hexagram.gua_ci}</p>
      </div>
      {hexagram.plain_yong_ci ? (
        <div className="flex flex-col gap-1">
          <span className="label-caps text-ink-muted">{hexagram.number === 1 ? '用九' : '用六'}</span>
          <PlainProse text={hexagram.plain_yong_ci} />
          <p className="font-display text-sm leading-relaxed text-ink-muted">{hexagram.yong_ci}</p>
        </div>
      ) : null}
    </div>
  );
}

/** A small neutral metadata pill. */
function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-element border border-rim bg-[#0e111a] px-2 py-0.5 text-[11px] text-ink-variant">
      {children}
    </span>
  );
}
