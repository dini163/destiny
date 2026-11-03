import { useI18n } from '../../i18n/context';
import { PlainProse } from '../ui/PlainProse';
import { ScoreLedger } from '../ui/ScoreLedger';
import { SourceNote } from '../ui/SourceNote';
import { VerdictCard } from '../ui/VerdictCard';
import type { BaziInterpretation, DimensionReading } from '../../types/bazi';

/**
 * 六维详批. `narrative` is the engine's join of the fired rules' own readings and
 * `plain` is the engine's join of their plain-language mirrors — the grid composes
 * no sentence of its own either way; it only fixes the reading order (conclusion
 * card first, then plain, then the technical ledger as the footnote).
 * 2026-10-21 verdict-card spec §6：结论卡片（结论先行）在六维卡之前；总论段并入卡片
 * headline（`plain_summary` 与 `verdict.headline` 同串），不再单挂一段。Spec §6.7, §8.2,
 * plain-reading spec §6.
 */
export function DimensionGrid({ reading }: { reading: BaziInterpretation }) {
  return (
    <div className="flex flex-col gap-4">
      <VerdictCard verdict={reading.verdict} />
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        {reading.six_dimensions.map((dimension) => (
          <DimensionCard key={dimension.dimension} dimension={dimension} />
        ))}
      </div>
      <p className="text-sm text-ink-variant">{reading.summary}</p>
    </div>
  );
}

function DimensionCard({ dimension }: { dimension: DimensionReading }) {
  const { t } = useI18n();
  return (
    <article className="flex flex-col gap-3 rounded-card border border-rim bg-surface p-4">
      <h3 className="font-display text-lg font-bold text-gold-bright">{t(dimension.dimension)}</h3>
      <ScoreLedger score={dimension.score} label="维度得分" />
      {dimension.strengths.length > 0 ? (
        <LineList tone="strengths" items={dimension.strengths} />
      ) : null}
      {dimension.cautions.length > 0 ? (
        <LineList tone="cautions" items={dimension.cautions} />
      ) : null}
      <PlainProse text={dimension.plain} />
      <p className="text-xs leading-relaxed text-ink-variant">{dimension.narrative}</p>
      <span className="self-end">
        <SourceNote source={dimension.source} />
      </span>
    </article>
  );
}

/** strengths 用中性列、cautions 用火色列：吉凶着色与神煞表同一套语汇。 */
function LineList({ tone, items }: { tone: 'strengths' | 'cautions'; items: string[] }) {
  const { t } = useI18n();
  const accent = tone === 'strengths' ? 'text-wuxing-wood' : 'text-wuxing-fire';
  return (
    <ul className="flex flex-col gap-1 text-xs">
      {items.map((item) => (
        <li key={`${tone}-${item}`} className="flex gap-1.5">
          <span className={accent}>{tone === 'strengths' ? t('利') : t('忌')}</span>
          <span className="text-ink-variant">{item}</span>
        </li>
      ))}
    </ul>
  );
}
