/**
 * 生命之树响应必须按源表原序递出：`grouping="keep"` 的全部前提是「次序由调用方决定」，
 * 而卡巴拉的调用方就是 `engines/kabbalah.py` 里 `build_tree` 的列表推导。
 * 白话表本身无序（dict），所以次序错乱不会被任何后端测抓到——只有这条会。
 * 复测：cd frontend && npx vitest run tests/components/kabbalah/NodeOrder.test.tsx
 */
import { describe, expect, it } from 'vitest';

import type { KabbalahTree } from '../../../src/types/kabbalah';
import { readFixture } from '../../lib/readFixture';

const tree = readFixture('kabbalah-tree') as KabbalahTree;

describe('生命之树的节点次序', () => {
  it('原质按 1→10 的源表序，路径按 11→32 的源表序', () => {
    expect(tree.sephiroth.map((n) => n.id)).toEqual(
      Array.from({ length: 10 }, (_, i) => `sephirah-${i + 1}`),
    );
    expect(tree.paths.map((n) => n.id)).toEqual(
      Array.from({ length: 22 }, (_, i) => `path-${i + 11}`),
    );
    expect(tree.sephirah_count).toBe(10);
    expect(tree.path_count).toBe(22);
  });

  it('Daath 在 sephiroth 之外单独递出，不进上面两条序列', () => {
    if (tree.daath === null) throw new Error('夹具里没有 Daath：录制跑歪或 T3 的必填闸没生效');
    expect(tree.daath.id).toBe('daath');
    expect(tree.sephiroth.map((n) => n.id)).not.toContain('daath');
  });
});
