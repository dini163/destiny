import type { CSSProperties } from 'react';

import type { Palace, StarPlacement, ZiweiChart } from '../../types/ziwei';
import {
  CENTER_STYLE,
  palaceGridStyle,
  sihuaClass,
  sihuaShort,
  starKindClass,
} from '../../lib/ziwei';

interface ZiweiChartGridProps {
  /** The complete chart — twelve palaces plus the summary facts for the centre. */
  chart: ZiweiChart;
}

/**
 * The classical 紫微斗数 命盘: a 4×4 square whose twelve rim cells are the 地支
 * palaces (fixed positions) and whose centre 2×2 carries the chart summary.
 *
 * Every cell renders exactly what the engine seated there — palace name, 宫干支,
 * 大限 range and the stars with their 四化 marks. The 命宫 is gilded and the 身宫
 * badged; nothing is placed that the backend did not compute (PRD no-mock rule).
 */
export function ZiweiChartGrid({ chart }: ZiweiChartGridProps) {
  return (
    <div className="overflow-x-auto">
      <div
        className="grid min-w-[680px] grid-cols-4 gap-1.5"
        style={{ gridTemplateRows: 'repeat(4, minmax(132px, auto))' }}
      >
        {chart.palaces.map((palace) => (
          <PalaceCell key={palace.index} palace={palace} style={palaceGridStyle(palace.index)} />
        ))}
        <ChartCenter chart={chart} />
      </div>
    </div>
  );
}

/** One 地支 palace cell: name + 大限 + 干支 header over its seated stars. */
function PalaceCell({ palace, style }: { palace: Palace; style: CSSProperties }) {
  return (
    <div
      style={style}
      className={`flex min-h-[132px] flex-col gap-1.5 rounded-card border p-2 ${
        palace.is_ming ? 'border-gold/50 bg-gold/[0.07]' : 'border-rim bg-surface/50'
      }`}
    >
      <div className="flex items-start justify-between gap-1">
        <div className="flex items-center gap-1">
          <span
            className={`font-display text-sm font-semibold ${
              palace.is_ming ? 'text-gold-bright' : 'text-ink'
            }`}
          >
            {palace.name}
          </span>
          {palace.is_shen ? (
            <span className="rounded-element bg-astral/20 px-1 text-[10px] text-astral">身</span>
          ) : null}
        </div>
        {palace.dayun ? (
          <span className="numeric text-[10px] text-ink-muted">{palace.dayun}</span>
        ) : null}
      </div>

      <div className="flex flex-1 flex-wrap content-start gap-x-2 gap-y-1">
        {palace.stars.map((star) => (
          <StarChip key={star.name} star={star} />
        ))}
        {palace.stars.length === 0 ? (
          <span className="text-[11px] text-ink-muted">（无主星·借对宫）</span>
        ) : null}
      </div>

      <div className="flex items-baseline justify-between gap-1 border-t border-rim-soft pt-1">
        <span className="font-display text-xs text-gold-soft">{palace.ganzhi}</span>
        <span className="text-[10px] text-ink-muted">{palace.zhi}宫</span>
      </div>
    </div>
  );
}

/** A single star with its 四化 badge and kind colour. */
function StarChip({ star }: { star: StarPlacement }) {
  return (
    <span className="flex items-baseline gap-0.5" title={star.nature ?? `${star.kind}·${star.element}`}>
      <span className={`font-display text-xs ${starKindClass(star.kind)}`}>{star.name}</span>
      {star.sihua ? (
        <span
          className={`rounded-element px-1 text-[9px] font-semibold leading-tight ${sihuaClass(star.sihua)}`}
        >
          {sihuaShort(star.sihua)}
        </span>
      ) : null}
    </span>
  );
}

/** The centre 2×2 summary block of the 命盘. */
function ChartCenter({ chart }: { chart: ZiweiChart }) {
  const { sihua } = chart;
  return (
    <div
      style={CENTER_STYLE}
      className="flex flex-col items-center justify-center gap-2 rounded-card border border-rim-strong bg-[#0e111a] p-3 text-center"
    >
      <span className="label-caps text-gold">紫微斗数命盘</span>
      <div className="flex flex-col gap-0.5">
        <span className="font-display text-lg font-semibold text-gold-bright">{chart.wuxing_ju}</span>
        <span className="text-[11px] text-ink-muted">
          命宫 {chart.ming_gong_ganzhi} · {chart.ming_gong_nayin}
        </span>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-0.5 text-[11px] text-ink-variant">
        <span>
          命主 <span className="text-gold-soft">{chart.ming_zhu}</span>
        </span>
        <span>
          身主 <span className="text-gold-soft">{chart.shen_zhu}</span>
        </span>
      </div>
      <div className="flex flex-wrap items-center justify-center gap-1">
        <SiHuaBadge label="禄" star={sihua.lu} sihua="化禄" />
        <SiHuaBadge label="权" star={sihua.quan} sihua="化权" />
        <SiHuaBadge label="科" star={sihua.ke} sihua="化科" />
        <SiHuaBadge label="忌" star={sihua.ji} sihua="化忌" />
      </div>
      <span className="numeric text-[10px] text-ink-muted">
        {chart.lunar_year_ganzhi}年 · {chart.dayun_direction} · {chart.dayun_start_age}岁起运
      </span>
    </div>
  );
}

/** One 四化 badge in the centre block. */
function SiHuaBadge({ label, star, sihua }: { label: string; star: string; sihua: string }) {
  return (
    <span className={`flex items-center gap-0.5 rounded-element px-1.5 py-0.5 text-[11px] ${sihuaClass(sihua)}`}>
      <span className="font-semibold">{label}</span>
      <span className="font-display">{star}</span>
    </span>
  );
}
