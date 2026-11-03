import { useState } from 'react';

import { ResultCard } from '../ui/ResultCard';
import { Icon } from '../ui/Icon';
import { downloadRuneTranscript } from '../../lib/runeExport';
import { loadVault, persistVault, removeCast, saveCast } from '../../lib/runeVault';
import type { SavedRuneCast } from '../../lib/runeVault';
import type { RuneCastResponse } from '../../types/runes';

interface RuneVaultPanelProps {
  /** 当前屏上这份铸石，供「存入秘匣」取用。 */
  cast: RuneCastResponse;
}

/**
 * 神谕秘匣：本机 localStorage 里的铸石收藏（PRD §9 客户端存档的卢恩落地）。
 *
 * 只存本机、不上传后端；列表按保存时间新→旧，每条可单独导出命谱或删除。这里不重做一整套
 * 石阵回看 —— 回看就是重新掷符或导出命谱，面板只承担「存得住、找得到、删得掉」。
 */
export function RuneVaultPanel({ cast }: RuneVaultPanelProps) {
  const [entries, setEntries] = useState<SavedRuneCast[]>(() => loadVault());
  const [justSaved, setJustSaved] = useState(false);

  function handleSave(): void {
    const next = saveCast(entries, cast);
    persistVault(next);
    setEntries(next);
    setJustSaved(true);
    window.setTimeout(() => setJustSaved(false), 1800);
  }

  function handleRemove(id: string): void {
    const next = removeCast(entries, id);
    persistVault(next);
    setEntries(next);
  }

  return (
    <ResultCard title="神谕秘匣" icon="vault">
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" onClick={handleSave} className="btn-primary shrink-0">
          <Icon name="vault" size={18} />
          {justSaved ? '已存入秘匣' : '存入本份铸石'}
        </button>
        <span className="label-caps text-ink-muted">本机保存 · 共 {entries.length} 份</span>
      </div>

      {entries.length === 0 ? (
        <p className="rounded-element border border-dashed border-rim-soft p-4 text-sm text-ink-muted">
          秘匣是空的。掷出一份铸石后按「存入本份铸石」，它就只留在这台设备的浏览器里。
        </p>
      ) : (
        <ul className="flex flex-col gap-2.5">
          {entries.map((entry) => (
            <li
              key={entry.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-element border border-rim bg-[var(--field-bg)] p-3"
            >
              <div className="flex min-w-0 flex-col gap-1">
                <span className="font-display text-sm text-ink">
                  {entry.cast.spread_name_zh}
                  <span className="numeric label-caps ml-2 text-ink-muted">
                    {entry.cast.stones.length} 枚 · {entry.cast.verdict.grade}
                  </span>
                </span>
                <span className="truncate text-xs text-ink-muted">
                  {entry.cast.question ?? '未附所问'} · 存于{' '}
                  {new Date(entry.saved_at).toLocaleString('zh-CN')}
                </span>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <button
                  type="button"
                  onClick={() => downloadRuneTranscript(entry.cast)}
                  className="btn-ghost rounded-element px-2.5 py-1 text-xs"
                >
                  <Icon name="seal" size={13} />
                  导出
                </button>
                <button
                  type="button"
                  onClick={() => handleRemove(entry.id)}
                  aria-label="删除这份存档"
                  className="flex h-7 w-7 items-center justify-center rounded-element border border-rim text-ink-muted transition-colors hover:border-wuxing-fire hover:text-wuxing-fire"
                >
                  <Icon name="close" size={14} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </ResultCard>
  );
}
