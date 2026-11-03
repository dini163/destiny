import { useI18n } from '../../i18n/context';
import { SourceNote } from '../ui/SourceNote';
import { wuxingChip } from '../../lib/wuxing';
import type { Yongshen, YongshenConflict, YongshenMethod } from '../../types/bazi';

/**
 * 用神三法（扶抑 / 通关 / 调候）逐条摊开。
 *
 * A method that stayed silent is listed, not hidden: `fired_rule` records which
 * branch was taken even when it chose nothing (spec §6.5 rule 3), and "调候未触发"
 * is information the reader needs to trust the ones that did fire.
 */
export function YongshenPanel({ yongshen }: { yongshen: Yongshen }) {
  return (
    <div className="flex flex-col gap-4">
      <ElementLine label="喜用" elements={yongshen.favorable_elements} />
      <ElementLine label="忌仇" elements={yongshen.unfavorable_elements} />
      {yongshen.conflict ? <ConflictNote conflict={yongshen.conflict} /> : null}
      <ul className="flex flex-col gap-2">
        {yongshen.methods.map((method) => (
          <MethodLine key={method.method} method={method} />
        ))}
      </ul>
    </div>
  );
}

/** The merged verdict as a row of five-element chips. */
function ElementLine({ label, elements }: { label: string; elements: string[] }) {
  const { t } = useI18n();
  return (
    <div className="flex items-center justify-between gap-2 rounded-element bg-[var(--field-bg)] px-3 py-2">
      <span className="label-caps">{t(label)}</span>
      <span className="flex flex-wrap items-center justify-end gap-1.5">
        {elements.length > 0 ? (
          elements.map((element) => (
            <span key={element} className={`rounded-element px-2 py-0.5 text-xs ${wuxingChip(element)}`}>
              {t(element)}
            </span>
          ))
        ) : (
          <span className="text-xs text-ink-muted">{t('三法互斥后无取用（见下）')}</span>
        )}
      </span>
    </div>
  );
}

/** One method: name, the rule branch it took, what it chose, and the source. */
function MethodLine({ method }: { method: YongshenMethod }) {
  const { t } = useI18n();
  const silent = method.chosen_elements.length === 0;
  return (
    <li className="flex flex-col gap-1.5 rounded-element border border-rim bg-[var(--field-bg)] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-display text-base text-ink">{method.method}</span>
        <span className="numeric text-xs text-ink-muted">{method.fired_rule}</span>
      </div>
      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        {silent ? (
          <span className="text-ink-muted">{t('未取用')}</span>
        ) : (
          method.chosen_elements.map((element) => (
            <span key={element} className={`rounded-element px-2 py-0.5 ${wuxingChip(element)}`}>
              {t(element)}
            </span>
          ))
        )}
        {method.already_present ? (
          <span className="label-caps rounded-element border border-rim-strong px-1.5 py-0.5 text-ink-muted">
            {t('命局已备')}
          </span>
        ) : null}
      </div>
      <span className="self-end">
        <SourceNote source={method.source} />
      </span>
    </li>
  );
}

/** Two methods disagreeing: shown as the engine's own sentence, side by side. */
function ConflictNote({ conflict }: { conflict: YongshenConflict }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-1.5 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="label-caps text-wuxing-fire">{t('取用冲突')}</span>
        <span className={`rounded-element px-2 py-0.5 text-xs ${wuxingChip(conflict.element)}`}>
          {t(conflict.element)}
        </span>
        {/* "相左"是引擎 reason 里的原词；suppressed_by 记的是持异议的那一法（恒为扶抑）。 */}
        <span className="text-xs text-ink-muted" title="suppressed_by">
          {t('与 {{method}} 相左', { method: conflict.suppressed_by })}
        </span>
      </div>
      <p className="text-sm leading-relaxed text-ink-variant">{conflict.reason}</p>
      <span className="self-end">
        <SourceNote source={conflict.source} />
      </span>
    </div>
  );
}
