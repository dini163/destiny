import { useState } from 'react';

import { GematriaConsole, GematriaResult } from '../components/kabbalah/GematriaConsole';
import { NodeInspector } from '../components/kabbalah/NodeInspector';
import { TreeOfLife } from '../components/kabbalah/TreeOfLife';
import { Icon } from '../components/ui/Icon';
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { ResultCard } from '../components/ui/ResultCard';
import { useGematria } from '../hooks/useGematria';
import { useKabbalahTree } from '../hooks/useKabbalahTree';
import { DEFAULT_SELECTION, pillarAccent, resolveSelection, type Selection } from '../lib/kabbalah';
import type { KabbalahTree } from '../types/kabbalah';

/**
 * 卡巴拉生命之树 page (Kabbalah Tree of Life).
 *
 * The Tree is fixed reference content fetched once via `useKabbalahTree`; the user
 * explores it by clicking a Sephirah or Path (or the chip index) to read its full
 * Golden Dawn correspondence. An optional gematria console weighs a word and folds
 * it onto the same map. Every value comes from the engine (PRD no-mock rule).
 *
 * 每一格先读白话：`NodeInspector` 把节点的 `plain_meaning`（多系统白话 spec §7，文本住在
 * `content/kabbalah_plain.py`，由引擎逐格挂进响应）排在最前，专业释义 `meaning` 降级在其下
 * —— 这一上一下不许调换，也不许在前端补一句领起：白话在上就是那一层存在的全部理由。
 */
export function KabbalahPage() {
  const tree = useKabbalahTree();
  const [selection, setSelection] = useState<Selection>(DEFAULT_SELECTION);
  const [word, setWord] = useState('');
  const gematria = useGematria();

  function handleWeigh(): void {
    const trimmed = word.trim();
    if (trimmed === '') return;
    gematria.mutate({ text: trimmed });
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <div className="kabbalah-reveal">
        <Intro />
      </div>

      {tree.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{tree.error.message}</span>
        </div>
      ) : null}

      {tree.isLoading ? <p className="label-caps text-ink-muted">正在展开生命之树…</p> : null}

      {tree.data ? (
        <>
          <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
            <div className="min-w-0 lg:col-span-7 2xl:col-span-8">
              <div className="kabbalah-reveal" style={{ animationDelay: '0.1s' }}>
                <ResultCard
                  title="生命之树"
                  eyebrow={`TREE OF LIFE · ${tree.data.sephirah_count} 原质 · ${tree.data.path_count} 路径`}
                  icon="compass"
                  elevated
                >
                  <div className="kabbalah-atlas">
                    <div className="kabbalah-atlas-heading">
                      <span className="label-caps text-gold-soft">ILLUSTRATED MAP · GOLDEN DAWN</span>
                      <span className="text-xs text-ink-variant">点选原质或路径，展开象征对应</span>
                    </div>
                    <TreeOfLife tree={tree.data} selection={selection} onSelect={setSelection} />
                  </div>
                  <div className="kabbalah-index">
                    <SephirahIndex tree={tree.data} selection={selection} onSelect={setSelection} />
                    <div className="gold-rule" />
                    <PathIndex tree={tree.data} selection={selection} onSelect={setSelection} />
                  </div>
                </ResultCard>
              </div>

              <div className="kabbalah-reveal" style={{ animationDelay: '0.18s' }}>
                <ResultCard title="全树白话" icon="sparkle" elevated>
                  <PlainSectionList sections={tree.data.plain} />
                </ResultCard>
              </div>
            </div>
            <div className="min-w-0 lg:col-span-5 2xl:col-span-4">
              <ResultCard
                title="原质 / 路径详解"
                icon="search"
                className="lg:sticky lg:top-36 lg:self-start"
              >
                <div
                  key={`${selection?.kind ?? 'none'}:${selection?.id ?? 'none'}`}
                  className="kabbalah-inspector-transition"
                >
                  <NodeInspector resolved={resolveSelection(selection, tree.data)} />
                </div>
              </ResultCard>
            </div>
          </div>

          <ResultCard title="gematria 数理折入" icon="gauge">
            <GematriaConsole value={word} onChange={setWord} pending={gematria.isPending} onSubmit={handleWeigh} />
            {gematria.error ? (
              <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-3 py-2 text-sm text-ink">
                <Icon name="alert" size={16} className="mt-0.5 shrink-0 text-wuxing-fire" />
                <span>{gematria.error.message}</span>
              </div>
            ) : null}
            {gematria.data ? <GematriaResult reading={gematria.data} onSelect={setSelection} /> : null}
          </ResultCard>
        </>
      ) : null}
    </div>
  );
}

