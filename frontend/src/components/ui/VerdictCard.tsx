import { Icon } from './Icon';
import type { Verdict } from '../../types/common';

/**
 * 结论卡片（2026-10-21 verdict-card spec §6）：档位 + 星级 + 结论句 + 分项要点 + 一句建议。
 *
 * 纯展示件，一个字也不写：五个字段全部来自后端 `Verdict`。颜色按 `stars` 派生而非按档位词表
 * （星级 ≥4 金色、=3 中性、≤2 火色）——各系统档位词不同，颜色只认星级，组件就不需要认识
 * 任何系统的词表。挂载点在各系统详批区顶部（结论先行）；体量纪律见 AGENTS §2 不变式 6。
 */
export function VerdictCard({ verdict }: { verdict: Verdict }) {
  const tone =
    verdict.stars >= 4 ? 'text-gold-bright' : verdict.stars === 3 ? 'text-ink' : 'text-wuxing-fire';
  const stars = '★★★★★'.slice(0, verdict.stars) + '☆☆☆☆☆'.slice(0, 5 - verdict.stars);

  return (
    <section className="flex flex-col gap-3 rounded-card border border-gold/25 bg-gradient-to-br from-[#141823] to-[#0e111a] p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <span className="label-caps">综合结论</span>
          <span className={`font-display text-3xl font-bold tracking-wide ${tone}`}>{verdict.grade}</span>
        </div>
        <span
          className="numeric text-lg tracking-widest text-gold-soft"
          aria-label={`${verdict.stars} 星`}
        >
          {stars}
        </span>
      </div>
      <p className="font-display text-sm leading-relaxed text-ink">{verdict.headline}</p>
      {verdict.points.length > 0 ? (
        <ul className="flex flex-wrap gap-1.5">
          {verdict.points.map((point) => (
            <li
              key={point}
              className="rounded-element border border-rim bg-[#0e111a] px-2.5 py-1 text-xs text-ink-variant"
            >
              {point}
            </li>
          ))}
        </ul>
      ) : null}
      <div className="flex items-start gap-2 rounded-element border border-rim-soft bg-[#0e111a] px-3 py-2.5">
        <Icon name="sparkle" size={16} className="mt-0.5 shrink-0 text-gold" />
        <p className="text-sm leading-relaxed text-ink">{verdict.advice}</p>
      </div>
    </section>
  );
}
