import { useState } from 'react';

import { ResultCard } from '../ui/ResultCard';
import { SourceNote } from '../ui/SourceNote';
import { codexMatches, flattenCodex, isBlankStone } from '../../lib/runes';
import type { AettGroup, CodexRune, RuneCodex } from '../../types/runes';

interface FutharkCodexProps {
  /** 恒为 25 条，不随 `include_wyrd` 变。 */
  codex: RuneCodex;
}

/** 码位印成 `U+16B7` 这种通行写法。纯版式：数值本身来自后端，这里不做任何推导。 */
function codepointOf(codepoint: number | null): string {
  if (codepoint === null) return '—';
  return `U+${codepoint.toString(16).toUpperCase().padStart(4, '0')}`;
}

/** 一格的按钮。三组栏与空白符栏共用，免得两处各写一遍版式然后各自漂移。 */
function CodexCell({
  rune,
  selected,
  onSelect,
}: {
  rune: CodexRune;
  selected: boolean;
  onSelect: () => void;
}) {
  const blank = isBlankStone(rune);
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`${rune.name} · ${rune.name_zh} · 序位 ${rune.order}`}
      className={`flex flex-col items-center gap-1 rounded-element border p-2 transition-colors ${
        selected
          ? 'border-gold/60 bg-gold/10'
          : 'border-rim bg-surface hover:border-rim-strong'
      }`}
    >
      {blank ? (
        <span
          aria-hidden="true"
          className="flex h-8 w-8 items-center justify-center rounded-full border border-dashed border-arcane/50"
        />
      ) : (
        <span aria-hidden="true" className="font-display text-2xl leading-8 text-gold-bright">
          {rune.glyph}
        </span>
      )}
      <span className="text-[11px] leading-tight text-ink-variant">{rune.name_zh}</span>
      <span className="numeric label-caps text-ink-muted">
        {String(rune.order).padStart(2, '0')}
      </span>
    </button>
  );
}

