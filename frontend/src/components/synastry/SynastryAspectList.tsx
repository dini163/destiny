import { useState } from 'react';

import { SegmentedControl } from '../ui/SegmentedControl';
import { aspectStyle } from '../../lib/astro';
import { natureStyle } from '../../lib/transit';
import type { SynastryAspect } from '../../types/synastry';

type Filter = 'counted' | 'all';

const FILTER_OPTIONS: ReadonlyArray<{ value: Filter; label: string }> = [
  { value: 'counted', label: '计入相契度' },
  { value: 'all', label: '全部' },
];

interface SynastryAspectListProps {
  /** Person-to-person aspects, already tightest-first. */
  aspects: SynastryAspect[];
}

/**
 * Synastry aspect list (人对人相位).
 *
 * Each row reads "甲方 point — aspect — 乙方 point" with the exact orb, the standard
 * nature chip and a 核心 badge for the classic relationship axes. A toggle narrows the
 * 56-ish detected pairs to just the counted ones (both endpoints personal — the rows
 * the score ledger pays for). Colours are presentation only; the type, orb, core and
 * counted flags all come straight from the backend's geometric detection (no-mock rule).
 */
export function SynastryAspectList({ aspects }: SynastryAspectListProps) {
  const [filter, setFilter] = useState<Filter>('counted');
  const shown = filter === 'counted' ? aspects.filter((aspect) => aspect.counted) : aspects;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <SegmentedControl<Filter>
          ariaLabel="相位筛选"
          options={FILTER_OPTIONS}
          value={filter}
          onChange={setFilter}
        />
        <span className="label-caps text-ink-muted">
          {shown.length} / {aspects.length} 条 · 按容许度排序
        </span>
      </div>

      {shown.length === 0 ? (
        <p className="text-sm text-ink-muted">当前经典容许度内，未检出人对人的主要相位。</p>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {shown.map((aspect, index) => {
            const asp = aspectStyle(aspect.type);
            const nat = natureStyle(aspect.nature);
            return (
              <li
                key={`${aspect.point_a}-${aspect.type}-${aspect.point_b}-${index}`}
                className={`flex flex-wrap items-center gap-x-3 gap-y-1 rounded-element border border-rim-soft bg-surface/60 px-3 py-2 ${
                  aspect.counted ? '' : 'opacity-60'
                }`}
              >
                <span className="flex w-[6.5rem] shrink-0 items-center gap-1.5">
                  <span className="label-caps shrink-0 rounded bg-gold/15 px-1 text-gold-soft">甲</span>
                  <span className="text-base leading-none" style={{ color: nat.color }}>
                    {aspect.point_a_glyph}
                  </span>
                  <span className="truncate text-sm text-ink">{aspect.point_a_zh}</span>
                </span>
                <span
                  className="flex shrink-0 items-center gap-1 rounded-full border px-2 py-0.5"
                  style={{ borderColor: `${asp.color}66`, color: asp.color }}
                >
                  <span className="text-sm leading-none">{aspect.glyph}</span>
                  <span className="text-xs">{asp.label}</span>
                </span>
                <span className="shrink-0 text-ink-muted" aria-hidden="true">
                  →
                </span>
                <span className="flex w-[6.5rem] shrink-0 items-center gap-1.5">
                  <span className="label-caps shrink-0 rounded bg-gold/15 px-1 text-gold-soft">乙</span>
                  <span className="truncate text-sm text-ink-variant">{aspect.point_b_zh}</span>
                </span>
                <span className="ml-auto flex shrink-0 items-center gap-2">
                  <span className="numeric text-xs text-ink-muted">容 {aspect.orb.toFixed(2)}°</span>
                  {aspect.core_bond ? (
                    <span className="rounded-full bg-gold/15 px-2 py-0.5 text-xs text-gold">核心</span>
                  ) : null}
                  <span
                    className="rounded-full px-2 py-0.5 text-xs"
                    style={{ backgroundColor: `${nat.color}22`, color: nat.color }}
                  >
                    {nat.label}
                  </span>
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
