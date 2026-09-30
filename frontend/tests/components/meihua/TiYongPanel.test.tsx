/**
 * 体用面板的阅读顺序测：白话整段必须排在技术判语之前，且整段逐字进 DOM。
 *
 * 钉三件事：① `plain_summary` 整段进 `PlainProse` 的那一个 `<p>`，文本全等、行数为七
 * （`whitespace-pre-line` 负责把七行显示出来，DOM 里不是一个 `<p>` 一行）；
 * ② DOM 序上白话整段在 `tiyong.text` 之前（spec §10「白话在上、原判语降为脚注」）；
 * ③ 夹具原文索引 4 那句逐字是艮的类象句——语料一改这条即红，逼着改动同时过一遍人审；面板的搬运由第一条整体钉住。
 *
 * 三条断言的口径统一说明：`PlainProse` 的契约是**一整段落进一个 `<p>`**
 * （`whitespace-pre-line` 负责换行显示），所以这里绝不能用 `paragraphByExact(单行)` 去找七个
 * 元素——找不到，`prose.ts` 那个定位件是抛错而不是返回 undefined，红法会让人误以为是语料变了。
 * 逐行只钉在数据侧（`split('\n')` 计数与按索引取全文），DOM 侧一律全文相等。第三条照 T6 的同类
 * 断言写成夹具原文字面量：语料一改它就红，红了要连带改这条测——这是有意的（spec §5 规则 7 的
 * 人审由这条测兜住一半）。
 *
 * 复测口径（2026-09-30 实算，报数 7、3 → 山火贲，体离用艮；重录夹具后于仓库根取）：
 * 七行 / 各行的字数与顺序是 0 开篇(61)、1 体生用(56)、2 离取象(92)、3 旺(52)、
 * 4 艮取象(90)、5 相(54)、6 中平收尾(55)——类象句在两侧各占一行，用侧那句是索引 4 而不是第二行。
 *   cd frontend && node -e "const c=require('./tests/fixtures/meihua.json');console.log(c.plain_summary.split(String.fromCharCode(10)).map(l=>l.length).join(' '))"
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { TiYongPanel } from '../../../src/components/meihua/TiYongPanel';
import type { MeihuaCast } from '../../../src/types/meihua';
import { paragraphByExact, precedes } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const cast = readFixture('meihua') as MeihuaCast;

afterEach(cleanup);

describe('TiYongPanel 白话区块', () => {
  it('plain_summary 整段进同一个 <p>：行数与后端一致、文本全等、不折不加', () => {
    render(<TiYongPanel cast={cast} />);
    const paragraph = paragraphByExact(cast.plain_summary);
    // 全文相等已由 paragraphByExact 的定位方式钉住，这里只钉行数与 pre-line。
    expect(cast.plain_summary.split('\n')).toHaveLength(7);
    expect(paragraph.className).toContain('whitespace-pre-line');
  });

  it('白话整段在技术判语之前被读到', () => {
    const { container } = render(<TiYongPanel cast={cast} />);
    const plain = paragraphByExact(cast.plain_summary);
    const technical = [...container.querySelectorAll('p')].find(
      (p) => p.textContent === cast.tiyong.text,
    );
    expect(technical).toBeTruthy();
    expect(precedes(plain, technical!)).toBe(true);
  });

  it('参考盘的用侧类象句逐字是艮那一句，落在索引 4（夹具：山火贲，体离用艮）', () => {
    expect(cast.plain_summary.split('\n')[4]).toBe(
      '艮取象为山，你在这一步见到的人是少年男子、小孩子、住山的人与修行之人，落在身上是手、指、背与鼻，方位在东北，物上是山石、门阙、果实与床，性子是静止稳重，也固执，事情到它这里就停住。',
    );
  });
});
