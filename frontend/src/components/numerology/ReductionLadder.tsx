import { useI18n } from '../../i18n/context';
import type { ReductionStep } from '../../types/numerology';

interface ReductionLadderProps {
  /** 后端账本，逐行照印。 */
  steps: readonly ReductionStep[];
  /** 阶梯标题；设计稿叫「约简运算阶梯 (Recursive Breakdown)」。 */
  caption?: string;
  /** 紧凑档：个人周期那五张卡用它，字号再收一级。 */
  compact?: boolean;
}

/**
 * 约简运算阶梯 —— **直接渲染后端 `steps`，前端一个算术都不做**（决策 5、plan T7 Step 2）。
 *
 * 版式上有一处刻意的克制：每行只印 `total → reduced`，把 `expression` 放在后面当**注脚**，
 * 而不是印成 `expression = total` 这样的等式。原因是账本有两种行，`expression` 注的是
 * 不同的那一侧：
 *
 * * 自动行（`年 1994 → 23`，注 `1+9+9+4`）—— 算式是 `total` 的逐位展开，注的是**右边**；
 * * 相加行（`相加 15 → 6`，注 `5+5+5`）—— 算式被引擎显式覆盖成加数串，注的是**左边**
 *   （引擎原话：默认会把 15 拆成 `1+5`，而读者要验算的是 `5+5+5=15`）。
 *
 * 两种行都真，但只有一个 `=` 号的位置能同时容下它们。前端要分辨就得把算式求值一遍，
 * 那正是决策 5 禁止的"前端重算"。故这里不猜，把三个字段都如实摊开，让读者自己接上。
 *
 * `steps` 为空时返回 null：那是决策 17 的留空卡（如 `Lynn` 的灵魂冲动数），由卡片改印
 * `unavailable_reason`，阶梯不该在此处印一句"无步骤"抢话。
 */
export function ReductionLadder({ steps, caption, compact }: ReductionLadderProps) {
  const { t } = useI18n();
  if (steps.length === 0) {
    return null;
  }
  const size = compact ? 'text-[11px]' : 'text-xs';
  return (
    <div className="flex flex-col gap-1.5">
      {caption ? <span className="label-caps text-ink-muted">{t(caption)}</span> : null}
      <ol className="flex flex-col gap-1">
        {steps.map((step, index) => (
          // 同一 `label` 会连着出现多行（`年 1994→23` 之后还有 `年 23→5`），故 key 带序号。
          <li
            key={`${step.label}#${index}`}
            className={`flex flex-wrap items-baseline gap-x-2 gap-y-0.5 ${size}`}
          >
            <span className="label-caps min-w-[4.5rem] shrink-0 text-ink-muted">{step.label}</span>
            <span className="numeric text-ink-variant">{step.total}</span>
            <span aria-hidden="true" className="text-ink-muted">
              →
            </span>
            <span className="numeric font-semibold text-gold-bright">{step.reduced}</span>
            <span className="numeric ml-auto text-ink-muted" title={t('本行的算式')}>
              {step.expression}
            </span>
            {step.karmic_debt ? (
              <span className="label-caps rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-1.5 py-0.5 text-wuxing-fire">
                {t('业力债')}
              </span>
            ) : null}
          </li>
        ))}
      </ol>
    </div>
  );
}
