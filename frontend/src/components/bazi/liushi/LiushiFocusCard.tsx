import { PillarCard } from '../PillarCard';
import { RelationChips } from '../RelationChips';
import { ShenShaList } from '../ShenShaList';
import { ResultCard } from '../../ui/ResultCard';
import { ScoreLedger } from '../../ui/ScoreLedger';
import { SourceNote } from '../../ui/SourceNote';
import { TransitFiredList } from '../transit/TransitFiredList';
import type { TransitHourDetail } from '../../../types/baziLiushi';

/**
 * 聚焦时辰详批：合成时柱、四段账本、命中判语全文、三张岁运扫描明细。
 *
 * 与 `LiuriFocusCard` 同构，只差两件事：账本多一段（行名自带 `（流时）` 后缀，前端零
 * 拼接），以及**没有历注那一块** —— 宜忌是日粒度内容，挂到时辰上等于本系统替通书做拆分
 * （决策 13）。十神、关系、神煞三块照旧：它们在响应里已筛过，只含岁运落点（一端为
 * `extra0`）的条目，所以空数组是"这一刻确实没有"，整块不渲染。
 */
export function LiushiFocusCard({ detail }: { detail: TransitHourDetail }) {
  return (
    <ResultCard
      eyebrow="FOCUSED HOUR"
      title={`${detail.ganzhi}时`}
      icon="clock"
      actions={
        <span className="flex items-baseline gap-3">
          <span className="numeric text-xs text-ink-variant">
            {detail.start_clock}–{detail.end_clock}
          </span>
          <span className="text-xs text-ink-muted">日主临时支·{detail.qi_strength}</span>
        </span>
      }
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <PillarCard pillar={detail.pillar} />
        <div className="flex flex-col gap-4">
          <ScoreLedger score={detail.score} label="流时气数" />
          {detail.narrative ? (
            <p className="text-sm leading-relaxed text-ink-variant">{detail.narrative}</p>
          ) : null}
        </div>
      </div>

      <div className="gold-rule" />

      <div className="flex flex-col gap-3">
        <span className="label-caps text-ink-muted">命中详单</span>
        <TransitFiredList rows={detail.fired} />
      </div>

      <div className="flex flex-col gap-3">
        <span className="label-caps text-ink-muted">流时之干论十神</span>
        <div className="flex flex-col gap-1.5 rounded-element bg-[var(--field-bg)] px-3 py-2.5">
          <span className="font-display text-base text-ink">{detail.ten_god.god}</span>
          <p className="text-sm leading-relaxed text-ink-variant">{detail.ten_god.meaning}</p>
          <span className="self-end">
            <SourceNote source={detail.ten_god.source} />
          </span>
        </div>
      </div>

      {detail.relations.length > 0 || detail.branch_groups.length > 0 ? (
        <div className="flex flex-col gap-3">
          <span className="label-caps text-ink-muted">岁运与原局的刑冲合害</span>
          <RelationChips relations={detail.relations} groups={detail.branch_groups} />
        </div>
      ) : null}

      {detail.shensha.length > 0 ? (
        <div className="flex flex-col gap-3">
          <span className="label-caps text-ink-muted">岁运落点神煞</span>
          <ShenShaList entries={detail.shensha} />
        </div>
      ) : null}
    </ResultCard>
  );
}
