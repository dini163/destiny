import { PlainProse } from '../ui/PlainProse';
import { SourceNote } from '../ui/SourceNote';
import { wuxingChip, wuxingLabelEn } from '../../lib/wuxing';
import type { NameFortune, NameGrid } from '../../types/name';

/** 吉凶档位的色调：设计稿只有四级，颜色不引入第五级。 */
const FORTUNE_TONE: Record<NameFortune, string> = {
  大吉: 'border-wuxing-wood/40 bg-wuxing-wood/10 text-wuxing-wood',
  吉: 'border-gold/40 bg-gold/10 text-gold-bright',
  半吉: 'border-wuxing-earth/40 bg-wuxing-earth/10 text-wuxing-earth',
  凶: 'border-wuxing-fire/40 bg-wuxing-fire/10 text-wuxing-fire',
};

/**
 * 五格剖象全景图谱（设计稿同名区块）。
 *
 * 卡片顺序与 `grids` 一致（后端固定 天→人→地→外→总），算式与结果并排显示，
 * 使"这一格怎么来的"在卡面上就能核对；缺笔画的卡只显算式里的 `?`，不显数字。
 * 阅读顺序按 spec §10 的清单类版式就地嵌：每格白话（`grid.plain`）在上，专业判语
 * （`grid.verdict`）降为下方小字。未核定那一格说什么由语料 `name.unresolved` 决定，
 * 本件不现编文案——本件只决定顺序，不决定句子。
 */
export function FiveGrids({ grids }: { grids: NameGrid[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
      {grids.map((grid) => (
        <article
          key={grid.key}
          className="flex flex-col gap-2 rounded-element border border-rim bg-surface p-3"
        >
          <header className="flex items-baseline justify-between gap-2">
            <span className="label-caps">{grid.label}</span>
            {grid.fortune ? (
              <span
                className={`label-caps rounded-element border px-1.5 py-0.5 ${FORTUNE_TONE[grid.fortune]}`}
              >
                {grid.fortune}
              </span>
            ) : null}
          </header>

          <p className="numeric text-sm text-ink-variant">
            {grid.formula}
            <span className="text-ink-muted">=</span>
            <span className="text-gold-bright">{grid.value ?? '?'}</span>
          </p>

          {grid.wuxing ? (
            <div className="flex flex-wrap items-center gap-1.5">
              <span className={`label-caps rounded-element px-1.5 py-0.5 ${wuxingChip(grid.wuxing)}`}>
                {grid.yinyang}
                {grid.wuxing}
                <span className="ml-1 opacity-70">{wuxingLabelEn(grid.wuxing)}</span>
              </span>
              {grid.number !== null ? (
                <span className="numeric text-xs text-ink-muted">数理 {grid.number}</span>
              ) : null}
            </div>
          ) : null}

          {grid.pattern_name ? (
            <p className="font-display text-sm text-ink">{grid.pattern_name}</p>
          ) : null}

          <PlainProse text={grid.plain} />
          {grid.verdict ? (
            <p className="text-xs leading-relaxed text-ink-variant">{grid.verdict}</p>
          ) : null}
          <div className="mt-auto pt-1">
            <SourceNote source={grid.source} />
          </div>
        </article>
      ))}
    </div>
  );
}
