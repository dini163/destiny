import { ReductionLadder } from './ReductionLadder';
import { SourceNote } from '../ui/SourceNote';
import { masterPair, yearRounds } from '../../lib/numerology';
import type { PersonalCycle, PersonalCycles } from '../../types/numerology';

/** 一轮周期共用的读数块：大号数字 + 主数后缀 + 时段 + 释义。 */
function CycleFigure({ cycle, emphasized }: { cycle: PersonalCycle; emphasized: boolean }) {
  const pair = masterPair(cycle.value, cycle.root, cycle.is_master);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline gap-2">
        <span
          className={`numeric leading-none ${
            emphasized ? 'text-4xl font-semibold text-gold-bright' : 'text-2xl font-semibold text-ink'
          }`}
        >
          {pair?.primary ?? '—'}
        </span>
        {pair?.rootSuffix ? (
          <span className="numeric text-base text-gold">{pair.rootSuffix}</span>
        ) : null}
        <span className="numeric text-xs text-ink-muted">{cycle.period}</span>
        {cycle.is_master ? (
          <span className="label-caps rounded-element border border-gold/40 bg-gold/10 px-1.5 py-0.5 text-gold-bright">
            主数
          </span>
        ) : null}
      </div>
      <p
        className={`leading-relaxed ${
          emphasized ? 'text-sm text-ink' : 'text-xs text-ink-variant'
        }`}
      >
        {cycle.meaning}
      </p>
    </div>
  );
}

/**
 * 个人年 / 月 / 日 + 流年三轮（spec §6.7、决策 11）。
 *
 * 每一轮都把自己的 `steps` 账本印出来：这一页的立身之处是"每个数都能拿计算器复核"，
 * 而个人年月日是链式约简（个人年根 → 加目标月 → 个人月根 → 加目标日），少印一环，
 * 读者就只能相信结论。故这里不为了紧凑而省掉账本，字号收到 11px 就是它的极限。
 *
 * 三轮的次序由 `yearRounds` 挑（前一年 / 今年 / 后一年），当前年另起一块大的：设计稿那个
 * 「2026 (今)」的高亮只认后端给的 `period` 与 `key`，前端不比较日期 —— 基准日是后端定的，
 * 前端再判一次"今天"就等于两处各有一个今天。
 */
export function PersonalCyclePanel({ cycles }: { cycles: PersonalCycles }) {
  const rounds = yearRounds(cycles);

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-12">
        <article className="flex flex-col gap-3 rounded-card border border-gold/40 bg-surface-raised p-4 lg:col-span-5">
          <span className="label-caps text-gold">{cycles.year.label}</span>
          <CycleFigure cycle={cycles.year} emphasized />
          <div className="rounded-element border border-rim bg-[#0e111a] p-2.5">
            <ReductionLadder steps={cycles.year.steps} caption="流年推导演算法" compact />
          </div>
          <div className="mt-auto">
            <SourceNote source={cycles.year.source} />
          </div>
        </article>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:col-span-7">
          {[cycles.month, cycles.day].map((cycle) => (
            <article
              key={cycle.key}
              className="flex flex-col gap-3 rounded-card border border-rim bg-surface p-4"
            >
              <span className="label-caps text-ink-muted">{cycle.label}</span>
              <CycleFigure cycle={cycle} emphasized={false} />
              <div className="rounded-element border border-rim bg-[#0e111a] p-2.5">
                <ReductionLadder steps={cycle.steps} compact />
              </div>
              <div className="mt-auto">
                <SourceNote source={cycle.source} />
              </div>
            </article>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {rounds.map((cycle) => {
          const current = cycle.key === 'year';
          const pair = masterPair(cycle.value, cycle.root, cycle.is_master);
          return (
            <div
              key={cycle.key}
              className={`flex flex-col items-center gap-0.5 rounded-element border p-3 text-center ${
                current ? 'border-gold/60 bg-surface-raised' : 'border-rim bg-surface'
              }`}
            >
              <span className={`label-caps ${current ? 'text-gold' : 'text-ink-muted'}`}>
                {cycle.period}
                {current ? ' (今)' : ''}
              </span>
              <span
                className={`numeric text-2xl font-semibold leading-none ${
                  current ? 'text-gold-bright' : 'text-ink-variant'
                }`}
              >
                {pair?.primary ?? '—'}
                {pair?.rootSuffix ? (
                  <span className="ml-0.5 text-sm text-gold">{pair.rootSuffix}</span>
                ) : null}
              </span>
              <span className="text-[11px] leading-snug text-ink-muted">{cycle.meaning}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
