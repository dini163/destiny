import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { ZiweiChartGrid } from '../../../src/components/ziwei/ZiweiChartGrid';
import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
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

it('the board grid renders no plain paragraph at all', () => {
  /** spec §10 的分工：盘面那一格只报星情与格局，白话住在页尾那一段。
   *  这条测的反面是「有人把 `palace.plain` 塞进 `ZiweiChartGrid`」——盘面 12 格各贴一段
   *  长文，页面上那块 4×4 就不再是盘了。门要能在改动发生的当天红，所以钉的是「不出现」，
   *  不是「出现了别的」。复测：`cd frontend && grep -n "plain" src/components/ziwei/*.tsx` → 零命中。
   */
  const { container } = render(<ZiweiChartGrid chart={chart} />);
  const texts = [...container.querySelectorAll('p')].map((p) => p.textContent ?? '');
  for (const palace of chart.palaces) {
    expect(texts).not.toContain(palace.plain);
  }
});

it('the provenance block lists both tables the endpoint read', () => {
  expect(chart.provenance.tables.map((t) => t.name)).toEqual(['ziwei', 'ziwei_plain']);
});
