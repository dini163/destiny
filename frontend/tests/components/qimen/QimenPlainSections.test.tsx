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

it('the board grid renders no plain paragraph at all', () => {
  /** 与紫微那条同判据：盘面格只报四盘席位，白话住在页尾。钉的是「不出现」。
   *  复测：`cd frontend && grep -n "plain" src/components/qimen/*.tsx` → 零命中。
   */
  const { container } = render(<QimenBoard chart={chart} />);
  const texts = [...container.querySelectorAll('p')].map((p) => p.textContent ?? '');
  for (const palace of chart.palaces) {
    expect(texts).not.toContain(palace.plain);
  }
});

it('the provenance block lists both tables the endpoint read', () => {
  expect(chart.provenance.tables.map((t) => t.name)).toEqual(['qimen', 'qimen_plain']);
});
