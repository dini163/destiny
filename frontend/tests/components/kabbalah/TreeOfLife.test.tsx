import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { TreeOfLife } from '../../../src/components/kabbalah/TreeOfLife';
import type { KabbalahTree } from '../../../src/types/kabbalah';
import { readFixture } from '../../lib/readFixture';

const tree = readFixture('kabbalah-tree') as KabbalahTree;

describe('TreeOfLife diagram', () => {
  it('separates path letters that share the same crossing', () => {
    const { container } = render(
      <TreeOfLife tree={tree} selection={null} onSelect={() => undefined} />,
    );
    const nodesByNumber = new Map(tree.sephiroth.map((node) => [node.number, node]));
    const pathsByMidpoint = new Map<string, string[]>();

    for (const path of tree.paths) {
      const from = nodesByNumber.get(path.from_sephirah);
      const to = nodesByNumber.get(path.to_sephirah);
      if (!from || !to) continue;
      const midpoint = `${(from.x + to.x) / 2}:${(from.y + to.y) / 2}`;
      pathsByMidpoint.set(midpoint, [...(pathsByMidpoint.get(midpoint) ?? []), path.id]);
    }

    const sharedCrossings = [...pathsByMidpoint.values()].filter((pathIds) => pathIds.length > 1);
    expect(sharedCrossings.length).toBeGreaterThan(0);

    for (const pathIds of sharedCrossings) {
      const positions = pathIds.map((pathId) => {
        const group = container.querySelector(`[data-path-id="${pathId}"]`);
        const label = group?.querySelector('.kabbalah-path-letter');
        return [Number(label?.getAttribute('x')), Number(label?.getAttribute('y'))] as const;
      });
      expect(new Set(positions.map(([x, y]) => `${x}:${y}`)).size).toBe(pathIds.length);
      for (let left = 0; left < positions.length; left += 1) {
        for (let right = left + 1; right < positions.length; right += 1) {
          const distance = Math.hypot(
            positions[left][0] - positions[right][0],
            positions[left][1] - positions[right][1],
          );
          expect(distance).toBeGreaterThan(5.4);
        }
      }
    }
  });
});
