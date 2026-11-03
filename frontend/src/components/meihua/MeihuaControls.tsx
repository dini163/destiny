import type { FormEvent } from 'react';

import type { MeihuaMethod } from '../../types/meihua';
import { MEIHUA_METHODS } from '../../lib/meihua';
import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { ChineseDateTimeField } from '../ui/DateTimeFieldCombined';
import { SegmentedControl } from '../ui/SegmentedControl';
import { useI18n } from '../../i18n/context';

interface MeihuaControlsProps {
  /** Chosen raising method (起卦法). */
  method: MeihuaMethod;
  onMethodChange: (method: MeihuaMethod) => void;
  /** Reported numbers (报数) — used only by the number method; 1 to 3 entries. */
  numbers: string[];
  onNumbersChange: (numbers: string[]) => void;
  /** Optional divination question (free text). */
  question: string;
  onQuestionChange: (value: string) => void;
  /** Optional cast moment (`datetime-local` value); empty means "now" on the backend. */
  castTime: string;
  onCastTimeChange: (value: string) => void;
  /** A cast is in flight. */
  pending: boolean;
  /** Raise the hexagram. */
  onSubmit: () => void;
}

const METHOD_OPTIONS = MEIHUA_METHODS.map((option) => ({ value: option.value, label: option.label }));
const NUMBER_SLOTS = 3;

/**
 * The 梅花易数 divination console.
 *
 * Like Zhouyi it has no birth data, so it replaces the shared InputBar: the querent
 * picks 年月日时 or 报数, optionally frames a question and a cast moment, and — for
 * the number method — fills one to three 报数 slots. Method labels and hints mirror
 * `app.engines.meihua`; the derivation is deterministic (no secrets RNG), so the
 * same inputs always raise the same hexagram.
 */
export function MeihuaControls({
  method,
  onMethodChange,
  numbers,
  onNumbersChange,
  question,
  onQuestionChange,
  castTime,
  onCastTimeChange,
  pending,
  onSubmit,
}: MeihuaControlsProps) {
  const { t } = useI18n();
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (pending) {
      return;
    }
    onSubmit();
  }

  const activeMethod = MEIHUA_METHODS.find((option) => option.value === method);

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="seal" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">{t('梅花易数')}</h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                meihua-tiyong · 邵康节
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              {t('随感随应、物象心机。以年月日时或报数起卦，定体用、察互变、衡卦气旺衰，依体用生克直断吉凶。同数同刻必得同卦。')}
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="seal" size={18} />
          {pending ? t('起卦推演中…') : t('起卦 · 断体用')}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <LabeledField className="xl:col-span-7" label="起卦之法 / METHOD">
          <SegmentedControl
            ariaLabel="起卦方法"
            options={METHOD_OPTIONS}
            value={method}
            onChange={onMethodChange}
          />
          <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">{activeMethod ? t(activeMethod.hint) : null}</p>
          {method === 'number' ? (
            <NumberEditor numbers={numbers} onChange={onNumbersChange} />
          ) : null}
        </LabeledField>

        <div className="flex flex-col gap-4 xl:col-span-5">
          <LabeledField label="所占之事 / QUESTION" hint={<span className="text-ink-muted">可选</span>}>
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[var(--field-bg)] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="seal" size={16} className="shrink-0 text-ink-muted" />
              <input
                type="text"
                value={question}
                onChange={(event) => onQuestionChange(event.target.value)}
                title={t('问题文字用于记录关注点；系统提供牌义或盘面规则参考，不会理解或验证现实事件。')}
                placeholder={t('例如：今日访友可有际遇？')}
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                aria-label={t('所占之事')}
              />
            </div>
          <p className="text-xs leading-relaxed text-ink-muted">{t('问题文字只用于记录关注点；解读来自盘面规则，请结合真实情境核对。')}</p>
          </LabeledField>

          <LabeledField label="起卦时刻 / CAST TIME" hint={<span className="text-ink-muted">留空取当前</span>}>
            <ChineseDateTimeField value={castTime} onChange={onCastTimeChange} ariaLabel="起卦" />
          </LabeledField>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold" />
          {t('起卦之后，本页会把这一次读过的每一张表、历法引擎与算式口径逐条列在盘下，出处由引擎署名，控制台不代它声明。')}
        </span>
      </div>
    </form>
  );
}

/** One to three 报数 slots for the number method (later slots optional). */
function NumberEditor({ numbers, onChange }: { numbers: string[]; onChange: (numbers: string[]) => void }) {
  const { t } = useI18n();
  function setSlot(index: number, value: string): void {
    const next = numbers.slice();
    next[index] = value.replace(/[^\d]/g, '').slice(0, 6);
    onChange(next);
  }

  return (
    <div className="mt-3 flex flex-col gap-2 rounded-element border border-rim-soft bg-surface p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="label-caps">{t('报数起卦 · REPORTED NUMBERS')}</span>
        <span className="text-[11px] text-ink-muted">{t('填一至三个正整数；后位留空则按前位起卦')}</span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {Array.from({ length: NUMBER_SLOTS }, (_, index) => (
          <div key={index} className="flex items-center gap-1.5">
            <span className="numeric text-[11px] text-ink-muted">{t('第{{n}}数', { n: index + 1 })}</span>
            <input
              type="text"
              inputMode="numeric"
              value={numbers[index] ?? ''}
              onChange={(event) => setSlot(index, event.target.value)}
              placeholder="—"
              aria-label={t('第{{n}}个报数', { n: index + 1 })}
              className="field numeric w-20 text-center"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
