import type { DayunDirection, DayunStep, LiunianYear } from '../../types/bazi';

interface DayunTimelineProps {
  /** 顺行/逆行, or null when gender was not supplied. */
  direction: DayunDirection | null;
  /** Solar date the first luck pillar begins. */
  startSolar: string | null;
  /** The luck-pillar steps (index 0 is the pre-luck childhood span). */
  steps: DayunStep[];
  /** Annual fortunes within the current luck pillar. */
  liunian: LiunianYear[];
}

/**
 * Luck-pillar (大运) axis with the current annual fortunes (流年).
 *
 * A horizontally scrollable run of ten-year steps — each showing the real ganzhi, age
 * span, year span, 旬 and 空亡 from the engine — with the in-force step highlighted.
 * Step 0 is the pre-luck childhood span (empty ganzhi). No fortune copy is fabricated;
 * only computed cycles are rendered.
 */
export function DayunTimeline({ direction, startSolar, steps, liunian }: DayunTimelineProps) {
  if (steps.length === 0) {
    return (
      <p className="text-sm text-ink-muted">
        未提供性别，无法排定大运顺逆。请在上方选择乾造 / 坤造后重新排盘。
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink-muted">
        <span>
          顺逆：
          <span className="text-gold">
            {direction === 'forward' ? '顺行' : direction === 'backward' ? '逆行' : '—'}
          </span>
        </span>
        {startSolar ? (
          <span>
            起运：<span className="numeric text-ink">{startSolar}</span>
          </span>
        ) : null}
        <span className="label-caps">横向滚动查看 {steps.length} 步大运</span>
      </div>

      <div className="overflow-x-auto pb-2">
        <div className="flex gap-3">
          {steps.map((step) => (
            <DayunCard key={step.index} step={step} />
          ))}
        </div>
      </div>

      {liunian.length > 0 ? (
        <div className="flex flex-col gap-2">
          <span className="label-caps">当前大运 · 流年（{liunian.length} 年）</span>
          <div className="flex flex-wrap gap-2">
            {liunian.map((year) => (
              <span
                key={year.year}
                className="numeric rounded-element border border-rim bg-[#0e111a] px-2.5 py-1 text-xs text-ink-variant"
              >
                {year.year} · {year.age}岁 · <span className="text-gold-soft">{year.ganzhi}</span>
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

/** A single ten-year luck-pillar step; the in-force step is gilded. */
function DayunCard({ step }: { step: DayunStep }) {
  const childhood = step.ganzhi === '';
  return (
    <div
      className={
        step.is_current
          ? 'relative flex w-40 shrink-0 flex-col gap-1 overflow-hidden rounded-card border border-rim-strong bg-surface-raised p-3'
          : 'relative flex w-40 shrink-0 flex-col gap-1 rounded-card border border-rim bg-surface p-3 transition hover:border-rim-strong'
      }
    >
      {step.is_current ? <div className="absolute inset-x-0 top-0 h-1 bg-gold" /> : null}
      <div className="flex items-center justify-between gap-1">
        <span className="numeric text-xs text-ink-muted">
          {step.start_age}–{step.end_age}岁
        </span>
        {step.is_current ? (
          <span className="label-caps rounded-element bg-gold px-1.5 py-0.5 text-[#3c2f00]">当下</span>
        ) : null}
      </div>
      <div className="flex items-baseline gap-2">
        <span
          className={`font-display text-2xl font-semibold ${
            step.is_current ? 'text-gold-bright' : 'text-ink'
          }`}
        >
          {childhood ? '—' : step.ganzhi}
        </span>
        <span className="numeric text-xs text-ink-muted">{step.start_year}</span>
      </div>
      <span className="label-caps">{childhood ? '起运前 · 童年' : `${step.xun}旬`}</span>
      <span className="text-xs text-ink-muted">
        {step.start_year}–{step.end_year} · 空亡 {step.xun_kong || '—'}
      </span>
    </div>
  );
}
