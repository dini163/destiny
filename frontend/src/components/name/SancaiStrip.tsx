import { SourceNote } from '../ui/SourceNote';
import { wuxingBg, wuxingLabelEn, wuxingText } from '../../lib/wuxing';
import type { NameGrid, Sancai } from '../../types/name';

const ORDER = ['tian', 'ren', 'di'] as const;

/**
 * 三才配置生克条纹图（PRD §6.5）。
 *
 * 只报生/克/比关系与由此推导的档位——不引入 125 行手抄吉凶表（spec 决策四）。
 * 调用方保证 `sancai` 非空，整块缺失时由页面负责不渲染本区。
 */
export function SancaiStrip({ sancai, grids }: { sancai: Sancai; grids: NameGrid[] }) {
  const valueOf = (key: (typeof ORDER)[number]): number | null =>
    grids.find((grid) => grid.key === key)?.value ?? null;

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-3">
        {ORDER.map((key) => {
          const element = sancai.elements[key];
          return (
            <div key={key} className="flex flex-col gap-1.5">
              <span className="label-caps">
                {grids.find((grid) => grid.key === key)?.label ?? key}
              </span>
              <div className="h-2 overflow-hidden rounded-full bg-surface-raised" role="presentation">
                <div className={`h-full ${wuxingBg(element)}`} />
              </div>
              <span className={`text-sm ${wuxingText(element)}`}>
                {element} · {wuxingLabelEn(element)}
              </span>
              <span className="numeric text-xs text-ink-muted">{valueOf(key) ?? '—'}</span>
            </div>
          );
        })}
      </div>

      <ul className="flex flex-col gap-2">
        {sancai.pairs.map((pair) => (
          <li
            key={pair.pair}
            className="flex flex-col gap-1 rounded-element border border-rim bg-surface px-3 py-2"
          >
            <span className="flex items-baseline gap-2">
              <span className="label-caps">{pair.pair}</span>
              <span className="text-sm text-gold-soft">{pair.relation}</span>
            </span>
            <span className="text-xs leading-relaxed text-ink-variant">{pair.verdict}</span>
            <SourceNote source={pair.source} />
          </li>
        ))}
      </ul>

      <p className="text-xs text-ink-muted">
        三才档位 <span className="text-gold-soft">{sancai.tier}</span>
        ，按三对关系中「生 / 比」与「克」的计数划分（模型参数，非古籍定级）。
      </p>
    </div>
  );
}
