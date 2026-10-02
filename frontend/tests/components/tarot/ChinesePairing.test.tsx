/**
 * 塔罗 `_zh` 的呈现（丁组 spec §6.4、§8；G17「中文在上、原文降脚注」）。
 *
 * 四种凭据各管各的，读的时候别混（形状照 `tests/components/lenormand/PlainSummary.test.tsx`）：
 * **渲染凭据**管 DOM——中文主体与英文脚注**两处都在**、中文在前；这只有渲染量得到，
 * 源码扫量不到「删掉英文那一行」以外的搬动。
 * **源码扫凭据**管挂点与「不产句子」——页面/组件里不许出现自己拼的中文整句，也不许再出现
 * 手抄的英文牌阵描述（G18）；两处次序一律经 `pinLiteralOrder` 下，因为 `indexOf` 在字面
 * 缺席时返回 -1，只钉次序不先钉存在性会假绿（口径记在 ledger 的 `6379a74` 那条）。
 * **夹具内容凭据**：`tables` 的行序就是页面上的展示契约；目录漂移钉把夹具那一阵的
 * `spread_id` / `spread_name_zh` / `cards.length` 与 `SPREAD_CATALOG` 里同 id 条目逐字对上
 * ——残留的两份阵名（偏差表第 8 行）就靠这一条看着。
 * **查不到**：语义忠实（中文是不是说歪了）与视觉效果（脚注的字有多小、折不折行）——
 * 前者走 T8 Step 7 的人工走查并逐条贴对，后者要浏览器。
 * 复测：cd frontend && npx vitest run tests/components/tarot/ChinesePairing.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { CardInspector } from '../../../src/components/tarot/CardInspector';
import { SpreadSummary } from '../../../src/components/tarot/SpreadSummary';
import { SPREAD_CATALOG } from '../../../src/lib/tarot';
import type { TarotSpreadResponse } from '../../../src/types/tarot';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';

// 路径必须先拼成变量再交给 `new URL`：本文件走 jsdom 环境的客户端资源改写，字面量形式会在
// 转译期被改成 dev-server 的 `http:` 资源地址，读文件即 ENOENT（`tests/lib/readFixture.ts:12-27`）。
const PAGE = '../../../src/pages/TarotPage.tsx';
const CONTROLS = '../../../src/components/tarot/SpreadControls.tsx';
const INSPECTOR = '../../../src/components/tarot/CardInspector.tsx';

const spread = readFixture('tarot') as TarotSpreadResponse;

afterEach(cleanup);

describe('塔罗中英配对呈现', () => {
  it('夹具本身两半都齐：156 格里本次抽到的每一格都有中文', () => {
    expect(spread.spread_description_zh).toBeTruthy();
    expect(spread.spread_description_zh).not.toBe(spread.spread_description);
    for (const card of spread.cards) {
      expect(card.meaning_zh).toBeTruthy();
      expect(card.meaning_zh).not.toBe(card.meaning);
      expect(card.position_meaning_zh).toBeTruthy();
      expect(card.keywords_zh).toHaveLength(card.keywords.length);
      expect(card.keywords_zh).not.toEqual(card.keywords);
    }
  });

  it('综合解读是中文整段，且带本次那个阵的中文原名', () => {
    expect(spread.synthesis).toContain('布阵');
    expect(spread.synthesis).toContain(`${spread.spread_name_zh}（${spread.spread_name}）`);
  });

  it('牌义：中文在上、英文原句在下的两行都在 DOM 里', () => {
    const card = spread.cards[0];
    const { container } = render(<CardInspector card={card} />);
    const text = container.textContent ?? '';
    expect(text).toContain(card.meaning_zh);
    expect(text).toContain(card.meaning);
    expect(text.indexOf(card.meaning_zh)).toBeLessThan(text.indexOf(card.meaning));
  });

  it('宫位释义与关键词同样中文在前、英文在后', () => {
    const card = spread.cards[1];
    const { container } = render(<CardInspector card={card} />);
    const text = container.textContent ?? '';
    expect(text).toContain(card.position_meaning_zh);
    expect(text.indexOf(card.position_meaning_zh)).toBeLessThan(text.indexOf(card.position_meaning));
    for (const keyword of card.keywords_zh) expect(text).toContain(keyword);
    for (const keyword of card.keywords) expect(text).toContain(keyword);
  });

  it('牌阵摘要中文描述在上、英文在下', () => {
    const { container } = render(<SpreadSummary spread={spread} />);
    const text = container.textContent ?? '';
    expect(text).toContain(spread.spread_description_zh);
    expect(text.indexOf(spread.spread_description_zh)).toBeLessThan(text.indexOf(spread.spread_description));
    expect(text).toContain(spread.spread_name_zh);
  });

  it('页面把表清单挂进出处块，选择器不再自带英文描述', () => {
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    const controls = readFileSync(fileURLToPath(new URL(CONTROLS, import.meta.url)), 'utf8');
    expect(page).toContain('<ProvenancePanel tables={spread.provenance.tables} />');
    // 锚点用**看得见的字**：塔罗这一块自己的标题是「洗牌溯源与免责」（`TarotPage.tsx:202`），
    // 别照 LenormandPage 的「抽牌溯源与口径」抄——那两个块的标题本来就不一样。
    pinLiteralOrder(page, ['洗牌溯源与免责', '<ProvenancePanel tables=']);
    // 目录不产句子（G18）：选择器里既没有 `spread.description` 也没有 `spread.name}`。
    expect(controls).not.toContain('spread.description');
    expect(controls).not.toContain('spread.name}');
  });

  it('目录只剩三个字段，且与夹具那一阵逐字相等（漂移钉）', () => {
    const entry = SPREAD_CATALOG.find((item) => item.id === spread.spread_id);
    if (!entry) throw new Error(`目录里没有夹具那一阵 ${spread.spread_id}`);
    expect(Object.keys(entry).sort()).toEqual(['id', 'name_zh', 'size']);
    expect(entry.name_zh).toBe(spread.spread_name_zh);
    expect(entry.size).toBe(spread.cards.length);
  });

  it('inspector 源码里中文主体那两行的字面形状', () => {
    const inspector = readFileSync(fileURLToPath(new URL(INSPECTOR, import.meta.url)), 'utf8');
    expect(inspector).toContain('{card.meaning_zh}');
    expect(inspector).toContain('{card.position_meaning_zh}');
    expect(inspector).toContain('card.keywords_zh.map');
    pinLiteralOrder(inspector, ['{card.meaning_zh}', '{card.meaning}']);
  });
});
