import { ScoreLedger } from '../ui/ScoreLedger';
import type { ScoreValue } from '../../types/scoring';

/**
 * 相契度四档的唯一色标（与 `backend/app/content/synastry.py::SYNASTRY_TIERS` 同源）。
 *
 * 一张表管两件事：环的那道弧用 `stroke`（SVG 属性只吃颜色值，Tailwind 类名进不去），
 * 档名与中心分数用同源色。两处一表，于是「什么颜色配什么档」不可能各改一半。颜色取自
 * `tailwind.config.ts` 既有 token（wood/gold/ink-muted/fire），与合婚环同一支色板。
 */
export const SYNASTRY_TIER_LOOK: Record<string, { stroke: string; text: string }> = {
  相契甚深: { stroke: '#2DD4BF', text: 'text-wuxing-wood' },
  和合互补: { stroke: '#D4AF37', text: 'text-gold' },
  中和可处: { stroke: '#948C79', text: 'text-ink-muted' },
  磨合为宜: { stroke: '#F43F5E', text: 'text-wuxing-fire' },
};

/** 未知档位回落到金-muted：账本换了词而页面不炸，是这一处兜底的唯一用途。 */
export function synastryTierLook(tier: string): { stroke: string; text: string } {
  return SYNASTRY_TIER_LOOK[tier] ?? { stroke: '#997B24', text: 'text-ink' };
}

const SIZE = 128;
const RADIUS = 54;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * 相契度环 + 展开的赋分账本。
 *
 * 环上只有两个数：`score.value` 与它的弧长（`2πR × (1 - value/100)`，起点在 12 点方向，
 * `rotate(-90 …)` 只转那道弧，不转中心文字）。总分只由 `ScoreLedger` 再印一次，环不重复
 * 读数，故「页面两处总分不一样」这种事故在这里没有通道。账本展开是这一页的立身之处：
 * 50 分起算、每一条计入的合盘相位一行、`Σ delta == value`。环好看，账本可核。
 */
export function SynastryScoreRing({ score }: { score: ScoreValue }) {
  const look = synastryTierLook(score.tier);
  const percent = Math.min(100, Math.max(0, score.value));
  const center = SIZE / 2;

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:gap-10">
      <div className="flex shrink-0 items-center gap-5">
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="h-36 w-36"
          role="img"
          aria-label={`相契度 ${score.value.toFixed(1)} 分，${score.tier}`}
        >
          <circle cx={center} cy={center} r={RADIUS} fill="none" stroke="#171C2B" strokeWidth={9} />
          <circle
            cx={center}
            cy={center}
            r={RADIUS}
            fill="none"
            stroke={look.stroke}
            strokeWidth={9}
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={CIRCUMFERENCE * (1 - percent / 100)}
            transform={`rotate(-90 ${center} ${center})`}
          />
          <text
            x={center}
            y={center - 2}
            textAnchor="middle"
            className="font-numeric"
            fontSize="26"
            fill={look.stroke}
          >
            {score.value.toFixed(1)}
          </text>
          <text x={center} y={center + 20} textAnchor="middle" fontSize="13" fill="#948C79">
            百分制
          </text>
        </svg>
        <div className="flex flex-col gap-1">
          <span className={`font-display text-2xl font-semibold ${look.text}`}>{score.tier}</span>
          <span className="text-xs text-ink-muted">
            四档：≥75 相契甚深 · 60–74 和合互补 · 45–59 中和可处 · &lt;45 磨合为宜
          </span>
        </div>
      </div>

      <div className="min-w-[16rem] flex-1">
        <ScoreLedger score={score} label="相契度账本（50 分起算）" />
      </div>
    </div>
  );
}
