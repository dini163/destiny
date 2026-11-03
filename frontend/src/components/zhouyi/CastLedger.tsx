import type { ZhouyiLine } from '../../types/zhouyi';
import { lineValueMeta, positionLabel } from '../../lib/zhouyi';
import { useI18n } from '../../i18n/context';

interface CastLedgerProps {
  /** The six dressed lines, bottom-to-top (throw order equals position order). */
  lines: ZhouyiLine[];
}

/**
 * The throw ledger (起卦记录): one row per cast, in the order the lines were
 * drawn (初爻 → 上爻).
 *
 * Each row reports only what the engine returns — the coin-sum value (6/7/8/9),
 * its classical name (老阴/少阳/少阴/老阳), polarity and whether it moves. For the
 * three-coin and time methods the backend returns the summed value, not the
 * individual faces, so no "2+3+3" breakdown is fabricated here (no-mock rule);
 * the manual editor in the console is where the caller's own coins are shown.
 */
export function CastLedger({ lines }: CastLedgerProps) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-1.5">
      {lines.map((line) => {
        const meta = lineValueMeta(line.value);
        return (
          <div
            key={line.position}
            className="flex items-center gap-2 rounded-element border border-rim-soft bg-[var(--field-bg)]/60 px-2.5 py-1.5"
          >
            <span className="numeric w-11 shrink-0 text-[11px] text-ink-muted">{t('第 {{n}} 掷', { n: line.position })}</span>
            <span className="w-9 shrink-0 font-display text-xs text-ink-variant">
              {positionLabel(line.position)}
            </span>
            <span className="numeric flex h-6 w-6 shrink-0 items-center justify-center rounded-element bg-surface text-xs font-bold text-gold-bright">
              {line.value}
            </span>
            <span aria-hidden="true" className="shrink-0 text-sm text-ink-muted">
              {line.symbol}
            </span>
            <span
              className={`shrink-0 text-xs ${meta.moving ? 'font-medium text-gold-soft' : 'text-ink-variant'}`}
            >
              {meta.name}
            </span>
            <span
              className={`ml-auto shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                meta.moving ? 'bg-wuxing-fire/20 text-wuxing-fire' : 'bg-surface text-ink-muted'
              }`}
            >
              {meta.moving ? t('动爻') : t('静爻')}
            </span>
          </div>
        );
      })}
      <p className="mt-1 text-[11px] leading-snug text-ink-muted">
        {t('数值 6/7/8/9 定老少阴阳：六老阴、七少阳、八少阴、九老阳；老阴老阳为动爻，动则变卦生。')}
      </p>
    </div>
  );
}
