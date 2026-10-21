import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { ZiweiChartGrid } from '../../../src/components/ziwei/ZiweiChartGrid';
import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
import { pinLiteralOrder } from '../../lib/sourcePin';
import { readFixture } from '../../lib/readFixture';
import type { ZiweiChart } from '../../../src/types/ziwei';

afterEach(cleanup);

const chart = readFixture('ziwei') as ZiweiChart;

it('the plain block carries all twelve palaces, board order, byte for byte', () => {
  const { container } = render(
    <PlainSectionList sections={chart.palaces.map((p) => ({ title: p.name, text: p.plain }))} />,
  );
  const headings = [...container.querySelectorAll('h3')].map((h) => h.textContent);
  expect(headings).toEqual(chart.palaces.map((p) => p.name));
  const paragraphs = [...container.querySelectorAll('p')].map((p) => p.textContent);
  expect(paragraphs).toEqual(chart.palaces.map((p) => p.plain));
});

it('the whole-chart block carries its three overview sections, byte for byte', () => {
  expect(chart.plain.map((s) => s.title)).toEqual(['全盘气象', '命宫与三方四正', '运限与四化']);
  const { container } = render(<PlainSectionList sections={chart.plain} />);
  const headings = [...container.querySelectorAll('h3')].map((h) => h.textContent);
  expect(headings).toEqual(['全盘气象', '命宫与三方四正', '运限与四化']);
  const paragraphs = [...container.querySelectorAll('p')].map((p) => p.textContent);
  expect(paragraphs).toEqual(chart.plain.map((s) => s.text));
});

it('the board grid renders no plain text at all', () => {
  /** spec §10 的分工：盘面那一格只报星情与格局，白话住在页尾那一段。
   *  这条测的反面是「有人把 `palace.plain` 塞进 `ZiweiChartGrid`」——盘面 12 格各贴一段
   *  长文，页面上那块 4×4 就不再是盘了。门要能在改动发生的当天红，所以钉的是「不出现」，
   *  不是「出现了别的」。
   *
   *  断的是整棵子树的文本而不是 `<p>`：这块盘今天一个 `<p>` 都不产（复测：
   *  `cd frontend && grep -o "<p[ >]" src/components/ziwei/ZiweiChartGrid.tsx | wc -l` → 0），
   *  按标签收文本的话 `texts` 恒为 `[]`，这条就成了一条永远绿的测——而格子里现有的写法
   *  全是 `span`/`div`，正是白话最自然的退化形态。
   *  源码面另有那条 grep 兜着：`grep -n "plain" src/components/ziwei/*.tsx` → 零命中。
   */
  const { container } = render(<ZiweiChartGrid chart={chart} />);
  const boardText = container.textContent ?? '';
  for (const palace of chart.palaces) {
    expect(boardText).not.toContain(palace.plain);
  }
});

it('the page wires the palaces into the block; the provenance block was removed per the 2026-10-21 UI requirement', () => {
  /** 上面两条只证「件怎么排」；页面有没有把 `.plain` 喂进来是另一件事，而标题那个表达式
   *  在这里被重新发明一遍的话，页面写成别的也照样绿——漂移恰好从没人钉的那一侧发生。
   *  整页渲染要走 hook + HTTP，本仓零 mock（AGENTS §9），所以挂载点照
   *  `tests/components/numerology/PlainSummary.test.tsx:44-51` 的形状读页面源码。
   *  路径必须先拼成变量再交给 `new URL`：字面量形式会被 jsdom 环境的客户端资源改写在转译期
   *  换掉，读文件即 ENOENT（`tests/lib/readFixture.ts` 头注的实录陷阱）。
   */
  const specifier = '../../../src/pages/ZiweiPage.tsx';
  const src = readFileSync(fileURLToPath(new URL(specifier, import.meta.url)), 'utf8');
  expect(src).toContain('sections={chart.palaces.map(');
  expect(src).toContain('title: palace.name');
  expect(src).toContain('text: palace.plain');
  expect(src).toContain('title="十二宫白话"');
  expect(src).toContain('title="全盘白话"');
  expect(src).toContain('sections={chart.plain}');
  /** 溯源块（`<Provenance>` / `<ProvenancePanel>`）已按 2026-10-21 UI 需求从页面移除，
   *  这里改钉「不出现」，不再挂表清单。 */
  expect(src).not.toContain('<ProvenancePanel');
  expect(src).not.toContain('<Provenance ');
  /** 次序钉经 `tests/lib/sourcePin.ts` 的 `pinLiteralOrder` 下，它先把每个锚点各自钉一遍
   *  存在性再逐对比次序（裸 `indexOf` 比较在锚点被整行删掉后因 -1 照样绿，终审 I-1 记的就是这个坑）。 */
  pinLiteralOrder(src, [
    '<ChartSummary chart={chart} />',
    'title="全盘白话"',
    'sections={chart.plain}',
    '<ZiweiChartGrid chart={chart} />',
    'sections={chart.palaces.map(',
  ]);
});

it('the fixture provenance payload still lists both tables the endpoint read', () => {
  expect(chart.provenance.tables.map((t) => t.name)).toEqual(['ziwei', 'ziwei_plain']);
});
