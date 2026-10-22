/**
 * 塔罗 `_zh` 的呈现（丁组 spec §6.4、§8；G17「中文在上、原文降脚注」）。
 *
 * 四种凭据各管各的，读的时候别混（形状照 `tests/components/lenormand/PlainSummary.test.tsx`）：
 * **渲染凭据**管 DOM——中文主体与英文脚注**两处都在**、中文在前；次序这一半同样走
 * `pinLiteralOrder`（G24：前端顺序钉一律走那个 helper，不分源码/DOM——`container.textContent`
 * 就是普通 `string`，helper 只吃字符串、不认结构，正好够用）。存在性由 helper 自带两遍
 * `toContain`，所以这三处不再另写，手写 `indexOf` 比较一处都不留。
 * 源码扫量不到「删掉英文那一行」以外的搬动，故 DOM 侧的次序必须由这一路来量。
 * **源码扫凭据**管挂点与「目录不产句子」——选择器里不许再出现手抄的英文牌阵描述（G18），
 * 挂点次序一律经 `pinLiteralOrder` 下，因为 `indexOf` 在字面缺席时返回 -1，只钉次序不先钉存在性
 * 会假绿（口径记在 ledger 的 `6379a74` 那条）。**同一句里没钉的那一半要说清**：「前端不许自己
 * 拼中文整句」在这两件上钉不住——`SpreadControls.tsx:146-148` 的牌阵说明与随机源口径**本来就该**
 * 是界面文案（那是 UI 话术，不是牌义语料），任何**正向**字面扫描都会把它误判成违规；本期削掉的是
 * 「抄来的英文语料」，不是「界面自己的中文」，后者由人工走查看。这一族只有一条**负向**钉（不许把
 * 「综合解读」说成取自牌库——页面已原样印引擎的 `note`，第二份手抄正是 R37 抓过的那类漂移），
 * 它锁的是「不许说什么」，不锁「怎么说」。
 * **夹具内容凭据**：`tables` 的行序就是这份清单自己的展示契约（面板按数组渲染，与
 * `lenormand`/`qimen`/`ziwei` 那三家同一条形状，五行顺序改了必须红在这里）；溯源块已按
 * 2026-10-21 UI 需求从页面移除，「前端把这四行递给面板」那半截凭据不再记挂；目录漂移钉把夹具那一阵的 `spread_id` /
 * `spread_name_zh` / `cards.length` 与 `SPREAD_CATALOG` 里同 id 条目逐字对上
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
      expect(card.position_meaning_zh).not.toBe(card.position_meaning);
      expect(card.position_label_zh).not.toBe(card.position_label);
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
    // 渲染出来的 `textContent` 也是普通 `string`，所以次序钉同样走 `pinLiteralOrder`
    // （G24 那句「前端顺序钉一律走 helper」不分源码/DOM，手写 `indexOf` 比较两处都不许）：
    // helper 自带两侧锚点的存在性钉，原来那两条 `toContain` 就是重复，删。
    const text = container.textContent ?? '';
    pinLiteralOrder(text, [card.meaning_zh, card.meaning]);
  });

  it('宫位释义与关键词同样中文在前、英文在后', () => {
    const card = spread.cards[1];
    const { container } = render(<CardInspector card={card} />);
    const text = container.textContent ?? '';
    pinLiteralOrder(text, [card.position_meaning_zh, card.position_meaning]);
    for (const keyword of card.keywords_zh) expect(text).toContain(keyword);
    // 英文那行走**整串**而不是逐词：本次夹具里 `scarcity` 同时出现在那张牌的英文牌义句中
    // （`content/tarot_minor.py` 的 "or a scarcity mindset"），逐词 `toContain` 在 chips 与脚注两行
    // 都被删掉时照样绿；带上分隔符拼整串就只认脚注那一行。
    expect(text).toContain(card.keywords.join(' · '));
  });

  it('牌阵摘要中文描述在上、英文在下', () => {
    const { container } = render(<SpreadSummary spread={spread} />);
    const text = container.textContent ?? '';
    pinLiteralOrder(text, [spread.spread_description_zh, spread.spread_description]);
    expect(text).toContain(spread.spread_name_zh);
  });

  it('选择器不再自带英文描述；页面溯源块已按 2026-10-21 UI 需求移除', () => {
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    const controls = readFileSync(fileURLToPath(new URL(CONTROLS, import.meta.url)), 'utf8');
    // 溯源块（「洗牌溯源与免责」标题、`<Provenance>`、`<ProvenancePanel>`）已按 2026-10-21
    // UI 需求从页面移除，这里改钉「不出现」。
    expect(page).not.toContain('<ProvenancePanel');
    expect(page).not.toContain('<Provenance ');
    expect(page).not.toContain('洗牌溯源与免责');
    // 目录不产句子（G18）：选择器里既没有 `spread.description` 也没有 `spread.name}`。
    expect(controls).not.toContain('spread.description');
    expect(controls).not.toContain('spread.name}');
    // 出处口径的第二份手抄（终审发现 11）负向钉：不许把「综合解读」说成取自牌库——
    // 那正是 R37 抓的那类过度归因。负向钉，正向文案仍可自由改写（本文件头注里
    // 「同一句里没钉的那一半要说清」那一段对这半句依然成立）。
    expect(controls).not.toMatch(/综合解读[^。]*取自主策展/);
  });

  it('目录六个条目都只剩三个字段，且与夹具那一阵逐字相等（漂移钉）', () => {
    // 三键形状对**六个**条目都钉：只钉夹具那一阵的话，另外五阵哪天被塞回一份手抄描述也不会红，
    // 而 G18 管的是整个目录。逐字对账（`name_zh` 与 `size`）只能覆盖夹具抽到的那一阵（偏差表第 8 行），
    // 其余五阵要目录端点才有得对，这条限度不藏在这里。
    for (const item of SPREAD_CATALOG) {
      expect(Object.keys(item).sort()).toEqual(['id', 'name_zh', 'size']);
    }
    const entry = SPREAD_CATALOG.find((item) => item.id === spread.spread_id);
    if (!entry) throw new Error(`目录里没有夹具那一阵 ${spread.spread_id}`);
    expect(entry.name_zh).toBe(spread.spread_name_zh);
    expect(entry.size).toBe(spread.cards.length);
  });

  it('夹具里的五行出处按展示序排列', () => {
    // 行序=展示序（`components/ui/ProvenancePanel.tsx` 的 `tables.map`），所以钉的是等序列表不是集合；
    // 后端 golden 钉的是同一份清单的另一头（`backend/tests/golden/test_tarot_golden.py` 那条五行等序钉），
    // 与 `lenormand`/`qimen`/`ziwei` 三家同形状。第五行 `tarot_polarity` 是 verdict 吉凶倾向表。
    // 这一条**只钉夹具那五行自己的展示序**（测体读的是 `readFixture('tarot')` 的 JSON，把
    // `TarotPage.tsx` 改坏不会红在这里）。溯源块已按 2026-10-21 UI 需求从页面移除，
    // 「前端把这五行递给面板」那半截凭据随之作废，不再在此记挂。
    expect(spread.provenance.tables.map((table) => table.name)).toEqual([
      'tarot_major',
      'tarot_minor',
      'tarot_deck',
      'tarot_keywords_zh',
      'tarot_polarity',
    ]);
  });

  it('inspector 源码里中文主体那两行的字面形状', () => {
    const inspector = readFileSync(fileURLToPath(new URL(INSPECTOR, import.meta.url)), 'utf8');
    expect(inspector).toContain('{card.meaning_zh}');
    expect(inspector).toContain('{card.position_meaning_zh}');
    expect(inspector).toContain('card.keywords_zh.map');
    pinLiteralOrder(inspector, ['{card.meaning_zh}', '{card.meaning}']);
  });
});
