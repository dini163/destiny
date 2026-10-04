/**
 * 周易今译的就地呈现（丁组 spec §5、§8；G17「今译在上、原句降脚注」）。
 *
 * 四种凭据各管各的，读的时候别混（形状照 `tests/components/tarot/ChinesePairing.test.tsx`）：
 * **渲染凭据**管 DOM——今译与原句两处都在、今译在前。次序同样走 `pinLiteralOrder`
 * （G24：前端顺序钉一律走那个 helper，不分源码/DOM——`container.textContent` 就是普通
 * `string`，helper 只吃字符串、不认结构，存在性由它自带的两遍 `toContain` 负责）。
 * **源码扫凭据**管挂点：页面把五张表递给 `ProvenancePanel`、两件里今译走 `PlainProse`。
 * **夹具内容凭据**：`tables` 的行序就是本页的展示契约（面板按数组渲染，与 tarot /
 * lenormand / qimen / ziwei 四家同形状）；夹具是 `scripts/record_frontend_fixtures.py`
 * 打真实 `:8000` 录的那一手（`CastMethod.MANUAL` + 固定六掷 → 丰 55 之咸 31、互卦大过 28），
 * 与后端 `test_bian_and_hu_carry_their_own_plain_gua_ci` 同一条链的两头。
 * **限度**：夹具那一手是 55 卦，`yong_ci` 与 `plain_yong_ci` 都是 null，所以用九/用六那一支
 * 今天没有 DOM 正面可吃——它由「后端乾那一手的 golden」+ 本文件最后那条源码扫两头夹住。
 * **查不到**：今译是否说歪了（语义忠实，要人逐条对经文）与脚注的字够不够小（要浏览器）。
 * 复测：cd frontend && npx vitest run tests/components/zhouyi/PlainReadings.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ClassicalText } from '../../../src/components/zhouyi/ClassicalText';
import { HexagramCard } from '../../../src/components/zhouyi/HexagramCard';
import type { ZhouyiCast } from '../../../src/types/zhouyi';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';

// 路径必须先拼成变量再交给 `new URL`：本文件走 jsdom 环境的客户端资源改写，字面量形式会在
// 转译期被改成 dev-server 的 `http:` 资源地址，读文件即 ENOENT（`tests/lib/readFixture.ts:12-27`）。
const PAGE = '../../../src/pages/ZhouyiPage.tsx';
const TEXT = '../../../src/components/zhouyi/ClassicalText.tsx';
const CARD = '../../../src/components/zhouyi/HexagramCard.tsx';

const cast = readFixture('zhouyi') as ZhouyiCast;

afterEach(cleanup);

describe('周易就地今译与出处块', () => {
  it('夹具三张卦都带自己的今译，且今译不等于原句', () => {
    for (const hexagram of [cast.ben, cast.hu]) {
      expect(hexagram.plain_gua_ci).toBeTruthy();
      expect(hexagram.plain_gua_ci).not.toBe(hexagram.gua_ci);
    }
    if (cast.bian) {
      expect(cast.bian.plain_gua_ci).toBeTruthy();
      expect(cast.bian.plain_gua_ci).not.toBe(cast.bian.gua_ci);
    }
    // 55 卦没有用九/用六：这一格是 null 而不是空串（spec §5「忠实的缺席」）。
    expect(cast.ben.yong_ci).toBeNull();
    expect(cast.ben.plain_yong_ci).toBeNull();
  });

  it('六条爻的今译齐备，一条也不许退化成原句', () => {
    expect(cast.lines).toHaveLength(6);
    for (const line of cast.lines) {
      expect(line.plain_yao_ci).toBeTruthy();
      expect(line.plain_yao_ci).not.toBe(line.yao_ci);
      expect(line.plain_yao_ci.length).toBeGreaterThan(line.yao_ci.length);
    }
  });

  it('卦爻辞面板：卦辞今译在上、原句在后，六条爻逐条同序', () => {
    const { container } = render(<ClassicalText ben={cast.ben} lines={cast.lines} />);
    const text = container.textContent ?? '';
    pinLiteralOrder(text, [cast.ben.plain_gua_ci, cast.ben.gua_ci]);
    for (const line of cast.lines) {
      pinLiteralOrder(text, [line.yao_name, line.plain_yao_ci, line.yao_ci]);
    }
    // 用九/用六那一支今天无夹具（头注「限度」）：至少钉它不许在这一手上冒出来。
    expect(text).not.toContain('用九');
    expect(text).not.toContain('用六');
  });

  it('变卦与互卦的卦辞行同样今译在上、原句在后', () => {
    if (!cast.bian) throw new Error('夹具那一手有动爻，变卦不该为空');
    for (const hexagram of [cast.bian, cast.hu]) {
      // `render` 的返回值在 RTL 16 里没有 `cleanup`（那是模块级导出，本文件已由顶部
      // `afterEach(cleanup)` 统一装）；两张卡各得各的 `container`，文本互不污染，
      // 所以循环里不必逐次拆——复测：`cd frontend && npx tsc -b --noEmit`。
      const { container } = render(<HexagramCard hexagram={hexagram} />);
      pinLiteralOrder(container.textContent ?? '', [hexagram.plain_gua_ci, hexagram.gua_ci]);
    }
  });

  it('页面把五张表递给出处块，展示序就是清单序', () => {
    expect(cast.provenance.tables.map((table) => table.name)).toEqual([
      'zhouyi_trigrams',
      'zhouyi_hexagrams',
      'zhouyi_najia',
      'zhouyi_text',
      'zhouyi_plain',
    ]);
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    expect(page).toContain('<ProvenancePanel tables={cast.provenance.tables} />');
    pinLiteralOrder(page, ['起卦溯源与免责', '<ProvenancePanel tables=', '历法 · ']);
    // 两个同名不同职的 `engine`（顶层 = 本端点推导器名，`provenance.engine` = 历法库）不许混成
    // 一句话：历法那一格只能出现在面板之下的小字行里。三锚点形状照雷诺曼那一家的先例
    // （`tests/components/lenormand/PlainSummary.test.tsx:83`）。
    expect(page).toContain('历法 · {cast.provenance.engine}');
    // 出处口径不许有两份手抄（R37 那一类）：页面正文那段说「依《周易》通行本与京房纳甲法
    // 真实推演」，具体是哪五张表一律由面板从响应渲染，源码里不许出现表名。
    expect(page).not.toContain('zhouyi_plain');
  });

  it('两件里今译走 PlainProse、原句降脚注，且今译在前', () => {
    const text = readFileSync(fileURLToPath(new URL(TEXT, import.meta.url)), 'utf8');
    const card = readFileSync(fileURLToPath(new URL(CARD, import.meta.url)), 'utf8');
    expect(text).toContain('<PlainProse text={ben.plain_gua_ci} />');
    expect(text).toContain('<PlainProse text={line.plain_yao_ci}');
    expect(card).toContain('<PlainProse text={hexagram.plain_gua_ci} />');
    pinLiteralOrder(text, ['{ben.plain_gua_ci}', '{ben.gua_ci}']);
    pinLiteralOrder(text, ['{line.plain_yao_ci}', '{line.yao_ci}']);
    pinLiteralOrder(card, ['{hexagram.plain_gua_ci}', '{hexagram.gua_ci}']);
    // 用九/用六那一支夹具吃不到（头注「限度」），所以它的今译/原句两头都由源码扫钉：
    // 只钉 `{ben.gua_ci}` 的话，删掉 `{ben.plain_yong_ci}` 那一行没人管得住。
    expect(text).toContain('<PlainProse text={ben.plain_yong_ci} />');
    expect(card).toContain('<PlainProse text={hexagram.plain_yong_ci} />');
    pinLiteralOrder(text, ['{ben.plain_yong_ci}', '{ben.yong_ci}']);
    pinLiteralOrder(card, ['{hexagram.plain_yong_ci}', '{hexagram.yong_ci}']);
    // 用九/用六的 title 仍由 `number === 1` 派生（偏差表第 6 行：本期不动它）。
    expect(text).toContain("ben.number === 1 ? '用九' : '用六'");
    expect(card).toContain("hexagram.number === 1 ? '用九' : '用六'");
  });
});
