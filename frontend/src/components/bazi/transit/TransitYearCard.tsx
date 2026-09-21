import { PillarCard } from '../PillarCard';
import { RelationChips } from '../RelationChips';
import { ShenShaList } from '../ShenShaList';
import { ResultCard } from '../../ui/ResultCard';
import { ScoreLedger } from '../../ui/ScoreLedger';
import { SourceNote } from '../../ui/SourceNote';
import { TransitFiredList } from './TransitFiredList';
import { TransitMonthStrip } from './TransitMonthStrip';
import type { TransitYear } from '../../../types/baziTransit';

/**
 * 单年详批：合成柱、气数账本、命中断语、十神古籍与三张岁运扫描明细。
 *
 * 三张明细（`relations` / `shensha` / `branch_groups`）在响应里已筛过，只含岁运落点
 * （一端为 `extra0`）的条目，命局自有的关系不在其中 —— 所以空数组是"这一年确实没有"，
 * 整块不渲染，不给它补一句"未构成刑冲合害"（那句话在本命盘页说的是另一件事）。
 *
 * 十神不计分（spec §6.3）：它单独一块只印《渊海子平》原句，加减分一律在账本里。
 */
export function TransitYearCard({ year }: { year: TransitYear }) {
  return (
    <ResultCard
      eyebrow={`${year.year} 流年 · 虚岁 ${year.age}`}
      title={`${year.pillar.ganzhi}年`}
      icon="timeline"
      elevated
      actions={
        <span className="label-caps text-ink-muted">
          {year.dayun_ganzhi ? `大运 ${year.dayun_ganzhi}` : '未起运'}
        </span>
      }
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <PillarCard pillar={year.pillar} />
        <div className="flex flex-col gap-4">
          <ScoreLedger score={year.score} label="岁运气数" />
          <p className="text-sm leading-relaxed text-ink-variant">{year.narrative}</p>
        </div>
      </div>

      <div className="gold-rule" />

      <div className="flex flex-col gap-3">
        <span className="label-caps text-ink-muted">命中详单</span>
        <TransitFiredList rows={year.fired} />
      </div>

      <div className="flex flex-col gap-3">
        <span className="label-caps text-ink-muted">流年之干论十神</span>
        <div className="flex flex-col gap-1.5 rounded-element bg-[#0e111a] px-3 py-2.5">
          <span className="font-display text-base text-ink">{year.ten_god.god}</span>
          <p className="text-sm leading-relaxed text-ink-variant">{year.ten_god.meaning}</p>
          <span className="self-end">
            <SourceNote source={year.ten_god.source} />
          </span>
        </div>
      </div>

      {year.relations.length > 0 || year.branch_groups.length > 0 ? (
        <div className="flex flex-col gap-3">
          <span className="label-caps text-ink-muted">岁运与原局的刑冲合害</span>
          <RelationChips relations={year.relations} groups={year.branch_groups} />
        </div>
      ) : null}

      {year.shensha.length > 0 ? (
        <div className="flex flex-col gap-3">
          <span className="label-caps text-ink-muted">岁运落点神煞</span>
          <ShenShaList entries={year.shensha} />
        </div>
      ) : null}

      {year.months ? (
        <div className="flex flex-col gap-3">
          <span className="label-caps text-ink-muted">十二节气月</span>
          <TransitMonthStrip months={year.months} />
        </div>
      ) : null}
    </ResultCard>
  );
}
