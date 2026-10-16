/**
 * 行运页「白话详解」块与出处三行表（Plan G spec §9；用户 2026-10-04 裁定第 3 条：图/网格/
 * 表格一律不动）。母本是 `tests/components/western/WesternPlainSections.test.tsx`。
 *
 * 三种凭据各管各的，读的时候别混：
 * **渲染凭据**（第 1、2 条）管 `PlainSectionList` 拿到真实五段后排成什么：五段齐、序对、
 *   逐字节，且这一件不加一个字、不把多行拆成多段。
 * **源码扫凭据**（第 3、4 条）管挂点与反串位：页面真把 `chart.plain` 递进来了吗、卡在专业网格
 *   与出处块之间吗、有没有把 `chart.natal.plain`（本命那 8 段）错接到行运页上。
 * **夹具内容凭据**（第 5、6 条）管响应：层名只住在开篇句（G37 的前端镜像）、`tables` 三行的
 *   名字/版本/出处串形状（spec §9「不只钉名字」）。
 *
 * **限度**（写在测里而不是留给读者猜）：夹具是 `scripts/record_frontend_fixtures.py` 打的
 * J2000 格林尼治那一手（与后端 golden 的 `_chart()` 同盘）。**零相位那一支本测吃不到**——
 * 今天没有一份真盘是零相位，它由后端 golden 的构造分支钉（T24 第 4 条），不在前端重复。
 * **查不到**：648 条判语是否说歪了（语义忠实要评审人逐段读）、这段长文在真机上的读感（走查，
 * 归 T27 Step 4）。
 * 复测：cd frontend && npx vitest run tests/components/transit/TransitPlainSections.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';
import type { TransitChart } from '../../../src/types/transit';

afterEach(cleanup);

const chart = readFixture('transit') as TransitChart;

/** 挂点测走 jsdom 的客户端资源改写，`new URL` 的参数必须先成变量（`tests/lib/readFixture.ts:12-27` 的实录陷阱）。 */
const PAGE = '../../../src/pages/TransitPage.tsx';

/** 五段的展示序 = `build_plain` 里五个 `emit(…)` 的序，也是 `TRANSIT_SECTION_TITLES` 的序。
 *  在这里逐字钉而不是从夹具推给自己看：少一段（有人改了 `emit` 却没删标题）只有字面清单能红。 */
const SECTION_TITLES = [
  '行运对本命相位',
  '次限对本命相位',
  '太阳弧对本命相位',
  '次限月亮',
  '次限上升与天顶',
];

it('the five sections arrive in roster order and render byte for byte', () => {
  expect(chart.plain.map((section) => section.title)).toEqual(SECTION_TITLES);
  const { container } = render(<PlainSectionList sections={chart.plain} />);
  expect([...container.querySelectorAll('h3')].map((h) => h.textContent)).toEqual(SECTION_TITLES);
  expect([...container.querySelectorAll('p')].map((p) => p.textContent)).toEqual(
    chart.plain.map((section) => section.text),
  );
});

it('the wheel, tables and cards stay free of plain prose', () => {
  /** 用户裁定 3：图/网格/表格一律不动——白话只许住在页尾那一张卡里。判据是**组件源码**：
   *  盘面五件（双轮盘、移动层位置表、相位表、次限卡、太阳弧卡）既不 import
   *  `PlainSectionList`，也不出现「白话」字面。这五件今天就没有白话（绿），但把它钉成契约：
   *  日后有人往盘面件里塞白话小字，这一条会红。
   *  路径先拼成变量再交给 `new URL`（`tests/lib/readFixture.ts:12-27` 的实录陷阱：jsdom 环境
   *  下 `new URL(字面量, import.meta.url)` 会被 Vite 改写成静态资源引用）。
   *  `ProgressionCard`/`SolarArcCard` 没有独立文件，定义在 `TransitPage.tsx` 内（`:249-300`），
   *  所以从页面源码里截出各自函数体来扫——整页唯一允许出现 `PlainSectionList` 的地方是页尾
   *  那张卡（归第 3 条），本条的落点只在这两件自己身上。
   */
  for (const component of ['TransitBiWheel', 'MovingPointTable', 'CrossAspectList']) {
    const specifier = `../../../src/components/transit/${component}.tsx`;
    const src = readFileSync(fileURLToPath(new URL(specifier, import.meta.url)), 'utf8');
    expect(src).not.toContain('PlainSectionList');
    expect(src).not.toContain('白话');
  }
  const pageSrc = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  for (const fn of ['ProgressionCard', 'SolarArcCard']) {
    const match = pageSrc.match(new RegExp(`function ${fn}\\(([^]*?)(?=\\nfunction |$)`));
    expect(match, fn).toBeTruthy();
    expect(match![1]).not.toContain('PlainSectionList');
    expect(match![1]).not.toContain('白话');
  }
});