/** 选中那一枚的两面释义与码位锚点。 */
function CodexDetail({ rune }: { rune: CodexRune }) {
  return (
    <div className="flex flex-col gap-4 rounded-element border border-rim bg-surface p-4">
      <div className="flex flex-wrap items-center gap-2.5">
        {isBlankStone(rune) ? null : (
          <span aria-hidden="true" className="font-display text-4xl leading-none text-gold-bright">
            {rune.glyph}
          </span>
        )}
        <span className="font-display text-lg text-ink">
          {rune.name} · {rune.name_zh}
        </span>
        {rune.is_wyrd ? (
          <span className="label-caps rounded-element border border-arcane/40 bg-arcane/10 px-1.5 py-0.5 text-[#c7cbff]">
            空白石 · 现代增补
          </span>
        ) : null}
      </div>

      {/* 宽表纪律：外层横向滚动、表自身给足最小宽度，窄屏读到的是一行完整的锚点而不是一列挤扁的字。 */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] text-xs">
          <caption className="sr-only">所选符文的码位、音译与名义</caption>
          <thead>
            <tr className="text-left text-ink-muted">
              <th scope="col" className="font-normal">序位</th>
              <th scope="col" className="font-normal">音译</th>
              <th scope="col" className="font-normal">音值</th>
              <th scope="col" className="font-normal">码位</th>
              <th scope="col" className="font-normal">Unicode 官方名</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t border-rim align-top">
              <td className="numeric py-2 pr-3 text-ink-variant">
                {String(rune.order).padStart(2, '0')}
              </td>
              <td className="numeric py-2 pr-3 text-ink-variant">
                {rune.transliteration === '' ? '—' : rune.transliteration}
              </td>
              <td className="py-2 pr-3 text-ink-variant">{rune.phoneme}</td>
              <td className="numeric py-2 pr-3 text-gold-soft">{codepointOf(rune.codepoint)}</td>
              <td className="py-2 text-ink-muted">{rune.unicode_name ?? '—'}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <p className="text-sm leading-relaxed text-ink-variant">
        <span className="label-caps mr-1.5 text-gold-soft">名义</span>
        {rune.name_meaning}
        {rune.name_meaning_uncertain ? (
          <span className="label-caps ml-2 rounded-element border border-rim bg-[var(--field-bg)] px-1.5 py-0.5 text-ink-muted">
            名义不确定
          </span>
        ) : null}
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="flex flex-col gap-2">
          <span className="label-caps text-[#2dd4bf]">正位</span>
          <div className="flex flex-wrap gap-1.5">
            {rune.upright_keywords.map((keyword) => (
              <span
                key={keyword}
                className="label-caps rounded-element border border-rim bg-[var(--field-bg)] px-1.5 py-0.5 text-ink-muted"
              >
                {keyword}
              </span>
            ))}
          </div>
          <p className="text-sm leading-relaxed text-ink-variant">{rune.upright_meaning}</p>
        </div>

        <div className="flex flex-col gap-2">
          <span className="label-caps text-[#f43f5e]">逆位</span>
          {rune.reversed_meaning === null || rune.reversed_keywords === null ? (
            <p className="text-sm leading-relaxed text-ink-muted">
              此符对称，无逆位 —— 字形转 180° 后与原形重合，故语料不给它编一段逆位释义。
            </p>
          ) : (
            <>
              <div className="flex flex-wrap gap-1.5">
                {rune.reversed_keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="label-caps rounded-element border border-rim bg-[var(--field-bg)] px-1.5 py-0.5 text-ink-muted"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
              <p className="text-sm leading-relaxed text-ink-variant">{rune.reversed_meaning}</p>
            </>
          )}
        </div>
      </div>

      <SourceNote source={rune.source} />
    </div>
  );
}

/**
 * 全典抽屉（spec §8、plan T7 Step 6；决策 25）。
 *
 * 三组 8+8+8 **全是真符文**，Dagaz 在第三位第二组末（决策 2 拦的是设计稿那张漏了 Dagaz、
 * 把 ᚨ 写成 ᚫ 的图）；空白符**单独一栏**并标注现代增补，不混进任何一组。全典恒为 25 条，
 * 不随 `include_wyrd` 变 —— 那个开关管的是抽不抽得着它，不是它在不在典里。
 *
 * 检索接 `lib/runes.ts` 的 `codexMatches`；命中数用 `flattenCodex` 摊平后数，跨组一个总数。
 * 某一组一条都没命中时**整栏隐掉**，而不是留一个空栏头：抽屉按组分栏，空栏头看着像「这一组
 * 本来就没有符文」。
 *
 * 三组各带一份 `naming_note`，但**当前三份逐字相同**，且与 `provenance.naming_note` 也是同一段
 * 话。故这里一条都不印：spec §8 把「ætt 命名多种叫法」归给出处卡，那一栏就在同一页上，再印
 * 一遍就是把同一段一百来字的声明在同屏印两次。字段照常下发，本组件不消费它。
 *
 * 选中状态与检索词各自独立：过滤把选中那枚滤掉时，下面的详情仍然留着 —— 读者正在读它，
 * 因为在框里补了一个字就把详情抽走，是在替他决定他看完了。
 */
export function FutharkCodex({ codex }: FutharkCodexProps) {
  const [query, setQuery] = useState('');
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const all = flattenCodex(codex);
  const hitCount = all.filter((rune) => codexMatches(rune, query)).length;
  const selected = all.find((rune) => rune.key === selectedKey) ?? null;

  const rails: { group: AettGroup; hits: CodexRune[] }[] = codex.aettir
    .map((group) => ({
      group,
      hits: group.runes.filter((rune) => codexMatches(rune, query)),
    }))
    .filter((rail) => rail.hits.length > 0);

  const wyrdVisible = codexMatches(codex.wyrd, query);

  return (
    <ResultCard
      title="全典 · Elder Futhark"
      eyebrow="CODEX"
      icon="search"
      actions={
        <span className="numeric label-caps text-ink-muted">
          {hitCount} / {codex.total} 条命中
        </span>
      }
    >
      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="按名、音译或词义检索，如 fehu、þ、赠予"
        className="field w-full"
        aria-label="检索全典：按名、音译或词义过滤"
      />

      {hitCount === 0 ? (
        <p className="rounded-element border border-rim bg-[var(--field-bg)] p-4 text-sm text-ink-muted">
          没有对得上的条目。清空检索框可以看整部典。
        </p>
      ) : (
        <div className="flex flex-col gap-5">
          <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
            {rails.map(({ group, hits }) => (
              <section
                key={group.key}
                className="flex flex-col gap-3 rounded-element border border-rim bg-[var(--field-bg)] p-3"
              >
                <header className="flex flex-col gap-1">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h3 className="font-display text-base text-ink">{group.name_zh}</h3>
                    <span className="numeric label-caps text-ink-muted">
                      {hits.length} / {group.runes.length}
                    </span>
                  </div>
                  <span className="label-caps text-gold-soft">{group.name}</span>
                  <span className="text-xs leading-relaxed text-ink-muted">{group.theme}</span>
                </header>
                <div className="grid grid-cols-4 gap-2">
                  {hits.map((rune) => (
                    <CodexCell
                      key={rune.key}
                      rune={rune}
                      selected={rune.key === selectedKey}
                      onSelect={() => setSelectedKey(rune.key)}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>

          {wyrdVisible ? (
            <section className="flex flex-col gap-3 rounded-element border border-arcane/30 bg-[var(--field-bg)] p-3">
              <header className="flex flex-wrap items-center gap-2">
                <h3 className="font-display text-base text-ink">{codex.wyrd.name_zh}</h3>
                <span className="label-caps rounded-element border border-arcane/40 bg-arcane/10 px-1.5 py-0.5 text-[#c7cbff]">
                  现代增补 · 不入三组
                </span>
              </header>
              <div className="grid grid-cols-4 gap-2 sm:max-w-[12rem]">
                <CodexCell
                  rune={codex.wyrd}
                  selected={codex.wyrd.key === selectedKey}
                  onSelect={() => setSelectedKey(codex.wyrd.key)}
                />
              </div>
            </section>
          ) : null}
        </div>
      )}

      {selected === null ? (
        <p className="label-caps text-ink-muted">选一枚看它的两面释义与码位锚点</p>
      ) : (
        <CodexDetail rune={selected} />
      )}
    </ResultCard>
  );
}
