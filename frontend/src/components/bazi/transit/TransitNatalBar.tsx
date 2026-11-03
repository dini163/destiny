import { PillarCard } from '../PillarCard';
import { ResultCard } from '../../ui/ResultCard';
import { wuxingChip } from '../../../lib/wuxing';
import type { BaziTransitResult } from '../../../types/baziTransit';

/** 本页要用的那半份命局摘要：岁运不重判喜忌，一切照主命盘的合并结果。 */
type NatalSummary = Pick<
  BaziTransitResult,
  'pillars' | 'day_master' | 'day_master_element' | 'favorable_elements' | 'unfavorable_elements'
>;

/**
 * 页顶命局条：本命四柱 + 日主 + 喜忌。
 *
 * 岁运的每一分都是从这份喜忌上算出来的（`yongshen` 族直接取 `favorable_elements`
 * 与 `unfavorable_elements`），所以它必须压在年表之上，读者才知道下面的加减以谁为准。
 * 藏干账本行不在岁运响应里（那是主命盘的账），故 `PillarCard` 回落为裸藏干列表。
 */
export function TransitNatalBar({ natal }: { natal: NatalSummary }) {
  return (
    <ResultCard
      title="推演所据的命局"
      icon="compass"
      actions={
        <span className="flex flex-wrap items-center gap-x-4 gap-y-2">
          <ElementChips label="日主" elements={[`${natal.day_master}·${natal.day_master_element}`]} />
          <ElementChips label="喜用" elements={natal.favorable_elements} tinted />
          <ElementChips label="忌神" elements={natal.unfavorable_elements} tinted />
        </span>
      }
    >
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {natal.pillars.map((pillar) => (
          <PillarCard key={pillar.position} pillar={pillar} />
        ))}
      </div>
    </ResultCard>
  );
}

/** One caption plus its elements; 日主 carries no tint because it isn't a verdict. */
function ElementChips({
  label,
  elements,
  tinted,
}: {
  label: string;
  elements: string[];
  tinted?: boolean;
}) {
  return (
    <span className="flex items-center gap-2">
      <span className="label-caps text-ink-muted">{label}</span>
      <span className="flex flex-wrap items-center gap-1.5">
        {elements.map((element) => (
          <span
            key={element}
            className={`rounded-element px-2 py-0.5 text-xs ${
              tinted ? wuxingChip(element) : 'bg-surface-raised text-ink'
            }`}
          >
            {element}
          </span>
        ))}
      </span>
    </span>
  );
}
