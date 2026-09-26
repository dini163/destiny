import type { QimenChart, QimenPalace } from '../../types/qimen';
import { elementDot, elementText, ganText, luckText, palacePlacement } from '../../lib/qimen';

/**
 * The 洛书九宫 board — a 3×3 grid laid 南上北下, each cell carrying the four plates
 * (神盘八神 · 天盘九星与三奇六仪 · 人盘八门 · 地盘干) exactly as the engine rotated
 * them. The 中五宫 renders specially (无门无神, 天禽与中宫地盘干寄坤二). Nothing here
 * is invented: every star, door, god and 干 is read straight from the response.
 */
export function QimenBoard({ chart }: { chart: QimenChart }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-2 sm:gap-3">
        {chart.palaces.map((palace) => (
          <PalaceCell key={palace.number} palace={palace} />
        ))}
      </div>
      <BoardLegend />
    </div>
  );
}

/** One 洛书宫 cell, positioned on the grid by its 0-based row/col. */
function PalaceCell({ palace }: { palace: QimenPalace }) {
  const style = palacePlacement(palace.row, palace.col);

  if (palace.is_center) {
    return (
      <div
        style={style}
        className="flex min-h-[132px] flex-col items-center justify-center gap-1.5 rounded-card border border-rim-soft bg-[#0d1017] p-2 text-center sm:min-h-[168px] sm:p-3"
      >
        <span className="label-caps text-ink-muted">中五宫 · 土</span>
        <span className={`font-display text-3xl leading-none sm:text-4xl ${ganText(palace.dipan_gan)}`}>
          {palace.dipan_gan}
        </span>
        <span className="text-[10px] leading-snug text-ink-muted sm:text-[11px]">
          天禽星与中宫地盘干
          <br />
          寄坤二宫
        </span>
      </div>
    );
  }

  return (
    <div
      style={style}
      className="flex min-h-[132px] flex-col gap-1 rounded-card border border-rim bg-surface p-1.5 sm:min-h-[168px] sm:gap-1.5 sm:p-2.5"
    >
      {/* 神盘 + 卦宫标识 */}
      <div className="flex items-start justify-between gap-1">
        {palace.god ? (
          <span
            className={`rounded-element px-1 py-0.5 text-[10px] font-semibold leading-none sm:text-xs ${
              palace.god.luck === '吉' ? 'bg-gold/15 text-gold-bright' : 'bg-wuxing-fire/15 text-wuxing-fire'
            }`}
            title={`${palace.god.name} · ${palace.god.nature}`}
          >
            {palace.god.name}
          </span>
        ) : (
          <span />
        )}
        <span className="flex flex-col items-end leading-none">
          <span className="font-display text-sm text-ink sm:text-base">
            {palace.gua}
            <span className="numeric ml-1 text-[10px] text-gold-soft">{palace.number}</span>
          </span>
          <span className="mt-0.5 text-[10px] text-ink-muted sm:text-[11px]">{palace.direction}</span>
        </span>
      </div>

      {/* 天盘九星 */}
      <div className="flex flex-col gap-0.5">
        {palace.stars.map((star) => (
          <span key={star.name} className="flex items-center gap-1 text-[11px] leading-none sm:text-xs">
            <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${elementDot(star.element)}`} />
            <span className={`font-display ${star.is_zhifu ? 'text-gold-bright' : 'text-ink'}`}>{star.name}</span>
            <span className={`text-[10px] ${luckText(star.luck)}`}>{star.luck}</span>
            {star.is_zhifu ? (
              <span className="rounded bg-gold/20 px-0.5 text-[9px] leading-tight text-gold-bright">符</span>
            ) : null}
          </span>
        ))}
      </div>

      {/* 天盘干 / 地盘干 */}
      <div className="flex flex-1 flex-col items-center justify-center rounded-element border border-rim-soft bg-[#0e111a] px-1 py-1">
        <div className="flex items-center gap-1.5">
          {palace.tianpan_gan.map((gan, index) => (
            <span
              key={`${gan}-${index}`}
              className={`font-display text-lg leading-none sm:text-2xl ${ganText(gan)}`}
            >
              {gan}
            </span>
          ))}
        </div>
        <span className="my-0.5 h-px w-full bg-rim-soft" />
        <span className={`font-display text-base leading-none text-ink-muted sm:text-xl ${elementText(palace.element)}`}>
          {palace.dipan_gan}
        </span>
      </div>

      {/* 人盘八门 */}
      {palace.door ? (
        <span className="flex items-center gap-1 text-[11px] leading-none sm:text-xs">
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${elementDot(palace.door.element)}`} />
          <span className={`font-display ${palace.door.is_zhishi ? 'text-astral' : 'text-ink'}`}>{palace.door.name}</span>
          <span className={`text-[10px] ${luckText(palace.door.luck)}`}>{palace.door.luck}</span>
          {palace.door.is_zhishi ? (
            <span className="rounded bg-astral/20 px-0.5 text-[9px] leading-tight text-astral">使</span>
          ) : null}
        </span>
      ) : null}

      {/* 地支 + 空亡 / 驿马 marks */}
      <div className="flex items-center justify-between gap-1">
        <span className="numeric text-[10px] text-ink-muted">{palace.zhi || '—'}</span>
        <span className="flex items-center gap-1">
          {palace.kong ? (
            <span className="rounded bg-surface-raised px-1 text-[9px] leading-tight text-ink-muted">空</span>
          ) : null}
          {palace.ma ? (
            <span className="rounded bg-wuxing-wood/20 px-1 text-[9px] leading-tight text-wuxing-wood">马</span>
          ) : null}
        </span>
      </div>
    </div>
  );
}

/** Colour / mark key so the board reads without guesswork. */
function BoardLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-element border border-rim-soft bg-surface px-3 py-2 text-[11px] text-ink-muted">
      <span className="flex items-center gap-1.5">
        <span className="font-display text-sm text-gold-bright">乙丙丁</span>三奇（金）
      </span>
      <span className="flex items-center gap-1.5">
        <span className="font-display text-sm text-ink-variant">戊己庚辛壬癸</span>六仪
      </span>
      <span className="flex items-center gap-1.5">
        <span className="rounded bg-gold/20 px-1 text-gold-bright">符</span>值符星落宫
      </span>
      <span className="flex items-center gap-1.5">
        <span className="rounded bg-astral/20 px-1 text-astral">使</span>值使门落宫
      </span>
      <span className="flex items-center gap-1.5">
        <span className="rounded bg-surface-raised px-1">空</span>旬空
      </span>
      <span className="flex items-center gap-1.5">
        <span className="rounded bg-wuxing-wood/20 px-1 text-wuxing-wood">马</span>驿马
      </span>
      <span className="flex items-center gap-1.5">
        上为天盘干、下为地盘干，色点标五行
      </span>
    </div>
  );
}
