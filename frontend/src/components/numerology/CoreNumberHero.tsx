import { ReductionLadder } from './ReductionLadder';
import { SourceNote } from '../ui/SourceNote';
import { masterPair } from '../../lib/numerology';
import { useI18n } from '../../i18n/context';
import type { CoreNumber } from '../../types/numerology';

const SIZE = 100;
const CENTER = SIZE / 2;

/**
 * 生命灵数大卡（spec §8、设计稿的 `lg:col-span-5` 那张）。
 *
 * 双环 SVG 照设计稿的版式，但**两道环都是整圆**：设计稿给外环加了 `stroke-dashoffset`，
 * 那等于把一个数印成了弧长，读者只会读成"某种百分比" —— 而决策 13 明令不出任何百分比，
 * 生命灵数也没有权威的量纲可供弧长去表达。故这里让环只做边框，数只做数：环不承担读数，
 * 就不可能承担一个编出来的读数。
 *
 * `value /root` 双数字版式走 `masterPair`：主数印 `11` 大号加 `/2` 小号，非主数只印一个数
 * （印 `6 /6` 是废字）。`value` 为 null 时（决策 17）整块换成 `unavailable_reason`，
 * 不印 0、不印空环。
 */
export function CoreNumberHero({ card }: { card: CoreNumber }) {
  const { t } = useI18n();
  const pair = masterPair(card.value, card.root, card.is_master);

  return (
    <article className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
          {t('核心最高显相')}
        </span>
        {card.is_master && card.master_title ? (
          <span className="label-caps rounded-element border border-gold/40 px-2 py-0.5 text-gold-bright">
            {t('主数 · {{title}}', { title: card.master_title })}
          </span>
        ) : null}
      </header>

      <div className="flex flex-col items-center gap-5 sm:flex-row sm:items-start sm:gap-7">
        <div className="relative flex h-36 w-36 shrink-0 items-center justify-center">
          <svg
            viewBox={`0 0 ${SIZE} ${SIZE}`}
            className="h-full w-full"
            role="img"
            aria-label={
              pair
                ? `${card.label} ${pair.primary}${pair.rootSuffix ?? ''}`
                : t('{{label}} 算不出', { label: card.label })
            }
          >
            <circle cx={CENTER} cy={CENTER} r={44} fill="none" stroke="#171C2B" strokeWidth={6} />
            <circle cx={CENTER} cy={CENTER} r={44} fill="none" stroke="#D4AF37" strokeWidth={2} />
            <circle
              cx={CENTER}
              cy={CENTER}
              r={37}
              fill="none"
              stroke="#948C79"
              strokeWidth={1}
              strokeDasharray="4 3"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            {pair ? (
              <>
                <span className="numeric text-4xl font-semibold leading-none text-gold-bright">
                  {pair.primary}
                </span>
                {pair.rootSuffix ? (
                  <span className="numeric mt-1 text-lg leading-none text-gold">{pair.rootSuffix}</span>
                ) : null}
              </>
            ) : (
              <span className="font-display text-sm text-ink-muted">{t('缺')}</span>
            )}
          </div>
        </div>

        <div className="flex min-w-0 flex-col gap-2">
          <h3 className="font-display text-lg font-semibold text-ink sm:text-xl">{card.label}</h3>
          {card.meaning ? (
            <p className="text-sm leading-relaxed text-ink-variant">{card.meaning}</p>
          ) : null}
          {card.unavailable_reason ? (
            <p className="flex items-start gap-2 text-sm leading-relaxed text-wuxing-fire">
              {card.unavailable_reason}
            </p>
          ) : null}
          {card.keywords.length > 0 ? (
            <ul className="flex flex-wrap gap-1.5 pt-1">
              {card.keywords.map((keyword) => (
                <li
                  key={keyword}
                  className="rounded-element bg-surface-raised px-2 py-1 text-xs text-ink"
                >
                  {keyword}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>

      <div className="rounded-card border border-rim bg-[var(--field-bg)] p-3">
        <ReductionLadder steps={card.steps} caption="约简运算阶梯 Recursive Breakdown" />
      </div>

      {card.talent || card.challenge ? (
        <dl className="flex flex-col gap-1.5 text-xs leading-relaxed">
          {card.talent ? (
            <div className="flex gap-2">
              <dt className="label-caps shrink-0 text-gold">{t('天赋')}</dt>
              <dd className="text-ink-variant">{card.talent}</dd>
            </div>
          ) : null}
          {card.challenge ? (
            <div className="flex gap-2">
              <dt className="label-caps shrink-0 text-wuxing-fire">{t('阴影')}</dt>
              <dd className="text-ink-variant">{card.challenge}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}

      <div className="mt-auto pt-1">
        <SourceNote source={card.source} />
      </div>
    </article>
  );
}
