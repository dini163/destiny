/**
 * 塔罗整幅牌面图案（CardArt）渲染凭据。
 *
 * 图案现在是位图优先：每张牌按 card_id 指向 `/cards/tarot/<card_id>.jpg`
 * 的生成插画；图片缺失或加载失败时回退到确定性矢量牌面（CardArtSvg）。
 * 凭据钉：① 默认渲染位图且路径正确；② onError 后回退矢量；③ 矢量兜底仍覆盖
 * 22 张大阿卡纳 + 56 张小阿卡纳全部渲染不抛错，并抽查愚人（太阳/山崖）、
 * 月亮（月牙）、高塔（闪电）、权杖 5（五个 pip）。
 * 复测：cd frontend && npx vitest run tests/components/tarot/CardArt.test.tsx
 */
import { cleanup, fireEvent, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { CardArt } from '../../../src/components/tarot/CardArt';
import { MAJOR_ART } from '../../../src/components/tarot/arcanaArt';
import type { DrawnCard, TarotSuit } from '../../../src/types/tarot';

/** A minimal drawn card; only fields that drive the artwork are set. */
function makeCard(overrides: Partial<DrawnCard>): DrawnCard {
  return {
    position_index: 0,
    position_key: 'single',
    position_label: 'single',
    position_label_zh: '单张',
    position_meaning: '',
    position_meaning_zh: '',
    card_id: 'major-00',
    name: 'The Fool',
    name_zh: '愚人',
    arcana: 'major',
    number: 0,
    suit: null,
    rank: null,
    element: null,
    orientation: 'upright',
    keywords: [],
    keywords_zh: [],
    meaning: '',
    meaning_zh: '',
    ...overrides,
  };
}

const SUITS: TarotSuit[] = ['wands', 'cups', 'swords', 'pentacles'];

/** Render the card then force the vector fallback, so SVG assertions stay stable. */
function renderVector(card: DrawnCard) {
  const view = render(<CardArt card={card} />);
  const img = view.container.querySelector('img');
  expect(img).not.toBeNull();
  fireEvent.error(img!);
  return view;
}

afterEach(cleanup);

describe('塔罗整幅牌面图案', () => {
  it('默认渲染位图，路径按 card_id 指向 /cards/tarot/*.jpg', () => {
    const { container } = render(<CardArt card={makeCard({ card_id: 'swords-07' })} />);
    const img = container.querySelector('img');
    expect(img).not.toBeNull();
    expect(img!.getAttribute('src')).toBe('/cards/tarot/swords-07.jpg');
    // 位图用于装饰，不暴露可读文本给读屏器
    expect(img!.getAttribute('aria-hidden')).toBe('true');
  });

  it('位图加载失败时回退到矢量牌面', () => {
    const { container } = render(<CardArt card={makeCard({ card_id: 'wands-01' })} />);
    fireEvent.error(container.querySelector('img')!);
    expect(container.querySelector('svg')).not.toBeNull();
    expect(container.querySelector('img')).toBeNull();
  });

  it('22 张大阿卡纳每张都有意象可画', () => {
    for (let number = 0; number <= 21; number += 1) {
      expect(MAJOR_ART[number]?.length ?? 0).toBeGreaterThan(0);
      const { container } = renderVector(
        makeCard({ number, card_id: `major-${String(number).padStart(2, '0')}` }),
      );
      // 意象至少画出一个形状；世界（21）全由圆环构成，故不能只查 path
      const shapes = container.querySelectorAll('path, circle').length;
      expect(shapes).toBeGreaterThan(1); // 光晕 circle + 至少一个意象形状
    }
  });

  it('56 张小阿卡纳全部渲染不抛错（4 花色 × 14 号位）', () => {
    for (const suit of SUITS) {
      for (let number = 1; number <= 14; number += 1) {
        const rank = number >= 11 ? (['Page', 'Knight', 'Queen', 'King'] as const)[number - 11] : null;
        const { container } = renderVector(
          makeCard({
            arcana: 'minor',
            suit,
            number,
            rank,
            card_id: `${suit}-${String(number).padStart(2, '0')}`,
          }),
        );
        // 数字牌至少画出 count 个 pip 的骨架（path/circle 数 ≥ count）
        const shapes = container.querySelectorAll('path, circle').length;
        expect(shapes).toBeGreaterThanOrEqual(rank ? 2 : number);
      }
    }
  });

  it('愚人画出行囊杖与远方太阳', () => {
    const { container } = renderVector(makeCard({ number: 0 }));
    const html = container.innerHTML;
    expect(html).toContain('M36 112 L46 60'); // 斜杖
    expect(html).toContain('cx="76" cy="46"'); // 小太阳
    expect(html).toContain('Q50 96 86 110'); // 山崖
  });

  it('月亮画出一弯月牙', () => {
    const { container } = renderVector(makeCard({ number: 18 }));
    expect(container.innerHTML).toContain('a12 12 0 1 0 0 26');
  });

  it('高塔画出塔身与闪电', () => {
    const { container } = renderVector(makeCard({ number: 16 }));
    const html = container.innerHTML;
    expect(html).toContain('L40 62 H60'); // 塔身
    expect(html).toContain('L47 94 h9'); // 闪电折线
  });

  it('权杖 5 画出五根权杖的五个 pip', () => {
    const { container } = renderVector(
      makeCard({ arcana: 'minor', suit: 'wands', number: 5 }),
    );
    const html = container.innerHTML;
    // 五个锚点各画出一根权杖（竖线），五处都应在场
    for (const [x, y] of [
      [36, 62],
      [64, 62],
      [50, 80],
      [36, 98],
      [64, 98],
    ]) {
      expect(html).toContain(`M${x} ${y - 7} V${y + 7}`);
    }
  });
});
