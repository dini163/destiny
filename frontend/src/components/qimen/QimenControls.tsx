import type { FormEvent } from 'react';

import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { ChineseDateTimeField } from '../ui/DateTimeField';

interface QimenControlsProps {
  /** Optional divination question (占问事项, free text). */
  question: string;
  onQuestionChange: (value: string) => void;
  /** Optional cast moment (`datetime-local` value); empty means "now" on the backend. */
  castTime: string;
  onCastTimeChange: (value: string) => void;
  /** A cast is in flight. */
  pending: boolean;
  /** Raise the board. */
  onSubmit: () => void;
}

/**
 * The 奇门遁甲 divination console.
 *
 * Like 梅花/六爻 it has no birth data, so it replaces the shared InputBar: the querent
 * frames an optional 占问事项 and 用事时刻, then 起局. The 节气 / 阴阳遁 / 局数 / 值符值使
 * are all derived deterministically from that moment by `app.engines.qimen` — same
 * input, same board.
 */
export function QimenControls({
  question,
  onQuestionChange,
  castTime,
  onCastTimeChange,
  pending,
  onSubmit,
}: QimenControlsProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (pending) {
      return;
    }
    onSubmit();
  }

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="gauge" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">奇门遁甲</h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                qimen-luoshu · 时家转盘
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              帝王之术，以用事时辰定阴阳遁与局数，布三奇六仪地盘，转天盘九星、人盘八门、神盘八神入洛书九宫，定值符值使，察旬空驿马，谋定决策之时空场。起局纯为确定性推算，同时必得同盘。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="gauge" size={18} />
          {pending ? '起局排盘中…' : '起局 · 排九宫'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <LabeledField label="占问事项 / QUESTION" hint={<span className="text-ink-muted">可选</span>}>
          <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
            <Icon name="seal" size={16} className="shrink-0 text-ink-muted" />
            <input
              type="text"
              value={question}
              onChange={(event) => onQuestionChange(event.target.value)}
              placeholder="例如：此行洽谈可否成事？"
              className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
              aria-label="占问事项"
            />
          </div>
        </LabeledField>

        <LabeledField label="用事时刻 / CAST TIME" hint={<span className="text-ink-muted">留空取当前</span>}>
          <ChineseDateTimeField value={castTime} onChange={onCastTimeChange} ariaLabel="用事" />
        </LabeledField>
      </div>

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold" />
          年月日时干支与节气由权威历法真实推算；九星八门八神、局数歌诀取自策展奇门数据，未作运行时虚构。时辰径取钟点，未校正真太阳时。
        </span>
      </div>
    </form>
  );
}
