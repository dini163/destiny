import { useState } from 'react';
import type { FormEvent } from 'react';

import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { SegmentedControl } from '../ui/SegmentedControl';
import type { RuneCastRequest, RuneSpreadId } from '../../types/runes';

/** 表单状态。与 `RuneCastRequest` 同义，只是各字段的形状跟着控件走。 */
interface ConsoleState {
  spreadId: RuneSpreadId;
  includeWyrd: boolean;
  allowReversed: boolean;
  question: string;
}

const EMPTY: ConsoleState = {
  // 与后端 `RuneCastRequest.spread_id` 的默认值一致：三女神阵。
  spreadId: 'three',
  includeWyrd: false,
  allowReversed: true,
  question: '',
};

/** `question` 的上限，逐字对齐后端 `RuneCastRequest.question` 的 `max_length`。 */
const QUESTION_MAX = 120;

/** 状态 → 请求。空着的选填项**不写那个键**，而不是写 `null` 或 `''`。 */
function requestOf(state: ConsoleState): RuneCastRequest {
  return {
    spread_id: state.spreadId,
    include_wyrd: state.includeWyrd,
    allow_reversed: state.allowReversed,
    ...(state.question.trim() === '' ? {} : { question: state.question.trim() }),
  };
}

interface RuneConsoleProps {
  pending: boolean;
  onSubmit: (request: RuneCastRequest) => void;
}

/**
 * 铸石台（spec §8、plan T7 Step 3）。
 *
 * **改动不自动重掷，只有按钮会**。这是它与 `NumerologyConsole` 刻意不同的一处：灵数推演是
 * 确定性的，拨一下开关当场重投只是重算一遍同样的东西；而卢恩每一次铸石都是一次**新的抽取**
 * （后端 `secrets`），让一个开关顺手换掉整批石，等于读者只想看一眼开关却拿到了一份新的
 * 「天意」。故这里改完设置要再按一次 CAST，按钮下方那句提示说的就是这件事。
 *
 * 牌阵三选只印枚数（单枚 / 三枚 / 五枚），**不在前端复制一份牌阵名**：`name_zh` 与位次释义
 * 都在语料里，掷符后随响应下发并由碑阵标题印出。塔罗那一版在前端留了一份 `SPREAD_CATALOG`
 * 并注明「镜像后端」，本轮不照抄 —— 决策 25 拦的正是同一件事（把语料抄进前端 TS 就是
 * 同一份事实存两处，必然漂移），而枚数是 `spread_id` 字面自己的意思，不算语料。
 *
 * 熵源如实写 `secrets`（spec §11 偏差 P）：设计稿那句「通过量子混沌伪随机熵源完成铸石」
 * 是假技术主张，且「伪随机」与同页的 CSPRNG 徽标自相矛盾。徽标也只留决策 18 那四枚 ——
 * 设计稿的 `#RUNES-FUTHARK-2026-N09` 收成 `#RUNES-FUTHARK`（偏差 O），那串流水号无从推导；
 * `100.0% COHERENCE` 与 `DIVINATION HARMONICS: 0.984 TST-ALIGNED` 一并删掉（偏差 H/J），
 * 本页不吃时间与地理入参，没有任何东西可以对齐。
 *
 * 设计稿页头那两枚「存入神谕秘匣 / 导出符印命谱」按钮**不渲染**（偏差 Q，属 Stage 9/10）；
 * 右侧那个 Bindrune 生成器同理（偏差 K）。
 */
export function RuneConsole({ pending, onSubmit }: RuneConsoleProps) {
  const [state, setState] = useState<ConsoleState>(EMPTY);

  function patch(next: Partial<ConsoleState>): void {
    setState((prev) => ({ ...prev, ...next }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit(requestOf(state));
  }

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="seal" size={22} />
          </span>
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">
                北欧卢恩神谕
              </h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                ELDER FUTHARK 24 + WYRD
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="label-caps rounded-element border border-rim bg-surface px-1.5 py-0.5 text-ink-muted">
                CSPRNG
              </span>
              <span className="label-caps rounded-element border border-rim bg-surface px-1.5 py-0.5 text-ink-muted">
                CRYPTO-SEEDED
              </span>
              <span className="label-caps rounded-element border border-rim bg-surface px-1.5 py-0.5 text-ink-muted">
                #RUNES-FUTHARK
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              抽石走 Python <code className="numeric text-gold-soft">secrets</code>（OS 熵源
              CSPRNG），释义全部取自策展语料库。本页不吃出生时间与地点：没有历法、没有星历，
              因此也不出综合评分、不出任何百分比 —— 没有可以推出那类数字的输入。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="sparkle" size={18} />
          {pending ? '铸石中…' : '重新掷符 CAST'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <LabeledField
          label="牌阵（按抽几枚）"
          hint={
            <span className="label-caps text-ink-muted">
              牌阵名与位次释义随响应给出
            </span>
          }
        >
          <SegmentedControl<RuneSpreadId>
            ariaLabel="牌阵"
            value={state.spreadId}
            onChange={(spreadId) => patch({ spreadId })}
            options={[
              { value: 'single', label: '单枚' },
              { value: 'three', label: '三枚' },
              { value: 'five', label: '五枚' },
            ]}
          />
        </LabeledField>

        <LabeledField
          label="求测事项（选填，120 字内）"
          hint={
            <span className="numeric label-caps text-ink-muted">
              {state.question.length}/{QUESTION_MAX}
            </span>
          }
        >
          <input
            value={state.question}
            onChange={(event) => patch({ question: event.target.value })}
            maxLength={QUESTION_MAX}
            placeholder="如：这次换工作该不该走"
            className="field w-full"
            aria-label="求测事项，仅用于回显与领起直读"
          />
        </LabeledField>
      </div>

      <div className="flex flex-col gap-3">
        <label className="flex cursor-pointer items-start gap-2 text-sm text-ink-variant">
          <input
            type="checkbox"
            checked={state.includeWyrd}
            onChange={(event) => patch({ includeWyrd: event.target.checked })}
            className="mt-0.5 h-4 w-4 accent-[#d4af37]"
          />
          <span className="flex flex-col gap-0.5">
            <span>空白符（Wyrd）入牌组</span>
            <span className="text-xs leading-relaxed text-ink-muted">
              它是现代增补的第 25 枚，不见于任何古铭文，故默认关闭。开启后它可能被抽到，
              但不计入三组任何一组；全典里它恒单独成条并另有出处。
            </span>
          </span>
        </label>

        <label className="flex cursor-pointer items-start gap-2 text-sm text-ink-variant">
          <input
            type="checkbox"
            checked={state.allowReversed}
            onChange={(event) => patch({ allowReversed: event.target.checked })}
            className="mt-0.5 h-4 w-4 accent-[#d4af37]"
          />
          <span className="flex flex-col gap-0.5">
            <span>允许逆位（merkstave）</span>
            <span className="text-xs leading-relaxed text-ink-muted">
              字形旋转 180° 后与原形重合的那几枚没有逆位读法，无论这里怎么设都恒正位，
              碑上也不给它们印朝向角标。判据全文在掷符后随碑阵印出。
            </span>
          </span>
        </label>
      </div>

      <p className="label-caps text-ink-muted">
        改动牌阵或两个开关后须再按一次 CAST：每一次铸石都是一次新的抽取，不会照着上一份结果改。
      </p>
    </form>
  );
}
