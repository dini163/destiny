import { FutharkCodex } from '../components/runes/FutharkCodex';
import { RuneConsole } from '../components/runes/RuneConsole';
import { RuneShadowCounsel } from '../components/runes/RuneShadowCounsel';
import { RuneStoneGrid } from '../components/runes/RuneStoneGrid';
import { RuneSynthesis } from '../components/runes/RuneSynthesis';
import { Icon } from '../components/ui/Icon';
import { ResultCard } from '../components/ui/ResultCard';
import { VerdictCard } from '../components/ui/VerdictCard';
import { useRunes } from '../hooks/useRunes';
import type { RuneCastResponse } from '../types/runes';

/**
 * 北欧卢恩神谕页（spec §8、plan T8 Step 1）。
 *
 * 装配那七个组件，本页自己不加第八块版面：牌阵的身份（中英文名与一句说明）挂在碑阵那张卡的
 * 标题与额头上，于是 `spread_name_zh` / `spread_name` / `spread_description` 三个下发字段都有
 * 地方落，而不必再立一个只做标题的组件。
 *
 * **所问不另起一格回显**。塔罗那一版在头条条里印了一次「求问」，因为它的综合解读并不领起所问；
 * 而本页的 `synthesis` 第一句就是「以……铸石，所问：……」，再回显一次等于同屏把同一句话印两遍。
 *
 * **没有翻牌交互**，这也是与塔罗页刻意不同的一处：塔罗的牌是背面朝上发下来、由读者逐张翻开，
 * 那个「翻」是它阅读仪式的一部分；卢恩铸石是掷出来就朝上的，石碑上没有背面可翻。硬加一层
 * 逐块点击展开，只会把一次已经完成的抽取伪装成还有待揭示的东西。
 *
 * 本页一个算术都不做：ætt 配比照后端那四行印，枚数取自数组长度而不是另行推算，正逆两面取哪
 * 一面也是后端定的。改控制台任何一项都要再按一次 CAST，理由写在 `RuneConsole` 里。
 */
export function NorseRunesPage() {
  const runes = useRunes();

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <RuneConsole pending={runes.isPending} onSubmit={runes.mutate} />

      {runes.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{runes.error.message}</span>
        </div>
      ) : null}

      {runes.isPending && !runes.data ? (
        <p className="label-caps text-ink-muted">正在铸石…</p>
      ) : null}

      {runes.data ? <RuneResults cast={runes.data} /> : null}
    </div>
  );
}

/** 一次铸石的全部结果，按「碑阵 → 直读 → 阴影参照 → 全典」的阅读次序排。出处块已按 2026-10-21 UI 需求移除。 */
function RuneResults({ cast }: { cast: RuneCastResponse }) {
  return (
    <>
      <ResultCard
        title={cast.spread_name_zh}
        eyebrow={`SPREAD · ${cast.spread_name}`}
        icon="seal"
        elevated
        actions={
          <span className="label-caps text-ink-muted">{cast.stones.length} 枚石碑</span>
        }
      >
        <p className="text-sm leading-relaxed text-ink-muted">{cast.spread_description}</p>
        <RuneStoneGrid
          spreadId={cast.spread_id}
          stones={cast.stones}
          reversibleNote={cast.reversible_note}
        />
      </ResultCard>

      <VerdictCard verdict={cast.verdict} />

      <RuneSynthesis synthesis={cast.synthesis} aettBalance={cast.aett_balance} />

      <RuneShadowCounsel notes={cast.shadow_counsel} />

      <FutharkCodex codex={cast.codex} />
    </>
  );
}
