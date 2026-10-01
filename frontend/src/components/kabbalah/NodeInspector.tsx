import type { ReactNode } from 'react';

import type { PathNode, SephirahNode } from '../../types/kabbalah';
import { pillarAccent } from '../../lib/kabbalah';
import { Icon } from '../ui/Icon';
import { PlainProse } from '../ui/PlainProse';

/** The resolved selection handed to the inspector. */
export type Resolved =
  | { kind: 'sephirah'; node: SephirahNode }
  | { kind: 'path'; node: PathNode }
  | null;

/** A caption + value row used across both inspector variants. */
function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-rim-soft/60 py-1.5 last:border-0">
      <span className="label-caps shrink-0 text-ink-muted">{label}</span>
      <span className="text-right text-sm text-ink-variant">{children}</span>
    </div>
  );
}

/**
 * Full detail of whichever node is selected on the Tree — a Sephirah (原质) or a
 * Path (路径). Every field is read straight from the engine's curated content.
 */
export function NodeInspector({ resolved }: { resolved: Resolved }) {
  if (resolved === null) {
    return <p className="text-sm text-ink-muted">点击生命之树上的原质或路径，查看其完整对应。</p>;
  }
  return resolved.kind === 'sephirah' ? (
    <SephirahDetail node={resolved.node} />
  ) : (
    <PathDetail node={resolved.node} />
  );
}

function SephirahDetail({ node }: { node: SephirahNode }) {
  const accent = pillarAccent(node.pillar);
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3.5">
        <span
          className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-2 font-display text-xl font-semibold text-[#0b0e16]"
          style={{ backgroundColor: node.color, borderColor: accent }}
        >
          {node.is_hidden ? '✧' : node.number}
        </span>
        <div className="flex flex-col gap-1">
          <span className="label-caps" style={{ color: accent }}>
            {node.is_hidden ? '隐藏原质 · DAATH' : `第 ${node.number} 原质 · SEPHIRAH`}
          </span>
          <span className="font-display text-2xl font-semibold text-ink">{node.name_zh}</span>
          <span className="text-sm text-ink-muted">
            {node.name} · <span className="text-gold-soft">{node.name_hebrew}</span>
          </span>
        </div>
      </div>

      <PlainProse text={node.plain_meaning} />

      <p className="text-xs leading-relaxed text-ink-muted">{node.meaning}</p>

      <div className="flex flex-wrap gap-1.5">
        {node.keywords.map((keyword) => (
          <span key={keyword} className="rounded-element border border-rim-soft bg-surface px-2 py-0.5 text-xs text-ink-variant">
            {keyword}
          </span>
        ))}
      </div>

      <div className="gold-rule" />

      <div className="flex flex-col">
        <Row label="三柱">{node.pillar_name_zh}</Row>
        <Row label="四界">{node.world_name_zh}</Row>
        <Row label="行星守护">{node.sphere}</Row>
        <Row label="大天使">{node.archangel}</Row>
        <Row label="神名">{node.divine_name}</Row>
        <Row label="王徽色">
          <span className="inline-flex items-center gap-2">
            <span className="h-3 w-3 rounded-full border border-rim" style={{ backgroundColor: node.color }} />
            <span className="numeric text-xs">{node.color.toUpperCase()}</span>
          </span>
        </Row>
      </div>
    </div>
  );
}

function PathDetail({ node }: { node: PathNode }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3.5">
        <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-2 border-gold bg-gold/10 font-display text-2xl text-gold">
          {node.letter}
        </span>
        <div className="flex flex-col gap-1">
          <span className="label-caps text-gold-soft">第 {node.number} 路径 · PATH</span>
          <span className="font-display text-2xl font-semibold text-ink">
            {node.tarot_zh} <span className="text-base text-ink-muted">{node.tarot_numeral}</span>
          </span>
          <span className="text-sm text-ink-muted">
            {node.letter_name} {node.letter_zh} · gematria {node.letter_value}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-element border border-rim-soft bg-surface/50 px-3 py-2 text-sm">
        <Icon name="arrowRight" size={16} className="shrink-0 text-gold" />
        <span className="text-ink-variant">
          <span className="text-gold-soft">{node.from_name_zh}</span>
          <span className="mx-1.5 text-ink-muted">→</span>
          <span className="text-gold-soft">{node.to_name_zh}</span>
        </span>
        <span className="ml-auto text-xs text-ink-muted">{node.correspondence}</span>
      </div>

      <PlainProse text={node.plain_meaning} />

      <p className="text-xs leading-relaxed text-ink-muted">{node.meaning}</p>

      <div className="gold-rule" />

      <div className="flex flex-col">
        <Row label="塔罗大阿卡纳">
          {node.tarot_zh} <span className="text-ink-muted">({node.tarot} {node.tarot_numeral})</span>
        </Row>
        <Row label="希伯来字母">
          {node.letter} {node.letter_name} · {node.letter_zh}
        </Row>
        <Row label="字母数值">{node.letter_value}</Row>
        <Row label="行星 / 星座 / 元素">{node.correspondence}</Row>
      </div>
    </div>
  );
}
