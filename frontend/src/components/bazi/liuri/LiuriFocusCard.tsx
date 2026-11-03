import { Link } from 'react-router-dom';

import { PillarCard } from '../PillarCard';
import { RelationChips } from '../RelationChips';
import { ShenShaList } from '../ShenShaList';
import { ResultCard } from '../../ui/ResultCard';
import { ScoreLedger } from '../../ui/ScoreLedger';
import { SourceNote } from '../../ui/SourceNote';
import { TransitFiredList } from '../transit/TransitFiredList';
import type { TransitDayDetail } from '../../../types/baziLiuri';

/**
 * 聚焦日详批：合成日柱、三段账本、命中判语全文、三张岁运扫描明细与全量历注。
 *
 * 账本三段在行名上自带 `（流月）`/`（流日）` 后缀（年段无缀），前端零拼接；同一天在
 * 矩阵格上与这里的分数、档位、命中是同一份账本读出的两个视图，不是两次计算。
 *
 * 三张明细在响应里已筛过，只含岁运落点（一端为 `extra0`）的条目，所以空数组是"这
 * 一天确实没有"，整块不渲染（与 `TransitYearCard` 同一条纪律）。`narrative` 同理：
 * 一条未中时它是空串，那就连段落都不给，不留一行"无判语"。
 *
 * 历注与四书语料视觉上分开：它来自外部历法库，不参与上面那本账的任何一分。
 */
export function LiuriFocusCard({ detail, href }: { detail: TransitDayDetail; href?: string }) {
  return (
    <ResultCard
      title={`${detail.ganzhi}日`}
      icon="sun"
      actions={
        <span className="flex items-baseline gap-3">
          <span className="numeric text-xs text-ink-variant">{detail.solar_date}</span>
          <span className="text-xs text-ink-muted">{detail.lunar_day}</span>
          {href ? (
            <Link
              to={href}
              className="label-caps rounded-element border border-rim px-2 py-1 text-gold-soft transition hover:border-rim-strong"
            >
              看这一刻的十二时辰
            </Link>
          ) : null}
        </span>
      }
    >
      <div className="grid gap-4 lg:grid-cols-[minmax(0,20rem)_minmax(0,1fr)]">
        <PillarCard pillar={detail.pillar} />
        <div className="flex flex-col gap-4">
          <ScoreLedger score={detail.score} label="流日气数" />
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
        <span className="label-caps text-ink-muted">流日之干论十神</span>
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

      <div className="flex flex-col gap-3">
        <span className="label-caps text-ink-muted">通书历注（全量）</span>
        <div className="flex flex-col gap-2 rounded-element bg-[var(--field-bg)] px-3 py-2.5">
          <AlmanacLine prefix="宜" items={detail.almanac.yi} />
          <AlmanacLine prefix="忌" items={detail.almanac.ji} />
        </div>
        <SourceNote source="通书宜忌（外部历法数据，非本仓古籍语料，不参与本页任何计分）" />
      </div>
    </ResultCard>
  );
}

/** 全量一条不漏；`—` 是库给的空，不是没查。 */
function AlmanacLine({ prefix, items }: { prefix: string; items: string[] }) {
  return (
    <span className="flex flex-wrap items-baseline gap-1.5 text-xs leading-relaxed">
      <span className="label-caps text-ink-muted">{prefix}</span>
      {items.length === 0 ? (
        <span className="text-ink-muted">—</span>
      ) : (
        items.map((item) => (
          <span key={item} className="rounded-element bg-surface-raised px-1.5 py-0.5 text-ink-variant">
            {item}
          </span>
        ))
      )}
    </span>
  );
}