it('the block keeps every line break and adds no sentence of its own', () => {
  /** 第 1 条已经逐字比过文本；本条管的是**形状**：一段一个 `<p>`（前端不许把开篇句与逐条
   *  判语拆成多个 `<p>`，也不许把五段并成一个），且每个 `<p>` 带 `whitespace-pre-line`
   *  ——与本命页那件同一条纪律，这里补的是**真实五段**那一手。 */
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

it('the page wires chart.plain under 白话详解 ahead of the provenance block', () => {
  const src = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  expect(src).toContain('<PlainSectionList sections={chart.plain} />');
  expect(src).toContain('title="白话详解"');
  pinLiteralOrder(src, [
    '<CrossAspectList aspects={aspects} />',
    '<PlainSectionList sections={chart.plain} />',
    '<Provenance chart={chart} />',
  ]);
});

it('the page never reaches into natal.plain, and the two plain families stay disjoint', () => {
  /** 反串位扫（偏差 9）：`TransitChart` 嵌着 `natal: WesternChart`，而 `WesternChart` 自带 F 的
   *  8 段 `plain`——挂点若写错成 `chart.natal.plain`，行运页会印出本命那 8 段。第一半是源码扫
   *  本身（读 `TransitPage.tsx`，不许出现 `natal.plain`）；第二半是形状测（夹具里行运 5 段的
   *  标题集合与本命 8 段的标题集合交集为空——5 段 vs 8 段字面不同，错接会立刻露出本命标题）。
   */
  const src = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  expect(src).not.toContain('natal.plain');
  const natalTitles = new Set(chart.natal.plain.map((section) => section.title));
  const transitTitles = new Set(chart.plain.map((section) => section.title));
  expect([...transitTitles].filter((t) => natalTitles.has(t))).toEqual([]);
});

it('the layer words appear only inside the opening sentence of each section', () => {
  /** G37 的前端镜像：后端门判的是「648 条判语里没有层名词」，本条判的是**渲染结果**——
   *  把每个 `<p>` 剥掉第一句（开篇句）之后的正文里也不许出现 `行运`/`次限`/`太阳弧`/`推运`。
   *  后端门抓的是表，前端这条抓的是用户实际读到的字——两处同一条纪律，缺一处都有人能改漏。 */
  const { container } = render(<PlainSectionList sections={chart.plain} />);
  const paragraphs = [...container.querySelectorAll('p')];
  const LAYER_WORDS = ['行运', '次限', '太阳弧', '推运'];
  for (const paragraph of paragraphs) {
    const lines = paragraph.textContent?.split('\n') ?? [];
    const body = lines.slice(1).join('\n');
    for (const word of LAYER_WORDS) {
      expect(body).not.toContain(word);
    }
  }
});

it('the provenance panel is handed the three overlay tables with their distinct source shapes', () => {
  /** spec §9 的「不只钉名字」：三行 `name` 字面序、`version` 非空且彼此相同（不写死 `2026.09`：
   *  滚动版本改的时候这里不该红）、前两行 `source` 逐字节相同且以 `平台自撰` 开头、第三行以
   *  `平台整理` 开头且与前两行不同——「两张自撰表共用一串、属性表另有其串」在用户可见层的形状。
   *  串的**全文**不在这里手抄：字面对账归后端 T25 的钉，前端这一侧抄一份全文就是 F 偏差里
   *  「两处手抄互漂」的那个债。 */
  const tables = chart.provenance.tables;
  expect(tables.map((table) => table.name)).toEqual([
    'transit_plain',
    'transit_plain_aspect',
    'aspects_nature',
  ]);
  const versions = new Set(tables.map((table) => table.version));
  expect(versions.size).toBe(1);
  expect(tables[0].version).toBeTruthy();
  expect(tables[0].source).toBe(tables[1].source);
  expect(tables[0].source).toContain('平台自撰');
  expect(tables[2].source).toContain('平台整理');
  expect(tables[2].source).not.toBe(tables[0].source);
  for (const table of tables) {
    expect(table.source).not.toContain('《');
    expect(table.source).not.toContain('依');
  }
});

it('the page renders those three tables through the shared provenance panel', () => {
  /** 走查三（T27 Step 4）的实录：页面原本只印 `note` 与 ENGINE 行，三行表永远到不了用户眼前——
   *  数据层（上一组）、类型层（T26）都齐了，独缺渲染。用与本命页同一条「数据进来、面板出去」的
   *  形态钉住：`TransitPage.tsx` 必须把 `chart.provenance.tables` 递进共享的 `ProvenancePanel`。
   *  复测：把下面这行换成 `tables={chart.provenance.tables.slice(0, 2)}` 或删掉它，本测即红。 */
  const src = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
  expect(src).toContain('<ProvenancePanel tables={chart.provenance.tables} />');
});
