import { SourceNote } from '../ui/SourceNote';
import { masterPair } from '../../lib/numerology';
import type { CoreNumber, CoreNumberKey } from '../../types/numerology';

/**
 * 每个核心数**怎么来的**一句话。
 *
 * 这是展示措辞而不是权威内容（同 `lib/tarot.ts` 的 `SUIT_ZH`、`lib/zhouyi.ts` 的
 * `POSITION_ZH` 那类键→中文标签的既有做法）：它不给出任何数，只说明这一张卡读的是哪一份
 * 输入，而且每一句都能在同一张卡自带的 `steps` 里逐行核对（`expression` 的第一项就是它）。
 * 语料里刻意不写死角色（spec §5.2：`CORE_MEANINGS` 只给中性释义，「作为生命灵数意味着
 * 什么」由前端标题提供），这句就是那个"前端标题"。
 */
const DERIVATION: Record<CoreNumberKey, string> = {
  life_path: '出生年月日各自约简后相加',
  expression: '全名字母值总和',
  soul_urge: '元音字母值总和',
  personality: '辅音字母值总和',
  birthday: '出生日约简',
  maturity: '生命灵数 + 表达数',
};

interface CoreNumberCardProps {
  card: CoreNumber;
  /** 栅格跨列（设计稿让成熟数横跨两列）。 */
  className?: string;
}

/**
 * 其余五个核心数的小卡（spec §8）。
 *
 * 与 {@link CoreNumberHero} 同一套字段、同一套双数字版式，只是尺寸收一档；两张卡都走
 * `masterPair`，于是"主数印 `11 /2`、非主数只印一个数"这条规矩不可能只在一处生效。
 *
 * `value` 为 null 时（决策 17，如 `Lynn` 的灵魂冲动数）卡**不消失**：标题与推导说明照印，
 * 数字位换成 `unavailable_reason`。少一张卡读起来像页面没渲染完，留一张说明原因的卡读起来
 * 像"查过了，这个名字算不出这个数"。
 */
export function CoreNumberCard({ card, className }: CoreNumberCardProps) {
  const pair = masterPair(card.value, card.root, card.is_master);

  return (
    <article
      className={`flex flex-col gap-3 rounded-card border border-rim bg-surface p-4 ${className ?? ''}`}
    >
      <header className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-0.5">
          <span className="label-caps text-ink-muted">{DERIVATION[card.key]}</span>
          <h3 className="font-display text-base font-semibold text-ink">{card.label}</h3>
        </div>
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-element border border-rim bg-surface-raised">
          {pair ? (
            <span className="numeric text-xl font-semibold text-gold-bright">
              {pair.primary}
              {pair.rootSuffix ? (
                <span className="ml-0.5 text-xs text-gold">{pair.rootSuffix}</span>
              ) : null}
            </span>
          ) : (
            <span className="font-display text-sm text-ink-muted">缺</span>
          )}
        </span>
      </header>

      {card.is_master && card.master_title ? (
        <span className="label-caps w-fit rounded-element border border-gold/40 bg-gold/10 px-1.5 py-0.5 text-gold-bright">
          主数 · {card.master_title}
        </span>
      ) : null}

      {card.meaning ? (
        <p className="text-xs leading-relaxed text-ink-variant">{card.meaning}</p>
      ) : null}

      {card.unavailable_reason ? (
        <p className="text-xs leading-relaxed text-wuxing-fire">{card.unavailable_reason}</p>
      ) : null}

      {card.keywords.length > 0 ? (
        <ul className="flex flex-wrap gap-1">
          {card.keywords.map((keyword) => (
            <li
              key={keyword}
              className="rounded-element bg-surface-raised px-1.5 py-0.5 text-[11px] text-ink-variant"
            >
              {keyword}
            </li>
          ))}
        </ul>
      ) : null}

      {card.talent ? (
        <p className="text-[11px] leading-relaxed text-ink-muted">
          <span className="label-caps text-gold">天赋 </span>
          {card.talent}
        </p>
      ) : null}
      {card.challenge ? (
        <p className="text-[11px] leading-relaxed text-ink-muted">
          <span className="label-caps text-wuxing-fire">阴影 </span>
          {card.challenge}
        </p>
      ) : null}

      <div className="mt-auto pt-1">
        <SourceNote source={card.source} />
      </div>
    </article>
  );
}
