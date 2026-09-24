import { ScoreLedger } from '../../ui/ScoreLedger';
import type { ScoreValue } from '../../../types/scoring';

/**
 * 合婚四档的唯一色标（spec §6.4）。
 *
 * 一张表管两件事：环的那道弧用 `stroke`（SVG 属性只吃颜色值，Tailwind 类名进不去），
 * 档名与分数文字用 `text`。两处同源，于是"什么颜色配什么档"不可能各改一半。
 * 颜色取自 `tailwind.config.ts` 的既有 token（wood/gold/ink-muted/fire），不新调一支色。
 */
export const HEHUN_TIER_LOOK: Record<string, { stroke: string; text: string }> = {
  天作之合: { stroke: '#2DD4BF', text: 'text-wuxing-wood' },
  相得益彰: { stroke: '#D4AF37', text: 'text-gold' },
  中和可处: { stroke: '#948C79', text: 'text-ink-muted' },
  欠和宜慎: { stroke: '#F43F5E', text: 'text-wuxing-fire' },
};

/** 未知档位回落到金-muted：账本换了词而页面不炸，是这一处兜底的唯一用途。 */
export function hehunTierLook(tier: string): { stroke: string; text: string } {
  return HEHUN_TIER_LOOK[tier] ?? { stroke: '#997B24', text: 'text-ink' };
}

const SIZE = 128;
const RADIUS = 54;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * 契合度环 + 展开的赋分账本（spec §8 的第二段）。
 *
 * 环上只有两个数：`score.value` 与它的弧长。弧长 = `2πR × (1 - value/100)`，起点在
 * 12 点方向（`rotate(-90 …)` 只转那道弧，不转中心文字 —— 中心那两行是要读的）。
 * 总分只由 `ScoreLedger` 再印一次数字，环不重复读数，所以"页面两处总分不一样"这种
 * 事故在这里没有通道。
 *
 * 账本展开是这一页的立身之处：50 分起算、每一条命中一行、`Σ delta == value`（§10.5）。
 * 环好看，账本可核 —— 缺了后半件这一页就只是一个吉凶断言。
 */
export function HehunScoreRing({ score }: { score: ScoreValue }) {
  const look = hehunTierLook(score.tier);
  const percent = Math.min(100, Math.max(0, score.value));
  const center = SIZE / 2;

  return (
    <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:gap-10">
      <div className="flex shrink-0 items-center gap-5">
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="h-36 w-36"
          role="img"
          aria-label={`契合度 ${score.value.toFixed(1)} 分，${score.tier}`}
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
          <span className="text-xs text-ink-muted">四档：≥80 天作之合 · 65–79 相得益彰 · 45–64 中和可处 · &lt;45 欠和宜慎</span>
        </div>
      </div>

      <div className="min-w-[16rem] flex-1">
        <ScoreLedger score={score} label="契合度账本（50 分起算）" />
      </div>
    </div>
  );
}
