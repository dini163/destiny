import type { MeihuaCast, TiYongParty } from '../../types/meihua';
import { relationChip } from '../../lib/meihua';
import { wuxingChip, wuxingText } from '../../lib/wuxing';
import { PlainProse } from '../ui/PlainProse';

interface TiYongPanelProps {
  /** The complete cast — supplies 体卦 / 用卦, the 生克 verdict and the 卦气 context. */
  cast: MeihuaCast;
}

/** 体 / 用 role captions: the subject (self) vs. the object (the matter). */
const ROLE_META: Record<string, { title: string; gloss: string }> = {
  ti: { title: '体卦', gloss: '主 · 己方 · 无动爻之卦' },
  yong: { title: '用卦', gloss: '客 · 所占之事 · 含动爻之卦' },
};

/**
 * 体用生克 — the heart of a 梅花易数 reading.
 *
 * The 体卦 (subject) and 用卦 (object) are shown with their 五行, 万物类象 and
 * 卦气旺衰 state under the current 月令; the banner then states the primary
 * 生克 relation (用生体 / 比和 / 体克用 / 体生用 / 用克体) and its judgement. All
 * text is the engine's own; the panel only colours and arranges it.
 *
 * 阅读顺序按 spec §10 第一条 bullet「清单类就地嵌」排：白话整段（`plain_summary`）在上，
 * 技术判语（`tiyong.text`）降为小字脚注。面板自己一个字都不写，两段的字都来自引擎。
 */
export function TiYongPanel({ cast }: TiYongPanelProps) {
  const { ti, yong, tiyong, wangshuai } = cast;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 rounded-element border border-rim-soft bg-[var(--field-bg)] px-3 py-2 text-xs">
        <span className="label-caps text-ink-muted">卦气 · 月令</span>
        <span className="font-display text-ink-variant">
          {wangshuai.season_zh}（{wangshuai.month_zhi}月）
        </span>
        <span className="text-ink-muted">当令</span>
        <span className={`font-display ${wuxingText(wangshuai.commanding_element)}`}>
          {wangshuai.commanding_element}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <PartyCard party={ti} accent />
        <PartyCard party={yong} />
      </div>

      <div className="flex flex-col gap-2 rounded-card border border-rim-strong bg-surface/70 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="label-caps text-ink-muted">体用生克 · VERDICT</span>
          <span className="font-display text-lg font-semibold text-ink">{tiyong.relation_zh}</span>
          <span className={`rounded-element px-2 py-0.5 text-xs font-semibold ${relationChip(tiyong.verdict)}`}>
            {tiyong.verdict}
          </span>
        </div>
        <PlainProse text={cast.plain_summary} className="rounded-element border border-rim-soft bg-[var(--field-bg)] p-3" />
        <p className="text-xs leading-relaxed text-ink-muted">{tiyong.text}</p>
      </div>
    </div>
  );
}

/** One 体 / 用 card: role, trigram identity, 五行, 万物类象 and 旺衰. */
function PartyCard({ party, accent }: { party: TiYongParty; accent?: boolean }) {
  const meta = ROLE_META[party.role] ?? { title: party.role, gloss: '' };
  const { trigram } = party;

  return (
    <div
      className={`flex flex-col gap-3 rounded-card border p-4 ${
        accent ? 'border-gold/40 bg-gold/[0.06]' : 'border-rim bg-surface/60'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col">
          <span className={`font-display text-base font-semibold ${accent ? 'text-gold-bright' : 'text-ink'}`}>
            {meta.title}
          </span>
          <span className="text-[11px] leading-snug text-ink-muted">{meta.gloss}</span>
        </div>
        <span className={`rounded-element px-2 py-0.5 text-[11px] ${wuxingChip(trigram.element)}`}>
          {trigram.element}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="font-display text-3xl leading-none text-gold">{trigram.symbol}</span>
        <div className="flex flex-col">
          <span className="font-display text-lg text-ink">
            {trigram.name_zh}
            <span className="ml-1 text-sm text-ink-muted">为{trigram.nature_zh}</span>
          </span>
          <span className="numeric text-[11px] text-ink-muted">{trigram.position === 'lower' ? '内卦' : '外卦'}</span>
        </div>
      </div>

      <p className="text-xs leading-relaxed text-ink-variant">{party.leixiang}</p>

      <div className="gold-rule" />

      <div className="flex items-baseline gap-2">
        <span className="label-caps text-ink-muted">旺衰</span>
        <span className={`font-display text-sm font-semibold ${wuxingText(trigram.element)}`}>{party.wangshuai}</span>
      </div>
      <p className="text-[11px] leading-relaxed text-ink-muted">{party.wangshuai_text}</p>
    </div>
  );
}
