import { SourceNote } from '../ui/SourceNote';
import { arrangeGrid } from '../../lib/numerology';
import type { LoshuGrid } from '../../types/numerology';

interface LoshuGridPanelProps {
  grid: LoshuGrid;
  /** 回显用：让"这张九宫读的是哪份输入"写在卡面上。 */
  birthDate: string;
}

/**
 * 生辰洛书九宫 + 八平面齐缺清单（spec §6.6、决策 9/10/12）。
 *
 * 与 {@link NameGridPanel} **不共用一个组件**，尽管两处的九宫长得像：它们是两套模型
 * （`LoshuGrid` / `NumberGrid`）、两个传统（印度洛书平面 / 毕达哥拉斯业力课）、两份缺数释义。
 * 合成一个组件就等于邀请后人合成一个模型，而那正是设计稿犯的错 —— 它把两张表印成一张，
 * 于是同时印错了两处（决策 9）。故这里连格位的渲染都各写一份：像，是设计语言的一致；
 * 分开，是数据口径的诚实。
 *
 * 洛书只吃生日的字面数字（决策 10）：`1994-05-14` 取出 `1 9 9 4 0 5 1 4`，0 不计入
 * `total` 但 `zero_count` 如实报。`digits` 一并印出，读者能逐位复核每一格是怎么数出来的；
 * `line_sums` 印出八条线各自的和，于是"这是真洛书"不只藏在后端单测里，响应自己就能被核对。
 */
export function LoshuGridPanel({ grid, birthDate }: LoshuGridPanelProps) {
  const rows = arrangeGrid(grid.cells, grid.layout);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <p className="text-xs leading-relaxed text-ink-muted">
          <span className="label-caps text-gold">来自生日 </span>
          {birthDate} 的字面数字逐位计入；0 不是洛书的数位，故不计入合计，但个数如实报出。
        </p>
        <p className="numeric text-xs text-ink-variant">
          取出的数字：{grid.digits.join(' ')}
          <span className="ml-2 text-ink-muted">
            合计 {grid.total} 个非 0 数字 · 0 出现 {grid.zero_count} 次
          </span>
        </p>
      </div>

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
                } ${cell.digit === 5 ? 'outline outline-1 outline-gold/40' : ''}`}
              >
                <span className={`label-caps ${absent ? 'text-wuxing-fire' : 'text-ink-muted'}`}>
                  {cell.digit === 5 ? `枢纽 (${cell.digit})` : absent ? `缺数 (${cell.digit})` : `数位 ${cell.digit}`}
                </span>
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
                <span
                  className="truncate text-[11px] text-ink-muted"
                  title={cell.tokens.join('、')}
                >
                  {cell.tokens.length > 0 ? cell.tokens.join(' ') : '—'}
                </span>
              </div>
            );
          }),
        )}
      </div>

      <p className="numeric text-[11px] text-ink-muted">
        八条线各自的和：{grid.line_sums.join(' · ')}（恒为 15 —— 幻方性质在响应里就能核对）
      </p>

      <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {grid.planes.map((plane) => (
          <li
            key={plane.key}
            className={`flex flex-col gap-1 rounded-element border p-3 ${
              plane.complete
                ? 'border-gold/40 bg-gold/10'
                : 'border-rim bg-surface-raised'
            }`}
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span
                className={`font-display text-sm font-semibold ${
                  plane.complete ? 'text-gold-bright' : 'text-ink'
                }`}
              >
                {plane.name_zh}
                <span className="label-caps ml-1.5 text-ink-muted">{plane.name_en}</span>
              </span>
              <span
                className={`numeric text-xs ${plane.complete ? 'text-gold' : 'text-wuxing-fire'}`}
              >
                {plane.cells.join('-')}
                {plane.complete ? ' 贯通' : ` 缺 ${plane.missing.join('、')}`}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-ink-variant">{plane.text}</p>
            <SourceNote source={plane.source} />
          </li>
        ))}
      </ul>

      {grid.missing.length > 0 ? (
        <ul className="flex flex-col gap-1.5">
          {grid.missing.map((item) => (
            <li
              key={item.digit}
              className="flex flex-wrap items-baseline gap-x-2 rounded-element border border-wuxing-fire/30 bg-wuxing-fire/5 px-3 py-2"
            >
              <span className="label-caps shrink-0 text-wuxing-fire">缺 {item.digit}</span>
              <span className="text-xs leading-relaxed text-ink-variant">{item.meaning}</span>
              <span className="ml-auto shrink-0">
                <SourceNote source={item.source} />
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="rounded-element border border-rim bg-surface-raised p-3 text-xs text-ink-variant">
          无缺数：1–9 九个数位在这个生日里都至少出现过一次。
        </p>
      )}

      <SourceNote source={grid.source} />
    </div>
  );
}
