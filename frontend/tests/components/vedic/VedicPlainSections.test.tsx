/**
 * 吠陀页「白话详解」块与出处三行表（Plan H T10；用户 2026-10-04 裁定第 3 条：盘面不动）。
 * 母本是 `tests/components/transit/TransitPlainSections.test.tsx`。
 *
 * 三种凭据各管各的：**渲染凭据**（第 1-3 条）管四段排成什么；**内容凭据**（第 4-6 条）
 * 管开篇句与两处角色词禁令在用户读到的字上也成立；**源码扫凭据**（第 7-8 条）管挂点、
 * 溯源块已按 2026-10-21 UI 需求从页面移除（三行表的夹具形状仍钉）。
 *
 * **限度**：252 条判语是否说歪了归评审人逐条读；`dasha_none` 那一支的真盘在 D 手
 * （1900-01-01 伦敦），夹具是 A 手，本测吃不到它——那一支由后端 golden 钉（T9）。
 * 复测：cd frontend && npx vitest run tests/components/vedic/VedicPlainSections.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';
import type { VedicChart } from '../../../src/types/vedic';

afterEach(cleanup);

const chart = readFixture('vedic') as VedicChart;

/** 路径先成变量再交给 `new URL`（`tests/lib/readFixture.ts:12-27` 的 jsdom 改写陷阱）。 */
const PAGE = '../../../src/pages/VedicPage.tsx';

const SECTION_TITLES = ['九曜落座', '九曜落宫', '星宿落点', '现行大运与小运'];

/** 开篇句逐字手抄：少一句、改一句只有字面清单能红（不从夹具推给自己看）。 */
const OPENERS = [
  '先说九曜落座这一层：九颗星各自停在哪个星座，决定了它们把你的力气往哪一处使，下面逐颗说的是你可以先认下的底色。',
  '再看九曜落宫这一层：整宫制把十二个星座依次安在十二个宫位上，星落在第几宫，说的就是它在你的生活里偏向哪一块。',
  '最后看星宿这一层：九曜与上升各自落在二十七宿的哪一宿，下面把这些宿的底色逐条说给你听，同一宿只讲一次。',
  '最后看现行的大运与小运：两层主星各自带着一段时期的底色，下面把这两颗主事星各说一句，你可以对着上面的时间轴读。',
];

it('the four sections arrive in roster order and render byte for byte', () => {
  expect(chart.plain.map((section) => section.title)).toEqual(SECTION_TITLES);
  const { container } = render(<PlainSectionList sections={chart.plain} />);
  expect([...container.querySelectorAll('h3')].map((h) => h.textContent)).toEqual(SECTION_TITLES);
  expect([...container.querySelectorAll('p')].map((p) => p.textContent)).toEqual(
    chart.plain.map((section) => section.text),
  );
});

it('pins the fixture line counts', () => {
  expect(chart.plain.map((section) => section.text.split('\n').length)).toEqual([10, 10, 10, 3]);
});

it('the block keeps one paragraph per section, every line break, and no sentence of its own', () => {
  const { container } = render(<PlainSectionList sections={chart.plain} />);
  const paragraphs = [...container.querySelectorAll('p')];
  expect(paragraphs).toHaveLength(chart.plain.length);
  for (const [index, section] of chart.plain.entries()) {
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

it('every section opens with the corpus opener and invents no line', () => {
  for (const [index, section] of chart.plain.entries()) {
    const lines = section.text.split('\n');
    expect(lines[0]).toBe(OPENERS[index]);
    for (const line of lines.slice(1)) {
      expect(line.length).toBeGreaterThan(0);
      expect(line.endsWith('。')).toBe(true);
    }
  }
});

it('the nakshatra body names no graha and no lagna', () => {
  const body = chart.plain[2].text.split('\n').slice(1).join('\n');
  for (const name of ['太阳', '太阴', '火星', '水星', '木星', '金星', '土星', '罗睺', '计都', '上升']) {
    expect(body).not.toContain(name);
  }
});

it('the dasha body carries no role word', () => {
  const body = chart.plain[3].text.split('\n').slice(1).join('\n');
  for (const word of ['大运', '小运', '安塔尔', 'bhukti', '值年', '流年']) {
    expect(body).not.toContain(word);
  }
});

it('the page wires chart.plain after the timeline, and the provenance block is removed per the 2026-10-21 UI requirement', () => {
  const src = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  expect(src).toContain('<PlainSectionList sections={chart.plain} />');
  expect(src).toContain('title="白话详解"');
  // 溯源块已按 2026-10-21 UI 需求移除：页面不得再出现 `<Provenance>` 组件（含共享面板的挂载）。
  expect(src).not.toContain('<Provenance');
  pinLiteralOrder(src, [
    '<DashaTimeline vimshottari={chart.vimshottari} />',
    '<PlainSectionList sections={chart.plain} />',
  ]);
});

it('the fixture carries the three vedic tables, and the page no longer renders the provenance block', () => {
  const tables = chart.provenance.tables;
  expect(tables.map((table) => table.name)).toEqual([
    'vedic',
    'vedic_plain',
    'vedic_plain_gruha',
  ]);
  const versions = new Set(tables.map((table) => table.version));
  expect(versions.size).toBe(1);
  expect(tables[0].version).toBeTruthy();
  expect(tables[1].source).toBe(tables[2].source);
  expect(tables[1].source).toContain('平台自撰');
  expect(tables[0].source).not.toBe(tables[1].source);
  for (const table of tables.slice(1)) {
    expect(table.source).not.toContain('《');
    expect(table.source).not.toContain('依');
  }
  // 溯源块已按 2026-10-21 UI 需求移除：页面不再把三行表递进共享 `ProvenancePanel`。
  const src = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  expect(src).not.toContain('<Provenance');
});
