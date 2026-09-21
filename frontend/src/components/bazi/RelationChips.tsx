import { useState } from 'react';

import { SourceNote } from '../ui/SourceNote';
import { Icon } from '../ui/Icon';
import { pillarColumnLabel } from '../../lib/pillars';
import type { BranchGroup, RelationPair } from '../../types/bazi';

/** 紧临 > 隔位 > 远位：力量差别用边框强度表达，不新造色值（spec §8.1）。 */
const STRENGTH_CLASS: Record<RelationPair['strength'], string> = {
  紧临: 'border-rim-strong',
  隔位: 'border-rim',
  远位: 'border-rim-soft',
};

const GROUP_CLASS: Record<BranchGroup['kind'], string> = {
  三合: 'border-rim-strong',
  半合: 'border-rim',
  三会: 'border-rim-strong',
};

/**
 * 刑冲合害破 (binary pairs) plus 三合/半合/三会 (branch groups).
 *
 * The two are listed apart because a 局 spans three pillars and cannot be
 * flattened into a pair (spec §6.3 `BranchGroup`). Relations are grouped by
 * `kind` so "三组六冲" reads as one phenomenon; a group with several pairs
 * collapses to a toggle and the expanded rows carry the engine's own reading.
 */
export function RelationChips({
  relations,
  groups,
}: {
  relations: RelationPair[];
  groups: BranchGroup[];
}) {
  if (relations.length === 0 && groups.length === 0) {
    return <p className="text-sm text-ink-muted">本命四柱之间未构成刑冲合害破或合会局。</p>;
  }
  return (
    <div className="flex flex-col gap-4">
      {groups.length > 0 ? <GroupBlock groups={groups} /> : null}
      {relations.length > 0 ? <PairBlock relations={relations} /> : null}
    </div>
  );
}

/** Binary relations bucketed by kind, keeping first-seen kind order. */
function PairBlock({ relations }: { relations: RelationPair[] }) {
  const kinds: string[] = [];
  for (const relation of relations) if (!kinds.includes(relation.kind)) kinds.push(relation.kind);
  return (
    <div className="flex flex-col gap-3">
      {kinds.map((kind) => (
        <KindRows key={kind} kind={kind} rows={relations.filter((r) => r.kind === kind)} />
      ))}
    </div>
  );
}

/** One kind: a header chip plus its pillar pairs, collapsed past three. */
function KindRows({ kind, rows }: { kind: string; rows: RelationPair[] }) {
  const [open, setOpen] = useState(false);
  const shown = open || rows.length <= 3 ? rows : rows.slice(0, 3);
  return (
    <div className="flex flex-col gap-1.5">
      <span className="label-caps text-ink-muted">
        {kind} · {rows.length}组
      </span>
      <ul className="flex flex-col gap-1.5">
        {shown.map((row, index) => (
          <li
            key={`${row.kind}-${row.pillar_a}-${row.pillar_b}-${index}`}
            className={`flex flex-wrap items-center justify-between gap-2 rounded-element border bg-[#0e111a] px-3 py-2 text-xs ${STRENGTH_CLASS[row.strength]}`}
          >
            <span className="flex items-center gap-1.5 text-ink">
              <span>{row.character_a}</span>
              <span className="text-ink-muted">{pillarColumnLabel(row.pillar_a)}</span>
              <Icon name="arrowRight" size={12} className="text-gold-muted" />
              <span>{row.character_b}</span>
              <span className="text-ink-muted">{pillarColumnLabel(row.pillar_b)}</span>
              <span className="label-caps text-ink-muted">{row.strength}</span>
              {row.transforming_element ? (
                <span className="label-caps text-gold-soft">化气{row.transforming_element}</span>
              ) : null}
            </span>
            <span className="w-full text-ink-variant sm:w-auto sm:max-w-md">{row.reading}</span>
          </li>
        ))}
      </ul>
      {rows.length > 3 ? (
        <button
          type="button"
          onClick={() => setOpen((prev) => !prev)}
          aria-expanded={open}
          className="label-caps flex items-center gap-1 self-start text-ink-muted hover:text-gold-soft"
        >
          <Icon name="chevronDown" size={12} className={open ? 'rotate-180' : undefined} />
          {open ? '收起其余' : `展开其余 ${rows.length - 3} 组`}
        </button>
      ) : null}
    </div>
  );
}

/** 三合/半合/三会 read as members of a frame, not as pairs. */
function GroupBlock({ groups }: { groups: BranchGroup[] }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="label-caps text-ink-muted">合会局</span>
      <ul className="flex flex-col gap-1.5">
        {groups.map((group, index) => (
          <li
            key={`${group.kind}-${group.element}-${index}`}
            className={`flex flex-wrap items-center justify-between gap-2 rounded-element border bg-[#0e111a] px-3 py-2 text-xs ${GROUP_CLASS[group.kind]}`}
          >
            <span className="flex items-center gap-1.5 text-ink">
              <span className="label-caps text-gold-soft">{group.kind}</span>
              <span>{group.element}</span>
              {group.members.map((member) => (
                <span
                  key={`${member.pillar}-${member.branch}`}
                  className="text-ink-muted"
                  title={member.pillar}
                >
                  {member.branch}
                  {pillarColumnLabel(member.pillar)}
                </span>
              ))}
              <span className="label-caps text-ink-muted">
                {group.is_complete ? '三字全' : '三字不全'}
              </span>
            </span>
            <span className="w-full text-ink-variant sm:w-auto sm:max-w-md">{group.reading}</span>
            <span className="self-end">
              <SourceNote source={group.source} />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
