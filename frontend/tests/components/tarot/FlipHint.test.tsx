/**
 * Lead-card flip nudge on the spread board.
 *
 * A face-down back can read as a blank front, so the first position tilts
 * periodically until the reader turns a card. The motion itself lives in CSS
 * and is only observable in a browser; this pins the two DOM rules that decide
 * when it runs: the lead card alone carries the hint, and any first flip stops
 * it for the whole spread.
 *
 * Re-run: cd frontend && npx vitest run tests/components/tarot/FlipHint.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SpreadBoard } from '../../../src/components/tarot/SpreadBoard';
import type { TarotSpreadResponse } from '../../../src/types/tarot';
import { readFixture } from '../../lib/readFixture';

const spread = readFixture('tarot') as TarotSpreadResponse;
const noop = (): void => {};

afterEach(cleanup);

function board(revealed: ReadonlySet<number>) {
  return render(
    <SpreadBoard
      cards={spread.cards}
      revealed={revealed}
      selected={null}
      onCardSelect={noop}
    />,
  );
}

describe('首张牌的翻转提示', () => {
  it('牌阵未动时只有第一张牌带提示', () => {
    const { container } = board(new Set());
    const hints = container.querySelectorAll('.tarot-card-hint');
    expect(hints).toHaveLength(1);
    expect(hints[0].closest('button')?.getAttribute('aria-label')).toContain('第 1 张');
  });

  it('任意一张牌翻开后，整个牌阵不再提示', () => {
    const { container } = board(new Set([2]));
    expect(container.querySelectorAll('.tarot-card-hint')).toHaveLength(0);
  });
});
