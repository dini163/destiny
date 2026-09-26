import type { FormEvent } from 'react';

import type { MeihuaMethod } from '../../types/meihua';
import { MEIHUA_METHODS } from '../../lib/meihua';
import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { ChineseDateTimeField } from '../ui/DateTimeField';
import { SegmentedControl } from '../ui/SegmentedControl';

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
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">梅花易数</h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                meihua-tiyong · 邵康节
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              随感随应、物象心机。以年月日时或报数起卦，定体用、察互变、衡卦气旺衰，依体用生克直断吉凶。起卦纯为确定性推算，同数同刻必得同卦。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="seal" size={18} />
          {pending ? '起卦推演中…' : '起卦 · 断体用'}
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
          <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">{activeMethod?.hint}</p>
          {method === 'number' ? (
            <NumberEditor numbers={numbers} onChange={onNumbersChange} />
          ) : null}
        </LabeledField>

        <div className="flex flex-col gap-4 xl:col-span-5">
          <LabeledField label="所占之事 / QUESTION" hint={<span className="text-ink-muted">可选</span>}>
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="seal" size={16} className="shrink-0 text-ink-muted" />
              <input
                type="text"
                value={question}
                onChange={(event) => onQuestionChange(event.target.value)}
                placeholder="例如：今日访友可有际遇？"
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                aria-label="所占之事"
              />
            </div>
          </LabeledField>

          <LabeledField label="起卦时刻 / CAST TIME" hint={<span className="text-ink-muted">留空取当前</span>}>
            <ChineseDateTimeField value={castTime} onChange={onCastTimeChange} ariaLabel="起卦" />
          </LabeledField>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold" />
          农历月日、时辰与月令由 <span className="text-gold-soft">lunar-python</span> 真实推算；卦象、卦辞取自策展《周易》数据，未作运行时虚构。
        </span>
      </div>
    </form>
  );
}

/** One to three 报数 slots for the number method (later slots optional). */
function NumberEditor({ numbers, onChange }: { numbers: string[]; onChange: (numbers: string[]) => void }) {
  function setSlot(index: number, value: string): void {
    const next = numbers.slice();
    next[index] = value.replace(/[^\d]/g, '').slice(0, 6);
    onChange(next);
  }

  return (
    <div className="mt-3 flex flex-col gap-2 rounded-element border border-rim-soft bg-surface p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="label-caps">报数起卦 · REPORTED NUMBERS</span>
        <span className="text-[11px] text-ink-muted">填一至三个正整数；后位留空则按前位起卦</span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {Array.from({ length: NUMBER_SLOTS }, (_, index) => (
          <div key={index} className="flex items-center gap-1.5">
            <span className="numeric text-[11px] text-ink-muted">第{index + 1}数</span>
            <input
              type="text"
              inputMode="numeric"
              value={numbers[index] ?? ''}
              onChange={(event) => setSlot(index, event.target.value)}
              placeholder="—"
              aria-label={`第${index + 1}个报数`}
              className="field numeric w-20 text-center"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
