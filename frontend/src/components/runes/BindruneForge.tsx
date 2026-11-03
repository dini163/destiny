import { useMemo, useState } from 'react';

import { ResultCard } from '../ui/ResultCard';
import { Icon } from '../ui/Icon';
import { flattenCodex, isBlankStone } from '../../lib/runes';
import type { CodexRune, RuneCodex } from '../../types/runes';

interface BindruneForgeProps {
  /** 本次响应里的全典，作为可选符文来源。 */
  codex: RuneCodex;
}

/** 一次绑定最多叠加的符文枚数。 */
const MAX_SELECTED = 5;

/**
 * Bindrune 组合符文生成器：从全典里挑选若干枚，并列成一条组合符。
 *
 * 传统 bindrune 是把几枚符文的主干笔画**手工熔刻**到同一条竖线上；前端没有每枚符文的
 * 笔画矢量，不伪造自动叠笔。这里做的是诚实的并置：把选中的字形排成一条符号带，并逐枚附上
 * 名义与正位关键词，供读者自行手刻或取用 —— 不给一个"已经熔合成一枚"的假结果。
 */
export function BindruneForge({ codex }: BindruneForgeProps) {
  const all = useMemo(() => flattenCodex(codex).filter((rune) => !isBlankStone(rune)), [codex]);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);

  const selected = all.filter((rune) => selectedKeys.includes(rune.key));

  function toggle(key: string): void {
    setSelectedKeys((prev) => {
      if (prev.includes(key)) return prev.filter((k) => k !== key);
      if (prev.length >= MAX_SELECTED) return prev;
      return [...prev, key];
    });
  }

  async function copyCombo(): Promise<void> {
    const text = selected.map((rune) => rune.glyph).join('');
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // 剪贴板被权限拒绝时不报错打断，组合带本身仍可见可手抄。
    }
  }

  return (
    <ResultCard title="Bindrune 组合符" icon="compass">
      <p className="text-sm leading-relaxed text-ink-muted">
        从全典挑 1–{MAX_SELECTED} 枚符文，并置成一条组合符。这里只做字形并置，不自动熔刻笔画；
        传统叠笔需手工刻写。
      </p>

      <div className="grid grid-cols-4 gap-2 sm:grid-cols-6 md:grid-cols-8">
        {all.map((rune) => {
          const active = selectedKeys.includes(rune.key);
          return (
            <button
              key={rune.key}
              type="button"
              onClick={() => toggle(rune.key)}
              aria-pressed={active}
              aria-label={`${rune.name} · ${rune.name_zh}`}
              className={`flex flex-col items-center gap-1 rounded-element border p-2 transition-colors ${
                active
                  ? 'border-gold/60 bg-gold/10'
                  : 'border-rim bg-surface hover:border-rim-strong'
              }`}
            >
              <span aria-hidden="true" className="font-display text-2xl leading-8 text-gold-bright">
                {rune.glyph}
              </span>
              <span className="text-[11px] leading-tight text-ink-variant">{rune.name_zh}</span>
            </button>
          );
        })}
      </div>

      {selected.length === 0 ? (
        <p className="label-caps rounded-element border border-dashed border-rim-soft p-4 text-ink-muted">
          点选上方符文后，这里会出现组合符号带。
        </p>
      ) : (
        <div className="flex flex-col gap-4 rounded-element border border-gold/25 bg-[#0c0e14] p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div
              aria-hidden="true"
              className="flex flex-wrap gap-3 font-display text-5xl leading-none text-gold-bright"
              style={{ filter: 'drop-shadow(0 0 14px rgba(242,202,80,0.45))' }}
            >
              {selected.map((rune) => (
                <span key={rune.key}>{rune.glyph}</span>
              ))}
            </div>
            <button
              type="button"
              onClick={copyCombo}
              className="btn-ghost shrink-0 rounded-element px-3 py-1.5 text-xs"
            >
              <Icon name="check" size={14} />
              {copied ? '已复制' : '复制组合'}
            </button>
          </div>

          <ul className="flex flex-col gap-2">
            {selected.map((rune) => (
              <SelectedRuneRow key={rune.key} rune={rune} />
            ))}
          </ul>
        </div>
      )}
    </ResultCard>
  );
}

/** 组合里单枚符文的名义与正位关键词。 */
function SelectedRuneRow({ rune }: { rune: CodexRune }) {
  return (
    <li className="flex flex-col gap-1 rounded-element border border-rim bg-[var(--field-bg)] p-3">
      <div className="flex flex-wrap items-center gap-2">
        <span aria-hidden="true" className="text-2xl text-gold-bright">
          {rune.glyph}
        </span>
        <span className="font-display text-sm text-ink">
          {rune.name} · {rune.name_zh}
        </span>
        <span className="text-xs text-ink-muted">{rune.name_meaning}</span>
      </div>
      {rune.upright_keywords.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {rune.upright_keywords.map((keyword) => (
            <span
              key={keyword}
              className="label-caps rounded-element border border-rim bg-surface px-1.5 py-0.5 text-[11px] text-ink-variant"
            >
              {keyword}
            </span>
          ))}
        </div>
      ) : null}
    </li>
  );
}
