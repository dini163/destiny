import { SourceNote } from '../ui/SourceNote';
import { pillarLabel } from '../../lib/pillars';
import type { ShenShaEntry, ShenShaMatch } from '../../types/bazi';

/** 吉凶着色复用五行色板的木/火与中性墨色，不新增色值（spec §8.1）。 */
const QUALITY_CLASS: Record<ShenShaEntry['quality'], string> = {
  吉: 'border-wuxing-wood/40',
  凶: 'border-wuxing-fire/40',
  中性: 'border-rim',
};

const QUALITY_TEXT: Record<ShenShaEntry['quality'], string> = {
  吉: 'text-wuxing-wood',
  凶: 'text-wuxing-fire',
  中性: 'text-ink-muted',
};

export function ShenShaList({ entries }: { entries: ShenShaEntry[] }) {
  if (entries.length === 0) {
    // 空白会被读成 bug，所以如实说明查表口径存在、只是本命未命中。
    return (
      <p className="text-sm text-ink-muted">
        本命四柱未检索到传统神煞命中；神煞为查表口径。
      </p>
    );
  }
  return (
    <ul className="flex flex-col gap-2">
      {entries.map((entry, index) => (
        <ShenShaRow key={`${entry.name}-${index}`} entry={entry} />
      ))}
    </ul>
  );
}

/** One hit: name, quality and landing chips on the summary line; meaning on open. */
function ShenShaRow({ entry }: { entry: ShenShaEntry }) {
  return (
    <li className={`rounded-element border bg-[#0e111a] ${QUALITY_CLASS[entry.quality]}`}>
      <details>
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2 [&::-webkit-details-marker]:hidden">
          <span className="flex items-baseline gap-2">
            <span className="font-display text-base text-ink">{entry.name}</span>
            <span className={`label-caps ${QUALITY_TEXT[entry.quality]}`}>{entry.quality}</span>
          </span>
          <span className="flex flex-wrap items-center justify-end gap-1">
            {entry.matches.map((hit) => (
              <MatchChip key={`${hit.position}-${hit.character}-${hit.at}`} hit={hit} />
            ))}
          </span>
        </summary>
        <div className="flex flex-col gap-2 border-t border-rim px-3 py-2.5">
          <p className="text-sm leading-relaxed text-ink-variant">{entry.meaning}</p>
          <p className="text-xs text-ink-muted">起例锚点：{entry.checked_from}</p>
          <span className="self-end">
            <SourceNote source={entry.source} />
          </span>
        </div>
      </details>
    </li>
  );
}

/** A `日支 · 亥` style landing chip built from the engine's {position, character, at}. */
function MatchChip({ hit }: { hit: ShenShaMatch }) {
  const suffix = hit.at === 'gan' ? '干' : hit.at === 'zhi' ? '支' : '柱';
  return (
    <span
      className="rounded-element border border-rim-strong px-1.5 py-0.5 text-xs text-ink-muted"
      title={hit.position}
    >
      {pillarLabel(hit.position)}
      {suffix} · {hit.character}
    </span>
  );
}
