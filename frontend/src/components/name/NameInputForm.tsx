import { useState } from 'react';
import type { FormEvent } from 'react';

import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import type { ApiError } from '../../api/client';
import type { NameAnalyzeRequest } from '../../types/name';

/** `ambiguous_traditional` 的 context 形状（后端 spec §7）。 */
interface AmbiguousChoice {
  char: string;
  candidates: string[];
}

function ambiguousChoices(error: ApiError | null): AmbiguousChoice[] {
  if (!error || error.code !== 'ambiguous_traditional') return [];
  const raw = error.context?.choices;
  return Array.isArray(raw) ? (raw as AmbiguousChoice[]) : [];
}

interface NameInputFormProps {
  pending: boolean;
  error: ApiError | null;
  onSubmit: (request: NameAnalyzeRequest) => void;
}

/**
 * 姓名输入台。
 *
 * 一简对多繁不靠猜（spec 决策六）：后端回 422 与候选字列表，这里把候选渲染成按钮，
 * 点一次即写入 `variants` 并自动重投。`variants` 在两次提交之间保留，所以已定过的
 * 字不会被重复追问。
 */
export function NameInputForm({ pending, error, onSubmit }: NameInputFormProps) {
  const [surname, setSurname] = useState('');
  const [given, setGiven] = useState('');
  const [variants, setVariants] = useState<Record<string, string>>({});

  const choices = ambiguousChoices(error);
  const message = error && choices.length === 0 ? error.message : null;

  function submit(overrides: Record<string, string>): void {
    const trimmed = { surname: surname.trim(), given: given.trim() };
    if (!trimmed.surname || !trimmed.given) return;
    // 仍有歧义的字才需要 variants；未定过时传 null，让后端自己判唯一候选。
    onSubmit({ ...trimmed, variants: Object.keys(overrides).length > 0 ? overrides : null });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    submit(variants);
  }

  function pick(char: string, traditional: string): void {
    const next = { ...variants, [char]: traditional };
    setVariants(next);
    submit(next);
  }

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="search" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">
                姓名参玄研判
              </h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                kangxi · 五格剖象
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              逐字以《康熙字典》部首体系核定笔画（由 Unihan 推导，非手抄），再依天、人、地、外、总五格
              配八十一数理吉凶与三才生克。一简对多繁不代作主张：需点选正体字。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="sparkle" size={18} />
          核定笔画
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <LabeledField label="姓氏（1–2 字）">
          <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
            <input
              className="w-full bg-transparent font-display text-base text-ink outline-none"
              value={surname}
              onChange={(event) => setSurname(event.target.value)}
              placeholder="如 陸"
              aria-label="姓氏"
            />
          </div>
        </LabeledField>
        <LabeledField label="名字（1–3 字）">
          <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
            <input
              className="w-full bg-transparent font-display text-base text-ink outline-none"
              value={given}
              onChange={(event) => setGiven(event.target.value)}
              placeholder="如 青玄"
              aria-label="名字"
            />
          </div>
        </LabeledField>
      </div>

      {Object.keys(variants).length > 0 ? (
        <p className="label-caps text-ink-muted">
          已指定正体：
          {Object.entries(variants)
            .map(([source, target]) => `${source}→${target}`)
            .join('、')}
          <button
            type="button"
            onClick={() => setVariants({})}
            className="ml-2 hover:text-gold-soft"
          >
            清除
          </button>
        </p>
      ) : null}

      {choices.length > 0 ? (
        <div className="flex flex-col gap-2 rounded-element border border-gold/40 bg-gold/10 px-4 py-3">
          <p className="text-sm text-ink">以下字一简对多繁，笔画随正体而变，请指定：</p>
          {choices.map((choice) => (
            <div key={choice.char} className="flex flex-wrap items-center gap-2">
              <span className="font-display text-base text-gold-bright">{choice.char}</span>
              {choice.candidates.map((candidate) => (
                <button
                  key={candidate}
                  type="button"
                  onClick={() => pick(choice.char, candidate)}
                  className="btn-ghost rounded-element border border-rim px-2 py-1 text-sm"
                >
                  {candidate}
                </button>
              ))}
            </div>
          ))}
        </div>
      ) : null}

      {message ? (
        <p className="flex items-start gap-2 text-sm text-ink">
          <Icon name="alert" size={16} className="mt-0.5 shrink-0 text-wuxing-fire" />
          {message}
        </p>
      ) : null}
    </form>
  );
}