/** Page intro: what the Tree is, plus the three pillars and four worlds as a legend. */
function Intro() {
  return (
    <ResultCard title="卡巴拉生命之树" icon="compass" elevated>
      <p className="max-w-4xl text-sm leading-relaxed text-ink-variant sm:text-base">
        生命之树是卡巴拉的核心图示：神圣之光自<span className="text-gold-soft">王冠（Kether）</span>逐级降落，经十原质（Sephiroth）显化为物质世界的<span className="text-gold-soft">王国（Malkuth）</span>；十原质之间由 22 条路径相连，每条路径对应一个希伯来字母、一张塔罗大阿卡纳与一组行星／星座／元素。点选任意原质或路径，即可查其黄金黎明（Golden Dawn）体系下的完整对应。
      </p>
    </ResultCard>
  );
}

/** Clickable chips for the ten Sephiroth (+ Daath) — the keyboard-accessible navigator. */
function SephirahIndex({
  tree,
  selection,
  onSelect,
}: {
  tree: KabbalahTree;
  selection: Selection;
  onSelect: (selection: Selection) => void;
}) {
  const nodes = tree.daath ? [...tree.sephiroth, tree.daath] : [...tree.sephiroth];
  return (
    <div className="flex flex-col gap-2">
      <span className="label-caps text-ink-muted">十原质 · SEPHIROTH</span>
      <div className="flex flex-wrap gap-1.5">
        {nodes.map((node) => {
          const active = selection?.id === node.id;
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => onSelect({ kind: 'sephirah', id: node.id })}
              aria-pressed={active}
              className={`kabbalah-index-chip inline-flex items-center gap-2 rounded-element border px-3 py-1.5 text-xs ${
                active
                  ? 'border-gold bg-gold/15 text-ink shadow-[0_0_14px_-6px_rgba(212,175,55,0.5)]'
                  : 'border-rim-soft bg-surface text-ink-muted hover:text-ink'
              }`}
            >
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: pillarAccent(node.pillar) }} />
              <span className={`numeric ${active ? 'text-gold-bright' : 'text-gold-soft'}`}>
                {node.is_hidden ? '✧' : node.number}
              </span>
              {node.name_zh}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** Clickable chips for the twenty-two Paths — number, Hebrew letter and Tarot trump. */
function PathIndex({
  tree,
  selection,
  onSelect,
}: {
  tree: KabbalahTree;
  selection: Selection;
  onSelect: (selection: Selection) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      <span className="label-caps text-ink-muted">22 路径 · PATHS</span>
      <div className="flex flex-wrap gap-1.5">
        {tree.paths.map((path) => {
          const active = selection?.id === path.id;
          return (
            <button
              key={path.id}
              type="button"
              onClick={() => onSelect({ kind: 'path', id: path.id })}
              title={`${path.from_name_zh} → ${path.to_name_zh}`}
              aria-pressed={active}
              className={`kabbalah-index-chip inline-flex items-center gap-1.5 rounded-element border px-3 py-1.5 text-xs ${
                active
                  ? 'border-gold bg-gold/15 text-ink shadow-[0_0_14px_-6px_rgba(212,175,55,0.5)]'
                  : 'border-rim-soft bg-surface text-ink-muted hover:text-ink'
              }`}
            >
              <span className={`numeric ${active ? 'text-gold-bright' : 'text-gold-soft'}`}>{path.number}</span>
              <span className="text-sm leading-none">{path.letter}</span>
              <span>{path.tarot_zh}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
