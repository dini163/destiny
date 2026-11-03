/**
 * 本命页「白话详解」块（戊组 spec §9；用户 2026-10-04 裁定第 3 条：页尾汇总块，
 * 图/网格/表格一律不动；2026-10-21 UI 需求：数据溯源块已从页面移除）。母本是
 * `tests/components/ziwei/ZiweiPlainSections.test.tsx`。
 *
 * 三种凭据各管各的，读的时候别混：
 * **渲染凭据**（第 1、2 条）管 `PlainSectionList` 拿到真实八段后排成什么：八段齐、序对、
 *   逐字节，且这一件不加一个字、不把多行拆成多段。
 * **夹具内容凭据**（第 4 条）管响应：`tables` 的行序就是本页的展示契约，与后端 golden
 *   `test_the_provenance_tables_are_the_three_plain_modules_in_order` 是同一条链的两头。
 * **源码扫凭据**（第 3 条）管挂点：页面真把 `chart.plain` 递进来了吗、溯源块是否已按
 *   2026-10-21 UI 需求移除、那句已被本轮推翻的「未作主观吉凶演绎」退役了吗。
 *
 * **限度**（写在测里而不是留给读者猜）：夹具是 `scripts/record_frontend_fixtures.py` 打的
 * J2000 格林尼治那一手（`utc_offset_hours=0.0`，与后端 `_greenwich_chart()` 同盘），八段全非空、
 * 逆行 1 颗。**零相位那一支本测吃不到**——今天没有一份真盘是零相位（地基表实测最少 11 条），
 * 它由后端 golden 的构造分支钉（偏差 14），不在前端重复。
 * **查不到**：542 条判语是否说歪了（语义忠实要评审人逐段读）、这段长文在真机上的读感（走查）。
 * 复测：cd frontend && npx vitest run tests/components/western/WesternPlainSections.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
import { VerdictCard } from '../../../src/components/ui/VerdictCard';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';
import type { WesternChart } from '../../../src/types/western';

afterEach(cleanup);

const chart = readFixture('western-natal') as WesternChart;

/** 挂点测走 jsdom 的客户端资源改写，`new URL` 的参数必须先成变量（`tests/lib/readFixture.ts:12-27` 的实录陷阱）。 */
const PAGE = '../../../src/pages/WesternNatalPage.tsx';

/** 八段的展示序 = `build_plain` 里八个 `emit(…)` 的序，也是 `WESTERN_SECTION_TITLES` 的序。
 *  在这里逐字钉而不是从夹具推给自己看：少一段（有人改了 `emit` 却没删标题）只有字面清单能红。 */
const SECTION_TITLES = [
  '十星落座',
  '十星落宫',
  '主要相位',
  '逆行诸星',
  '上升与天顶',
  '北交点',
  '十二宫主题',
  '元素与形态',
];

it('the eight sections arrive in roster order and render byte for byte', () => {
  expect(chart.plain.map((section) => section.title)).toEqual(SECTION_TITLES);
  const { container } = render(<PlainSectionList sections={chart.plain} />);
  expect([...container.querySelectorAll('h3')].map((h) => h.textContent)).toEqual(SECTION_TITLES);
  expect([...container.querySelectorAll('p')].map((p) => p.textContent)).toEqual(
    chart.plain.map((section) => section.text),
  );
});

it('the block keeps every line break and adds no sentence of its own', () => {
  /** 第 1 条已经逐字比过文本；本条管的是**形状**：一段一个 `<p>`（前端不许把开篇句与逐条
   *  判语拆成多个 `<p>`，也不许把八段并成一个），且每个 `<p>` 带 `whitespace-pre-line`
   *  ——`spec §10` 给 `PlainProse` 立的禁区在丙组用一份手写两条的 `SECTIONS` 钉过
   *  （`tests/components/ui/PlainSectionList.test.tsx`），这里补的是**真实八段 63 行**那一手：
   *  手写夹具永远测不到「段数一多、行数一长就有人想拆」。 */
  const { container } = render(<PlainSectionList sections={chart.plain} />);
  const paragraphs = [...container.querySelectorAll('p')];
  expect(paragraphs).toHaveLength(chart.plain.length);
  // 断行是否真的到了 DOM：断 `paragraph.textContent` 而不是断夹具。
  // 断夹具的那一版（`chart.plain` 每段含 `\n`）恒真——评审实测把组件的 `{text}` 改成
  // `{text.replace(/\n/g, ' ')}` 时它照样全绿，而那条腿的标题恰恰叫 `keeps every line break`。
  for (const [index, section] of chart.plain.entries()) {
    // 每段都是「开篇句 + ≥1 条判语」，所以段内必有换行；零换行的那一段就是装配掉了条目。
    expect(section.text).toContain('\n');
    expect(paragraphs[index].textContent).toBe(section.text);
    expect(paragraphs[index].textContent?.split('\n')).toHaveLength(
      section.text.split('\n').length,
    );
  }
  for (const paragraph of paragraphs) {
    expect(paragraph.className).toContain('whitespace-pre-line');
  }
});

it('the page wires chart.plain under 白话详解, the provenance block is removed per the 2026-10-21 UI requirement, and the false disclaimer is gone', () => {
  const src = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  expect(src).toContain('<PlainSectionList sections={chart.plain} />');
  expect(src).toContain('title="白话详解"');
  // 页头英文类目 kicker 已按"去掉 eyebrow"的设计决策整体移除；白话详解卡只留中文标题。
  expect(src).not.toContain('eyebrow="PLAIN READING"');
  // 溯源块已按 2026-10-21 UI 需求移除：页面不得再出现 `<Provenance>` 组件（含共享面板的挂载）。
  expect(src).not.toContain('<Provenance');
  // 本轮上线的东西**就是**主观吉凶演绎（542 条自撰判语），这句留着就是页面上的假话（spec §1.1）。
  expect(src).not.toContain('未作主观吉凶演绎');
  pinLiteralOrder(src, [
    '<AspectMatrix planets={chart.planets} aspects={chart.aspects} />',
    '<PlainSectionList sections={chart.plain} />',
  ]);
});

it('the provenance panel is handed the three plain tables in roster order', () => {
  expect(chart.provenance.tables.map((table) => table.name)).toEqual([
    'western_plain',
    'western_plain_placement',
    'western_plain_aspect',
  ]);
  for (const table of chart.provenance.tables) {
    expect(table.version).toBeTruthy();
    expect(table.source).toContain('自撰');
  }
});

it('综合结论卡片按后端 verdict 渲染档位词与星级排', () => {
  /** verdict 卡片四要素逐字来自后端（VerdictCard spec §6），夹具是重录后的真实响应。 */
  render(<VerdictCard verdict={chart.verdict} />);
  const body = document.body.textContent ?? '';
  expect(body).toContain(chart.verdict.grade);
  expect(body).toContain('★'.repeat(chart.verdict.stars));
  expect(body).toContain('☆'.repeat(5 - chart.verdict.stars));
  for (const point of chart.verdict.points) expect(body).toContain(point);
  expect(body).toContain(chart.verdict.advice);
});

it('页面把 verdict 卡片挂在 ChartSummary 之后', () => {
  const src = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  expect(src).toContain('<VerdictCard verdict={chart.verdict} />');
  pinLiteralOrder(src, [
    '<ChartSummary chart={chart} />',
    '<VerdictCard verdict={chart.verdict} />',
  ]);
});
