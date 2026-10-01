import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { QimenBoard } from '../../../src/components/qimen/QimenBoard';
import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
import { readFixture } from '../../lib/readFixture';
import type { QimenChart } from '../../../src/types/qimen';

afterEach(cleanup);

const chart = readFixture('qimen') as QimenChart;

it('the plain block carries all nine palaces in luoshu order, byte for byte', () => {
  const { container } = render(
    <PlainSectionList
      sections={chart.palaces.map((p) => ({ title: `${p.gua}${p.number}宫 · ${p.direction}`, text: p.plain }))}
    />,
  );
  const headings = [...container.querySelectorAll('h3')].map((h) => h.textContent);
  expect(headings).toEqual(chart.palaces.map((p) => `${p.gua}${p.number}宫 · ${p.direction}`));
  const paragraphs = [...container.querySelectorAll('p')].map((p) => p.textContent);
  expect(paragraphs).toEqual(chart.palaces.map((p) => p.plain));
});

it('the center palace keeps its single line and no seats', () => {
  /** 中五宫那一段只有一句开篇句（T6 的 `items=[]` 支路）。前端不许给它补一句
   *  「此宫无星」——补出来的字不在受控语料里（spec §5）。 */
  const center = chart.palaces.find((p) => p.number === 5);
  expect(center?.plain.split('\n')).toHaveLength(1);
  expect(center?.stars).toHaveLength(0);
  expect(center?.door).toBeNull();
  expect(center?.god).toBeNull();
});

it('the board grid renders no plain text at all', () => {
  /** 与紫微那条同判据：盘面格只报四盘席位，白话住在页尾。钉的是「不出现」。
   *  断整棵子树的文本而不是 `<p>`：这块盘今天一个 `<p>` 都不产（复测：
   *  `cd frontend && grep -o "<p[ >]" src/components/qimen/QimenBoard.tsx | wc -l` → 0），
   *  按标签收文本这条门就永远绿不了也永远红不了。
   *  源码面另有那条 grep 兜着：`grep -n "plain" src/components/qimen/*.tsx` → 零命中。
   */
  const { container } = render(<QimenBoard chart={chart} />);
  const boardText = container.textContent ?? '';
  for (const palace of chart.palaces) {
    expect(boardText).not.toContain(palace.plain);
  }
});

it('the page wires the nine palaces into the block and the tables into the panel', () => {
  /** 标题那串「卦名 + 宫数 + 方位」是本任务唯一一处**在页面里拼**的字面量：brief 给的理由是
   *  只给卦名会和盘面格内的写法漂。上面那条 byte-for-byte 测把同一个模板重新发明了一遍，
   *  所以页面少写 `宫` 或换成 `${p.gua}${p.number}` 也照样绿——这条去钉真页面。
   *  读源码的形状与路径拼法的理由同 `tests/components/numerology/PlainSummary.test.tsx:44-51`。
   */
  const specifier = '../../../src/pages/QimenPage.tsx';
  const src = readFileSync(fileURLToPath(new URL(specifier, import.meta.url)), 'utf8');
  expect(src).toContain('title: `${palace.gua}${palace.number}宫 · ${palace.direction}`,');
  expect(src).toContain('text: palace.plain,');
  expect(src).toContain('<ProvenancePanel tables={chart.provenance.tables} />');
  expect(src.indexOf('<QimenBoard chart={chart} />')).toBeLessThan(src.indexOf('<PlainSectionList'));
});

it('the provenance block lists both tables the endpoint read', () => {
  expect(chart.provenance.tables.map((t) => t.name)).toEqual(['qimen', 'qimen_plain']);
});
