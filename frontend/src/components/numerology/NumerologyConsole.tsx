import { useState } from 'react';
import type { FormEvent } from 'react';

import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import type { NumerologyChartRequest } from '../../types/numerology';

/** 表单状态。与 `NumerologyChartRequest` 同义，只是各字段的形状跟着控件走。 */
interface ConsoleState {
  fullName: string;
  nameZh: string;
  birthDate: string;
  referenceDate: string;
  yAsVowel: boolean;
}

const EMPTY: ConsoleState = {
  fullName: '',
  nameZh: '',
  birthDate: '',
  referenceDate: '',
  yAsVowel: false,
};

/** 状态 → 请求。空着的选填项**不写那个键**，而不是写 `null` 或 `''`。 */
function requestOf(state: ConsoleState): NumerologyChartRequest {
  return {
    full_name: state.fullName.trim(),
    name_zh: state.nameZh.trim() || null,
    birth_date: state.birthDate,
    ...(state.referenceDate === '' ? {} : { reference_date: state.referenceDate }),
    y_as_vowel: state.yAsVowel,
  };
}

interface NumerologyConsoleProps {
  pending: boolean;
  /** 屏上是否已有一份结果：决定 Y 开关要不要当场重投。 */
  hasChart: boolean;
  onSubmit: (request: NumerologyChartRequest) => void;
}

/**
 * 灵数输入台（spec §8、决策 1）。
 *
 * 表单自己把前提写死在明面上：**毕达哥拉斯映射定义在拉丁字母表上，请输入拼音或英文名**。
 * 这一句不是提示语而是系统的边界 —— 后端没有、也绝不会有汉字→字母的假映射，纯中文名会回
 * 422 + `numerology_no_latin_letters`。中文名仍然可以填，但只作回显，标注清楚，不参与计算。
 *
 * Y 元音开关同理（决策 7）：`Lynn` 的 Y 是元音、`Yolanda` 的 Y 不是，而音节切分既不可判定
 * 也不可单测，故系统不代作主张，默认按辅音，把判据写在开关旁边交给用户。
 *
 * 开关拨动时若屏上已有结果就**当场重投**：走查第 9 条要看的正是「灵魂冲动数与人格面具数
 * 此消彼长、表达数不变」在 UI 上也成立，而这需要上一份结果留在屏上做参照（hook 用
 * `useLastSuccessMutation` 就是为了这个）。还没有结果时不重投，免得用户刚拨一下就被
 * 一句"请先填生日"打断。
 */
export function NumerologyConsole({ pending, hasChart, onSubmit }: NumerologyConsoleProps) {
  const [state, setState] = useState<ConsoleState>(EMPTY);

  function patch(next: Partial<ConsoleState>): void {
    setState((prev) => ({ ...prev, ...next }));
  }

  const incomplete = state.fullName.trim() === '' || state.birthDate === '';

  function submit(next: ConsoleState): void {
    if (next.fullName.trim() === '' || next.birthDate === '') {
      return;
    }
    onSubmit(requestOf(next));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    submit(state);
  }

  function toggleYAsVowel(checked: boolean): void {
    const next = { ...state, yAsVowel: checked };
    setState(next);
    if (hasChart) {
      submit(next);
    }
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
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">
                数字命理全景矩阵
              </h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                pythagorean · 1–9 字母映射
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              六个核心数、四顶峰与四挑战、个人年月日、姓名天赋九宫与生辰洛书九宫，一次推演给全。
              每个数都自带约简账本，拿计算器就能逐行复核 —— 本页不出综合评分，也不出均衡度百分比。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={incomplete || pending}>
          <Icon name="sparkle" size={18} />
          {pending ? '推演中…' : '推演灵数'}
        </button>
      </div>

      <p className="flex items-start gap-2 rounded-element border border-gold/40 bg-gold/10 px-3 py-2 text-xs leading-relaxed text-gold-soft">
        <Icon name="alert" size={14} className="mt-0.5 shrink-0" />
        毕达哥拉斯映射定义在拉丁字母表上，请输入拼音或英文名（如 LU QINGXUAN）。
        汉字没有权威的字母化口径，本系统不代作主张；中文名可另填，仅作回显。
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <LabeledField label="拉丁字母全名（必填，1–80 字）">
          <input
            value={state.fullName}
            onChange={(event) => patch({ fullName: event.target.value })}
            maxLength={80}
            placeholder="如：LU QINGXUAN"
            className="field"
            aria-label="拉丁字母全名"
          />
        </LabeledField>
        <LabeledField label="中文名（选填，仅回显）" hint={<span className="label-caps text-ink-muted">不参与计算</span>}>
          <input
            value={state.nameZh}
            onChange={(event) => patch({ nameZh: event.target.value })}
            maxLength={20}
            placeholder="如：陆青玄"
            className="field"
            aria-label="中文名，仅回显"
          />
        </LabeledField>
        <LabeledField label="公历生日（必填）">
          <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
            <Icon name="calendar" size={16} className="shrink-0 text-ink-muted" />
            <input
              className="numeric w-full bg-transparent text-sm text-ink outline-none"
              type="date"
              value={state.birthDate}
              onChange={(event) => patch({ birthDate: event.target.value })}
              aria-label="公历生日"
            />
          </div>
        </LabeledField>
        <LabeledField
          label="基准日（选填）"
          hint={<span className="label-caps text-ink-muted">留空取今天</span>}
        >
          <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
            <Icon name="clock" size={16} className="shrink-0 text-ink-muted" />
            <input
              className="numeric w-full bg-transparent text-sm text-ink outline-none"
              type="date"
              value={state.referenceDate}
              onChange={(event) => patch({ referenceDate: event.target.value })}
              aria-label="个人周期的基准日"
            />
          </div>
        </LabeledField>
      </div>

      <label className="flex cursor-pointer items-start gap-2 text-sm text-ink-variant">
        <input
          type="checkbox"
          checked={state.yAsVowel}
          onChange={(event) => toggleYAsVowel(event.target.checked)}
          className="mt-0.5 h-4 w-4 accent-[#d4af37]"
        />
        <span className="flex flex-col gap-0.5">
          <span>把 Y 计入元音</span>
          <span className="text-xs leading-relaxed text-ink-muted">
            判据是这个 Y 在音节里当不当元音用：Lynn、Rhythm 的 Y 算元音，Yolanda、Young
            的 Y 算辅音。音节切分无法判定，故默认按辅音；改动会同时移动灵魂冲动数与人格面具数，
            表达数（全字母总和）不变。
          </span>
        </span>
      </label>

      {incomplete ? (
        <p className="label-caps text-ink-muted">拉丁字母全名与公历生日都填了才能推演。</p>
      ) : null}
    </form>
  );
}
