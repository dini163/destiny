import type { FormEvent } from 'react';

import { SPREAD_CATALOG } from '../../lib/tarot';
import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { SegmentedControl } from '../ui/SegmentedControl';

interface SpreadControlsProps {
  /** Currently chosen spread id. */
  spreadId: string;
  onSpreadChange: (id: string) => void;
  /** Optional focus question (free text). */
  question: string;
  onQuestionChange: (value: string) => void;
  /** Whether cards may land reversed. */
  allowReversed: boolean;
  onAllowReversedChange: (value: boolean) => void;
  /** A draw is in flight. */
  pending: boolean;
  /** Shuffle + deal the chosen spread. */
  onSubmit: () => void;
}

type ReversalMode = 'both' | 'upright';

const REVERSAL_OPTIONS: ReadonlyArray<{ value: ReversalMode; label: string }> = [
  { value: 'both', label: '正逆位' },
  { value: 'upright', label: '仅正位' },
];

/**
 * The oracle console (塔罗神谕 input stage).
 *
 * Tarot has no birth data, so this replaces the shared InputBar: the reader
 * picks one of the six real spreads, optionally frames a question, chooses
 * whether reversals apply, and deals. Spread tiles are driven by the catalogue
 * mirrored from the backend library, so counts and names are never invented.
 */
export function SpreadControls({
  spreadId,
  onSpreadChange,
  question,
  onQuestionChange,
  allowReversed,
  onAllowReversedChange,
  pending,
  onSubmit,
}: SpreadControlsProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (pending) {
      return;
    }
    onSubmit();
  }

  const reversal: ReversalMode = allowReversed ? 'both' : 'upright';

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="sparkle" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">塔罗秘仪神谕</h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                secrets CSPRNG 洗牌
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              78 张伟特系（Rider-Waite）大小阿卡纳，牌义取自主策展牌库。选定牌阵、凝神求问，即可布阵抽牌并逐张翻开。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="sparkle" size={18} />
          {pending ? '洗牌布阵中…' : '洗牌 · 布阵 · 抽牌'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <LabeledField className="xl:col-span-8" label="牌阵蓝图 / SPREAD">
          <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
            {SPREAD_CATALOG.map((spread) => {
              const active = spread.id === spreadId;
              return (
                <button
                  key={spread.id}
                  type="button"
                  onClick={() => onSpreadChange(spread.id)}
                  aria-pressed={active}
                  className={`flex flex-col gap-1 rounded-element border p-2.5 text-left transition ${
                    active
                      ? 'border-gold-strong bg-gold/10'
                      : 'border-rim bg-[#0e111a] hover:border-rim-strong'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`font-display text-sm font-semibold ${active ? 'text-gold-bright' : 'text-ink'}`}
                    >
                      {spread.name_zh}
                    </span>
                    <span className={`numeric shrink-0 text-xs ${active ? 'text-gold' : 'text-ink-muted'}`}>
                      {spread.size} 张
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </LabeledField>

        <div className="flex flex-col gap-4 xl:col-span-4">
          <LabeledField label="求问焦点 / QUESTION" hint={<span className="text-ink-muted">可选</span>}>
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="seal" size={16} className="shrink-0 text-ink-muted" />
              <input
                type="text"
                value={question}
                onChange={(event) => onQuestionChange(event.target.value)}
                placeholder="例如：我该如何看待当前事业的转折？"
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                aria-label="求问焦点"
              />
            </div>
          </LabeledField>

          <LabeledField label="正逆位 / ORIENTATION">
            <SegmentedControl
              ariaLabel="正逆位设置"
              options={REVERSAL_OPTIONS}
              value={reversal}
              onChange={(next) => onAllowReversedChange(next === 'both')}
            />
          </LabeledField>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold" />
          洗牌与正逆位由 Python <span className="text-gold-soft">secrets</span>（操作系统级 CSPRNG）决定，每次抽牌独立且不可复现。
        </span>
        <span>牌名、关键词与牌义取自主策展 78 张牌库，综合解读由引擎的固定句式串起这些字段。</span>
      </div>
    </form>
  );
}
