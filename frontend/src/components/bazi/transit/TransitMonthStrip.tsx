import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useI18n } from '../../../i18n/context';
import { Icon } from '../../ui/Icon';
import { ScoreLedger } from '../../ui/ScoreLedger';
import { TransitFiredList } from './TransitFiredList';
import type { TransitMonth } from '../../../types/baziTransit';

/**
 * 聚焦年的十二节气月。
 *
 * 月界取自响应里的 `start_solar` / `end_solar`（立春起寅月，非农历初一，逐段由交节
 * 推出），前端不排节气、也不补"腊月"之外的第 13 段。每段的分数是两段账本之和：
 * 该流年全部命中行 + 该流月命中行（spec §6.4），所以展开账本的前若干行与该年年卡
 * 逐行相同 —— 这是设计而非重复，凶年里的吉月要看得见是谁把分加回来的。
 *
 * 月段行在 `label` 上自带「（流月）」后缀，无需前端再加标记。
 *
 * `hrefFor` 是「看本段逐日」那一条链接：由页面拼好交进来（生辰只在页面上有），本组件
 * 不认识链接层也不认识流日页 —— 不给 hrefFor 就只是少一个入口，月卡本身完好。
 */
export function TransitMonthStrip({
  months,
  hrefFor,
}: {
  months: TransitMonth[];
  hrefFor?: (month: TransitMonth) => string;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {months.map((month) => (
        <MonthCard
          key={`${month.index}-${month.ganzhi}`}
          month={month}
          href={hrefFor ? hrefFor(month) : undefined}
        />
      ))}
    </div>
  );
}

/** One 节气月: caption, date span, ledger and its own fired rows. */
function MonthCard({ month, href }: { month: TransitMonth; href?: string }) {
  const [open, setOpen] = useState(false);
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-3 rounded-element border border-rim bg-[var(--field-bg)] p-4">
      <div className="flex items-baseline justify-between gap-2">
        <span className="flex items-baseline gap-2">
          <span className="font-display text-base text-ink">{t('{{m}}月', { m: month.month_in_chinese })}</span>
          <span className="text-sm text-gold-soft">{month.ganzhi}</span>
        </span>
        <span className="label-caps text-ink-muted">{t(month.pillar.di_shi)}</span>
      </div>

      <p className="numeric text-xs text-ink-muted">
        {month.start_solar} ~ {month.end_solar}
      </p>

      <ScoreLedger score={month.score} label="流月气数" />

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          aria-expanded={open}
          className="label-caps flex items-center gap-1 self-start text-ink-muted hover:text-gold-soft"
        >
          <Icon name="chevronDown" size={12} className={open ? 'rotate-180' : undefined} />
          {open ? t('收起本月命中') : t('展开本月命中 {{n}} 行', { n: month.fired.length })}
        </button>

        {href ? (
          <Link
            to={href}
            className="label-caps flex items-center gap-1 self-start text-ink-muted hover:text-gold-soft"
          >
            <Icon name="calendar" size={12} />
            {t('看本段逐日')}
          </Link>
        ) : null}
      </div>

      {open ? <TransitFiredList rows={month.fired} /> : null}
    </div>
  );
}
