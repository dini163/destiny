import type { FormEvent } from 'react';

import { useI18n } from '../../i18n/context';
import type { GematriaReading } from '../../types/kabbalah';
import type { Selection } from '../../lib/kabbalah';
import { Icon } from '../ui/Icon';

interface GematriaConsoleProps {
  /** Current input word. */
  value: string;
  onChange: (value: string) => void;
  /** A fold is in flight. */
  pending: boolean;
  /** Submit the word for weighing. */
  onSubmit: () => void;
}

/**
 * The gematria input console: a word is weighed with English ordinal gematria and
 * folded onto the fixed Tree. Like the other consoles it owns no birth data — just a
 * single text field. The server does the arithmetic; nothing is computed here.
 */
export function GematriaConsole({ value, onChange, pending, onSubmit }: GematriaConsoleProps) {
  const { t } = useI18n();
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (pending || value.trim() === '') return;
    onSubmit();
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="flex flex-1 items-center gap-2 rounded-element border border-rim bg-[var(--field-bg)] px-3 py-2 transition focus-within:border-rim-strong">
          <Icon name="search" size={16} className="shrink-0 text-ink-muted" />
          <input
            type="text"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder={t('输入一个拉丁词或名字，如 Metatron / Zohar')}
            className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
            aria-label={t('gematria 输入词')}
            maxLength={64}
          />
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending || value.trim() === ''}>
          <Icon name="gauge" size={18} />
          {pending ? t('称量中…') : t('称量折入')}
        </button>
      </div>
      <p className="text-xs leading-relaxed text-ink-muted">
        {t('以英文 ordinal（A=1…Z=26）逐字母求和，再折入固定的十原质与 22 路径。纯中文或无拉丁字母的输入会返回 ')}
        <span className="text-gold-soft">gematria_no_latin_letters</span>
        {t('，请改用拉丁拼写。')}
      </p>
    </form>
  );
}

/** One gematria statistic (ordinal / reduction / digital root). */
function Stat({ label, value }: { label: string; value: number }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col items-center gap-0.5 rounded-element border border-rim-soft bg-surface/50 px-3 py-2">
      <span className="numeric font-display text-2xl font-semibold text-gold">{value}</span>
      <span className="label-caps text-ink-muted">{t(label)}</span>
    </div>
  );
}

/**
 * The gematria reading: the numeric totals, the per-letter breakdown, the matched
 * Sephirah + Path (clickable — selecting one highlights it on the Tree) and the
 * synthesis composed from their real meanings.
 */
export function GematriaResult({
  reading,
  onSelect,
}: {
  reading: GematriaReading;
  onSelect: (selection: Selection) => void;
}) {
  const { t } = useI18n();
  const { sephirah, path } = reading;
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="label-caps text-ink-muted">{t('称量')}</span>
        <span className="font-display text-lg text-ink">{reading.normalized}</span>
        <span className="text-xs text-ink-muted">{t('（原文：{{text}}）', { text: reading.text })}</span>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <Stat label="ordinal" value={reading.english_ordinal} />
        <Stat label="reduction" value={reading.english_reduction} />
        <Stat label="数根" value={reading.digital_root} />
      </div>

      <div className="flex flex-wrap gap-1.5">
        {reading.breakdown.map((item, index) => (
          <span
            key={`${item.letter}-${index}`}
            className="inline-flex items-baseline gap-1 rounded-element border border-rim-soft bg-surface px-2 py-0.5 text-xs"
          >
            <span className="font-semibold text-ink-variant">{item.letter}</span>
            <span className="numeric text-gold-soft">{item.ordinal}</span>
          </span>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => onSelect({ kind: 'sephirah', id: sephirah.id })}
          className="flex items-center gap-3 rounded-element border border-rim-soft bg-surface/40 px-3 py-2.5 text-left transition hover:border-gold/50"
        >
          <span
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-sm font-semibold text-[#0b0e16]"
            style={{ backgroundColor: sephirah.color, borderColor: sephirah.color }}
          >
            {sephirah.number}
          </span>
          <span className="flex flex-col">
            <span className="label-caps text-ink-muted">{t('折入原质')}</span>
            <span className="font-display text-base text-ink">{sephirah.name_zh}</span>
            <span className="text-xs text-ink-muted">{sephirah.sphere}</span>
          </span>
        </button>

        <button
          type="button"
          onClick={() => onSelect({ kind: 'path', id: path.id })}
          className="flex items-center gap-3 rounded-element border border-rim-soft bg-surface/40 px-3 py-2.5 text-left transition hover:border-gold/50"
        >
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-gold bg-gold/10 text-lg text-gold">
            {path.letter}
          </span>
          <span className="flex flex-col">
            <span className="label-caps text-ink-muted">{t('折入路径')}</span>
            <span className="font-display text-base text-ink">
              {path.tarot_zh} <span className="text-xs text-ink-muted">{path.tarot_numeral}</span>
            </span>
            <span className="text-xs text-ink-muted">{path.correspondence}</span>
          </span>
        </button>
      </div>

      <p className="font-display text-sm leading-relaxed text-ink-variant">{reading.synthesis}</p>
    </div>
  );
}
