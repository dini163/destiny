import type { FormEvent } from 'react';

import type { SignificatorChoice } from '../../types/lenormand';
import { SIGNIFICATOR_OPTIONS, SPREAD_OPTIONS } from '../../lib/lenormand';
import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { SegmentedControl } from '../ui/SegmentedControl';

interface LenormandControlsProps {
  /** Chosen spread id. */
  spread: string;
  onSpreadChange: (spread: string) => void;
  /** Querent significator choice. */
  significator: SignificatorChoice;
  onSignificatorChange: (value: SignificatorChoice) => void;
  /** Optional question (free text). */
  question: string;
  onQuestionChange: (value: string) => void;
  /** A draw is in flight. */
  pending: boolean;
  /** Draw the spread. */
  onSubmit: () => void;
}

const SPREAD_SEGMENTS = SPREAD_OPTIONS.map((option) => ({ value: option.value, label: option.label }));
const SIGNIFICATOR_SEGMENTS = SIGNIFICATOR_OPTIONS.map((option) => ({ value: option.value, label: option.label }));

/**
 * The 雷诺曼 divination console.
 *
 * Like tarot it has no birth data, so it replaces the shared InputBar: the querent
 * picks a 牌阵, optionally marks their 指示牌 (男人/女人) and frames a question, then
 * draws. Cards are shuffled with an OS-backed CSPRNG on the server, so every draw is
 * fresh; the reading is composed from the curated 36-card library.
 */
export function LenormandControls({
  spread,
  onSpreadChange,
  significator,
  onSignificatorChange,
  question,
  onQuestionChange,
  pending,
  onSubmit,
}: LenormandControlsProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (pending) {
      return;
    }
    onSubmit();
  }

  const activeSpread = SPREAD_OPTIONS.find((option) => option.value === spread);

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="vault" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">雷诺曼神谕</h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                lenormand · 36 张组合直读
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              欧式三十六张生活微观象征牌，一律正位、以组合直读见长：前牌为主、后牌为饰，两两相叠成句。可选指示牌定位问卜者，大桌全景尽铺三十六张作命运俯瞰。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="sparkle" size={18} />
          {pending ? '洗牌抽牌中…' : '洗牌 · 抽牌'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <LabeledField className="xl:col-span-7" label="牌阵 / SPREAD">
          <SegmentedControl
            ariaLabel="牌阵"
            options={SPREAD_SEGMENTS}
            value={spread}
            onChange={onSpreadChange}
          />
          <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">
            <span className="numeric mr-1 text-gold-soft">{activeSpread?.size ?? 0} 张</span>
            {activeSpread?.hint}
          </p>
        </LabeledField>

        <div className="flex flex-col gap-4 xl:col-span-5">
          <LabeledField label="指示牌 / SIGNIFICATOR" hint={<span className="text-ink-muted">大桌尤重</span>}>
            <SegmentedControl
              ariaLabel="指示牌"
              options={SIGNIFICATOR_SEGMENTS}
              value={significator}
              onChange={onSignificatorChange}
            />
          </LabeledField>

          <LabeledField label="所问之事 / QUESTION" hint={<span className="text-ink-muted">可选</span>}>
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="seal" size={16} className="shrink-0 text-ink-muted" />
              <input
                type="text"
                value={question}
                onChange={(event) => onQuestionChange(event.target.value)}
                placeholder="例如：这段合作关系前景如何？"
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                aria-label="所问之事"
              />
            </div>
          </LabeledField>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold" />
          抽牌由权威算法真实洗牌、无重复发牌；牌义与组合直读取自策展 36 张牌库，未作运行时虚构。
        </span>
      </div>
    </form>
  );
}
