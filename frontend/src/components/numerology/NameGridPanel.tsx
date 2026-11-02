import { SourceNote } from '../ui/SourceNote';
import { arrangeGrid } from '../../lib/numerology';
import type { NumberGrid } from '../../types/numerology';

interface NameGridPanelProps {
  grid: NumberGrid;
  /** 回显用：让"这张九宫读的是哪份输入"写在卡面上。 */
  fullName: string;
}

/**
 * 姓名天赋九宫 + 业力课条（spec §6.5、决策 9）。
 *
 * 与 {@link LoshuGridPanel} **刻意分成两个组件**：输入不同（姓名字母 vs 生日数字）、传统
 * 不同（毕达哥拉斯业力课 vs 洛书平面）、缺数释义也不同。合成一张表就是设计稿犯的那个错，
 * 它因此同时印错了两处。故本件只认 `NumberGrid`，一个洛书字段都不碰。
 *
 * 摆法来自后端的 `layout`（决策 12）：真洛书是 `4 9 2 / 3 5 7 / 8 1 6`，前端自己按数字升序
 * 排就会排出设计稿那个非幻方的摆法。
 *
 * `count === 0` 的格用告警色 + 虚线框，并且**照样印出那个 0**：0 在九宫里不是缺失值，
 * 「这个数一次都没出现」本身就是业力课，是结论。格位为 `undefined` 时印「契约缺格」——
 * 后端保证 `cells` 覆盖 1..9 且 `layout` 是它的一个排列，正常到不了这一支，真到了就该看得见。
 */
export function NameGridPanel({ grid, fullName }: NameGridPanelProps) {
  const rows = arrangeGrid(grid.cells, grid.layout);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-xs leading-relaxed text-ink-muted">
        <span className="label-caps text-gold">来自姓名 </span>
        {fullName} 的拉丁字母逐字计入；计数合计 {grid.total} 恒等于参与计算的字母数
        （非字母字符由引擎跳过并另行如实报数）。
      </p>

      <div className="grid grid-cols-3 gap-2 rounded-card border border-rim bg-[var(--field-bg)] p-3">
        {rows.map((row, rowIndex) =>
          row.map((cell, colIndex) => {
            if (!cell) {
              return (
                <div
                  key={`hole-${rowIndex}-${colIndex}`}
                  className="flex h-24 items-center justify-center rounded-element border border-dashed border-wuxing-fire/40 text-xs text-wuxing-fire"
                >
                  契约缺格
                </div>
              );
            }
            const absent = cell.count === 0;
            return (
              <div
                key={cell.digit}
                className={`flex h-24 flex-col justify-between rounded-element p-2.5 ${
                  absent
                    ? 'border border-dashed border-wuxing-fire/50 bg-wuxing-fire/5'
                    : 'border border-rim bg-surface-raised'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`label-caps ${absent ? 'text-wuxing-fire' : 'text-ink-muted'}`}>
                    {absent ? `业力课缺 (${cell.digit})` : `数位 ${cell.digit}`}
                  </span>
                </div>
                <div className="flex items-end justify-between gap-1">
                  <span
                    className={`numeric text-2xl font-semibold leading-none ${
                      absent ? 'text-ink-muted' : 'text-gold-bright'
                    }`}
                  >
                    {cell.digit}
                  </span>
                  <span
                    className={`numeric text-xs ${absent ? 'text-wuxing-fire' : 'text-ink-variant'}`}
                  >
                    {absent ? '缺失 · 0 次' : `× ${cell.count} 次`}
                  </span>
                </div>
                <span className="numeric truncate text-[11px] text-ink-muted" title={cell.tokens.join('、')}>
                  {cell.tokens.length > 0 ? cell.tokens.join(' ') : '—'}
                </span>
              </div>
            );
          }),
        )}
      </div>

      {grid.karmic_lessons.length > 0 ? (
        <ul className="flex flex-col gap-2">
          {grid.karmic_lessons.map((lesson) => (
            <li
              key={lesson.digit}
              className="flex flex-col gap-1 rounded-element border border-wuxing-fire/30 bg-wuxing-fire/5 p-3"
            >
              <span className="label-caps text-wuxing-fire">
                业力课 {lesson.digit} · Karmic Lesson
              </span>
              <p className="text-xs leading-relaxed text-ink-variant">{lesson.meaning}</p>
              <SourceNote source={lesson.source} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="rounded-element border border-rim bg-surface-raised p-3 text-xs text-ink-variant">
          无业力课：1–9 九个数位在这份姓名里都至少出现过一次。
        </p>
      )}

      <SourceNote source={grid.source} />
    </div>
  );
}
