import { ELEMENT_ORDER, MODALITY_ORDER, elementStyle, modalityStyle } from '../../lib/astro';
import { useI18n } from '../../i18n/context';

interface ElementBalanceProps {
  /** fire/earth/air/water counts among the ten bodies. */
  elementBalance: Record<string, number>;
  /** cardinal/fixed/mutable counts among the ten bodies. */
  modalityBalance: Record<string, number>;
}

/**
 * Element + modality balance (元素与形态分布).
 *
 * Bars are driven purely by the engine's real head-counts (each set sums to the
 * ten bodies); the percentage is count ÷ total. The three signs listed under
 * each element are a fixed zodiac fact, not chart-derived interpretation.
 */
export function ElementBalance({ elementBalance, modalityBalance }: ElementBalanceProps) {
  const { t } = useI18n();
  const elementTotal = Object.values(elementBalance).reduce((sum, n) => sum + n, 0) || 1;
  const modalityTotal = Object.values(modalityBalance).reduce((sum, n) => sum + n, 0) || 1;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <span className="label-caps mb-2 block text-ink-muted">{t('四元素分布 · ELEMENTS')}</span>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {ELEMENT_ORDER.map((key) => {
            const count = elementBalance[key] ?? 0;
            const style = elementStyle(key);
            const percent = Math.round((count / elementTotal) * 100);
            return (
              <BalanceBar
                key={key}
                label={style.label}
                color={style.color}
                count={count}
                percent={percent}
                footnote={style.signs}
              />
            );
          })}
        </div>
      </div>

      <div>
        <span className="label-caps mb-2 block text-ink-muted">{t('三形态分布 · MODALITIES')}</span>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          {MODALITY_ORDER.map((key) => {
            const count = modalityBalance[key] ?? 0;
            const style = modalityStyle(key);
            const percent = Math.round((count / modalityTotal) * 100);
            return (
              <BalanceBar key={key} label={style.label} color={style.color} count={count} percent={percent} />
            );
          })}
        </div>
      </div>
    </div>
  );
}

/** A labelled proportion bar with an optional footnote. */
function BalanceBar({
  label,
  color,
  count,
  percent,
  footnote,
}: {
  label: string;
  color: string;
  count: number;
  percent: number;
  footnote?: string;
}) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-1 rounded-element border border-rim-soft bg-surface p-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="label-caps" style={{ color }}>
          {label}
        </span>
        <span className="numeric text-xs text-ink">
          {t('{{count}} 星 · {{percent}}%', { count, percent })}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-raised">
        <div className="h-full rounded-full" style={{ width: `${percent}%`, backgroundColor: color }} />
      </div>
      {footnote ? <span className="text-[11px] text-ink-muted">{footnote}</span> : null}
    </div>
  );
}
