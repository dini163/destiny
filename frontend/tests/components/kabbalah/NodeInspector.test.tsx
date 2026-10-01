/**
 * 卡巴拉详情面板的白话挂点（多系统白话 spec §10「清单类就地嵌」）。
 *
 * 钉三件事：① 白话在原判语**之上**且文本全等于响应字段（不用子串匹配——子串会让
 * 「白话没渲染、只剩脚注」这种半坏状态混过去）；② 原质与路径**两个**分支都挂
 * （`NodeInspector.tsx` 有两个同形 `<p>{node.meaning}</p>`，只改一处就漏掉 22 条路径）；
 * ③ 33 个节点在树响应里全部带白话，缺一个就是后端 T3 的必填闸没守住。
 * 复测：cd frontend && npx vitest run tests/components/kabbalah/NodeInspector.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { NodeInspector } from '../../../src/components/kabbalah/NodeInspector';
import type { KabbalahTree } from '../../../src/types/kabbalah';
import { paragraphByExactIn, precedes } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const tree = readFixture('kabbalah-tree') as KabbalahTree;

afterEach(cleanup);

function text(container: HTMLElement): string {
  return container.textContent ?? '';
}

describe('NodeInspector 白话', () => {
  it('原质分支：白话整句在原判语之上', () => {
    const node = tree.sephiroth[0];
    const { container } = render(<NodeInspector resolved={{ kind: 'sephirah', node }} />);
    expect(node.plain_meaning.length).toBeGreaterThan(40);
    expect(text(container)).toContain(node.plain_meaning);
    expect(text(container)).toContain(node.meaning);
    // 全文相等 + 容器内定位（`tests/lib/prose.ts` 的两件都是为这一刻存在的：子串匹配会让
    // 「白话没渲染、只剩脚注」混过去，而卡巴拉的判语句在两个分支里长得一样）。
    expect(precedes(paragraphByExactIn(container, node.plain_meaning), paragraphByExactIn(container, node.meaning))).toBe(true);
  });

  it('路径分支：白话整句在原判语之上', () => {
    const node = tree.paths[0];
    const { container } = render(<NodeInspector resolved={{ kind: 'path', node }} />);
    expect(node.plain_meaning.length).toBeGreaterThan(40);
    expect(text(container)).toContain(node.plain_meaning);
    expect(precedes(paragraphByExactIn(container, node.plain_meaning), paragraphByExactIn(container, node.meaning))).toBe(true);
  });

  it('树响应里 33 个节点全部带白话', () => {
    // `types/kabbalah.ts:87` 是 `daath: SephirahNode | null`（后端 `schemas/kabbalah.py:93` 给了
    // default=None），所以这里先把 null 变成一条会说的失败，而不是让循环在 null 上崩成
    // 「TypeError: Cannot read properties of null」。引擎今天总是递出 Daath（`build_tree`），
    // null 只可能来自夹具录歪或 T3 的必填闸没守住。
    if (tree.daath === null) throw new Error('夹具里没有 Daath：要么录制跑歪，要么 T3 的白话必填闸没生效');
    const nodes = [...tree.sephiroth, tree.daath, ...tree.paths];
    expect(nodes).toHaveLength(33);
    for (const node of nodes) {
      expect(node.plain_meaning.length).toBeGreaterThan(40);
      expect(node.plain_meaning).not.toBe(node.meaning);
    }
  });
});
