

import { Icon } from '../ui/Icon';
import { useI18n } from '../../i18n/context';
import type {
  EvidenceConfidence,
  ReportEvidenceCard,
  ReportSection,
} from '../../types/report';

/** 置信度徽标的配色：high 金 / medium 中性 / low 蓝紫（与 VerdictCard 同一套星级配色逻辑）。 */
const CONFIDENCE_TONE: Record<EvidenceConfidence, string> = {
  high: 'text-gold-bright border-gold/30',
  medium: 'text-ink border-rim',
  low: 'text-sky-300 border-sky-400/30',
};

const CONFIDENCE_LABEL: Record<EvidenceConfidence, string> = {
  high: '模型账本',
  medium: '传统规则解释',
  low: '综合建议',
};

/** 摘要章的一条「标签：值」：按后端拼好的第一个全角冒号拆成两段渲染。 */
function SummaryLine({ line }: { line: string }) {
  const split = line.indexOf('：');
  if (split <= 0) return <li className="text-sm leading-relaxed text-ink">{line}</li>;
  return (
    <li className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
      <span className="label-caps shrink-0 pt-0.5 text-gold">{line.slice(0, split)}</span>
      <span className="text-sm leading-relaxed text-ink">{line.slice(split + 1)}</span>
    </li>
  );
}

/** 一张证据卡：结论 / 盘面依据 / 出处 / 置信度 / 可推翻句。 */
function EvidenceCard({ card }: { card: ReportEvidenceCard }) {
  const { t } = useI18n();
  return (
    <details className="report-evidence rounded-element border border-rim-soft bg-[var(--field-bg)] px-3 py-2.5">
      <summary className="flex w-full items-center justify-between gap-2 text-left">
        <p className="text-sm font-medium leading-relaxed text-ink">{card.claim}</p>
        <span
          className={`shrink-0 rounded-full border px-2 py-0.5 text-[11px] leading-none ${CONFIDENCE_TONE[card.confidence]}`}
        >
          {t(CONFIDENCE_LABEL[card.confidence])}
        </span>
      </summary>
      <div className="evidence-body">
        <dl className="mt-2 flex flex-col gap-1.5 border-t border-rim-soft pt-2 text-xs text-ink-variant">
          <div>
            <dt className="label-caps text-ink-variant">{t('盘面依据')}</dt>
            <dd className="mt-0.5 leading-relaxed">{card.chart_fact}</dd>
          </div>
          <div>
            <dt className="label-caps text-ink-variant">{t('出处')}</dt>
            <dd className="mt-0.5">{card.source}</dd>
          </div>
          <div>
            <dt className="label-caps text-ink-variant">{t('如何被推翻')}</dt>
            <dd className="mt-0.5 leading-relaxed">{card.falsifier}</dd>
          </div>
        </dl>
      </div>
    </details>
  );
}

/**
 * 报告的一章：按章节类型选择渲染形状（摘要=标签条目、主体=段落+要点、边界=单段声明）。
 * 证据卡默认折叠，点开看依据与可推翻句 —— 报告写作纪律「每条结论必须有依据」的展示面。
 */
export function ReportSectionCard({ section, index }: { section: ReportSection; index: number }) {
  const { id, title, kind } = section;
  return (
    <section
      className="report-section flex flex-col gap-3 rounded-card border border-gold/15 bg-gradient-to-b from-surface to-[var(--field-bg)] p-4 sm:p-5"
      aria-labelledby={`report-${id}`}
    >
      <div className="flex items-baseline gap-2.5">
        <span className="numeric text-sm text-gold">{String(index + 1).padStart(2, '0')}</span>
        <h2 id={`report-${id}`} className="font-display text-lg font-semibold tracking-wide text-ink">
          {title}
        </h2>
        {kind === 'action' ? (
          <Icon name="sparkle" size={14} className="text-gold" />
        ) : null}
      </div>

      {section.body.length > 0 ? (
        <div className="flex flex-col gap-2.5">
          {section.body.map((paragraph) => (
            <p key={paragraph} className="text-sm leading-relaxed text-ink">
              {paragraph}
            </p>
          ))}
        </div>
      ) : null}

      {section.bullets.length > 0 ? (
        kind === 'summary' ? (
          <ul className="flex flex-col gap-2.5">
            {section.bullets.map((line) => (
              <SummaryLine key={line} line={line} />
            ))}
          </ul>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {section.bullets.map((bullet) => (
              <li key={bullet} className="flex items-start gap-2 text-sm leading-relaxed text-ink">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold/70" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        )
      ) : null}

      {section.evidence_cards.length > 0 ? (
        <div className="mt-1 flex flex-col gap-1.5 border-t border-rim-soft pt-2.5">
          {section.evidence_cards.map((card) => (
            <EvidenceCard key={card.claim_id} card={card} />
          ))}
        </div>
      ) : null}
    </section>
  );
}
