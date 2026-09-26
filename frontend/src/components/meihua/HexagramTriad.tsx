import type { ReactNode } from 'react';

import type { MeihuaCast, MeihuaHexagram, MeihuaTrigram } from '../../types/meihua';
import { wuxingText } from '../../lib/wuxing';
import { HexagramGlyph } from '../zhouyi/HexagramGlyph';

interface HexagramTriadProps {
  /** The complete cast — supplies 本/互/变卦, the moving line and the 体用 roles. */
  cast: MeihuaCast;
}

/** 内卦 / 外卦 → 下卦 / 上卦. */
const POSITION_ZH: Record<string, string> = { lower: '下卦', upper: '上卦' };

/**
 * The 本卦 → 互卦 → 变卦 triptych (梅花易数 core reading).
 *
 * 本卦 is the matter as raised, 互卦 (lines 2‑3‑4 / 3‑4‑5) its middle passage and
 * 变卦 its outcome after the moving line flips. The 本卦 card carries the 体 / 用
 * role chips (which trigram is the subject vs. the object), because that pairing is
 * what drives the whole 生克 judgement. Every figure, name and trigram comes
 * straight from the engine — nothing is drawn that the backend did not compute.
 */
export function HexagramTriad({ cast }: HexagramTriadProps) {
  const { ben, hu, bian, moving_position, ti, yong } = cast;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <TriadCard
        eyebrow="本卦 · PRIMARY"
        caption="起卦所得 · 事之本体"
        hexagram={ben}
        moving={[moving_position]}
        barClass="bg-gold-soft"
        nameClass="text-gold-bright"
        roles={
          <>
            <RoleChip role="体" trigram={ti.trigram} accent />
            <RoleChip role="用" trigram={yong.trigram} />
          </>
        }
      />
      <TriadCard
        eyebrow="互卦 · NUCLEAR"
        caption="二三四·三四五爻 · 事之中段"
        hexagram={hu}
        barClass="bg-gold-muted"
        nameClass="text-ink"
      />
      <TriadCard
        eyebrow="变卦 · CHANGED"
        caption="动爻变后 · 事之归宿"
        hexagram={bian}
        moving={[moving_position]}
        barClass="bg-astral"
        nameClass="text-ink"
      />
    </div>
  );
}

interface TriadCardProps {
  eyebrow: string;
  caption: string;
  hexagram: MeihuaHexagram;
  moving?: number[];
  barClass: string;
  nameClass: string;
  roles?: ReactNode;
}

/** One hexagram column: caption, figure, name, trigram natures and optional roles. */
function TriadCard({ eyebrow, caption, hexagram, moving, barClass, nameClass, roles }: TriadCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-card border border-rim bg-surface/60 p-4">
      <div className="flex flex-col gap-0.5">
        <span className="label-caps">{eyebrow}</span>
        <span className="text-[11px] leading-snug text-ink-muted">{caption}</span>
      </div>

      <div className="flex items-start gap-3">
        <HexagramGlyph lines={hexagram.lines} moving={moving} barClass={barClass} className="w-14 shrink-0" />
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex items-baseline gap-2">
            <span className="font-display text-2xl leading-none text-gold">{hexagram.symbol}</span>
            <span className={`font-display text-base font-semibold ${nameClass}`}>{hexagram.full_name_zh}</span>
          </div>
          <span className="numeric text-[11px] text-ink-muted">第 {hexagram.number} 卦</span>
          <span className="text-[11px] leading-snug text-ink-variant">
            {hexagram.lower.name_zh}
            {hexagram.lower.nature_zh}下 · {hexagram.upper.name_zh}
            {hexagram.upper.nature_zh}上
          </span>
        </div>
      </div>

      {roles ? <div className="flex flex-wrap gap-1.5">{roles}</div> : null}
    </div>
  );
}

/** A compact 体 / 用 chip naming the trigram, its position and its 五行. */
function RoleChip({ role, trigram, accent }: { role: string; trigram: MeihuaTrigram; accent?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-element px-2 py-0.5 text-[11px] ${
        accent ? 'bg-gold/15 text-gold' : 'border border-rim bg-[#0e111a] text-ink-variant'
      }`}
    >
      <span className="font-semibold">{role}</span>
      <span className="text-ink-muted">{POSITION_ZH[trigram.position] ?? ''}</span>
      <span className="font-display">
        {trigram.symbol}
        {trigram.name_zh}
      </span>
      <span className={wuxingText(trigram.element)}>{trigram.element}</span>
    </span>
  );
}
