import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { LiushiHourLadder } from '../../../src/components/bazi/liushi/LiushiHourLadder';
import { TransitYearCard } from '../../../src/components/bazi/transit/TransitYearCard';
import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
import { readFixture } from '../../lib/readFixture';
import { pinLiteralOrder } from '../../lib/sourcePin';
import type { BaziTransitResult } from '../../../src/types/baziTransit';
import type { BaziLiushiResult } from '../../../src/types/baziLiushi';
import type { PlainSection } from '../../../src/types/common';

afterEach(cleanup);

const sourceOf = (relative: string) => {
  // 三层深（tests/components/ui/ → frontend/）；先交变量再进 new URL，理由见本步正文。
  const specifier = `../../../${relative}`;
  return readFileSync(fileURLToPath(new URL(specifier, import.meta.url)), 'utf8');
};

const PAGES: ReadonlyArray<{ title: string; source: string; anchors: string[] }> = [
  { title: '合盘白话', source: 'src/pages/BaziHehunPage.tsx',
    anchors: ['title="契合度总分"', 'title="合盘白话"', 'sections={annotatePlainSections(result.plain)}', 'title="男女档案对位"'] },
  { title: '岁运白话', source: 'src/pages/BaziTransitPage.tsx',
    anchors: ['<TransitNatalBar natal={transit.data} />', 'title="岁运白话"', 'sections={transit.data.plain}', 'title="流年区间账本"'] },
  { title: '流月白话', source: 'src/pages/BaziLiuriPage.tsx',
    anchors: ['<LiuriSegmentHeader', 'title="流月白话"', 'sections={result.plain}', '{{gz}}月逐日矩阵'] },
  { title: '流时白话', source: 'src/pages/BaziLiushiPage.tsx',
    anchors: ['<TransitNatalBar natal={result} />', 'title="流时白话"', 'sections={result.plain}', 'title="一日真气"'] },
  { title: '全树白话', source: 'src/pages/KabbalahPage.tsx',
    anchors: ['<PathIndex', 'title="全树白话"', 'sections={tree.data.plain}', 'title="原质 / 路径详解"'] },
];

it.each(PAGES)('$title 卡按声明次序挂在技术盘之前', (page) => {
  pinLiteralOrder(sourceOf(page.source), page.anchors);
});

it('流年卡与时辰 ladder 的源码里不出现 plain', () => {
  // 反向判据的源码侧那一半：整体白话只住页面层，明细组件不许顺手接走。
  // 渲染侧的另一半（页面上真的看不到整段句子）要夹具里的 plain，进 J-T8 Step 1。
  for (const component of [
    'src/components/bazi/transit/TransitYearCard.tsx',
    'src/components/bazi/liushi/LiushiHourLadder.tsx',
  ]) {
    expect(sourceOf(component)).not.toContain('plain');
  }
});

it('两张卡各渲染一次不抛（props 逐字照组件签名）', () => {
  // 这一条只证明挂件的 props 形状读对了：TransitYearCard 只要 year（hrefFor 可省），
  // LiushiHourLadder 四件全必填（hours / peakIndex / focusZhi / onSelect，实测无一件可省）。
  // 它不涉白话，夹具不动也绿，所以留在本步当 props 的钉子。
  const transit = readFixture('bazi-liuyue') as BaziTransitResult;
  const { container: yearCard } = render(<TransitYearCard year={transit.years[0]} />);
  expect(yearCard.textContent ?? '').toContain(transit.years[0].pillar.ganzhi);
  const liushi = readFixture('bazi-liushi-day') as BaziLiushiResult;
  const { container: ladder } = render(
    <LiushiHourLadder hours={liushi.hours} peakIndex={0} focusZhi={null} onSelect={() => {}} />,
  );
  expect(ladder.textContent ?? '').toContain(liushi.hours[0].zhi);
});

const PLAIN_FIXTURES: ReadonlyArray<{ slug: string; title: string }> = [
  { slug: 'bazi-hehun', title: '合盘白话' },
  { slug: 'bazi-liuyue', title: '岁运白话' },
  { slug: 'bazi-liuri-matrix', title: '流月白话' },
  { slug: 'bazi-liushi-day', title: '流时白话' },
  { slug: 'kabbalah-tree', title: '全树白话' },
];

it.each(PLAIN_FIXTURES)('$title 的 plain 逐节 byte-for-byte 进块', ({ slug }) => {
  // `PlainSectionList` 一节一个 article：h3 是节名，`PlainProse` 把整段文本塞进**一个** `p`
  // （`whitespace-pre-line` 负责按 `\n` 断行，不拆元素）。所以两侧都是逐节一一对应，
  // 不是逐行——照逐行写会红，且红得像是组件的错。
  const payload = readFixture(slug) as { plain: PlainSection[] };
  const { container } = render(<PlainSectionList sections={payload.plain} />);
  expect([...container.querySelectorAll('h3')].map((node) => node.textContent)).toEqual(
    payload.plain.map((section) => section.title),
  );
  expect([...container.querySelectorAll('p')].map((node) => node.textContent)).toEqual(
    payload.plain.map((section) => section.text),
  );
});

it('流年卡与时辰 ladder 不渲染任何白话段', () => {
  // 反向判据的渲染侧那一半（批次一在 ziwei / qimen 各钉过的那条形）：整段句子只住页面层。
  const transit = readFixture('bazi-liuyue') as BaziTransitResult;
  const { container: yearCard } = render(<TransitYearCard year={transit.years[0]} />);
  for (const section of transit.plain) {
    expect(yearCard.textContent ?? '').not.toContain(section.text);
  }
  const liushi = readFixture('bazi-liushi-day') as BaziLiushiResult;
  const { container: ladder } = render(
    <LiushiHourLadder hours={liushi.hours} peakIndex={0} focusZhi={null} onSelect={() => {}} />,
  );
  for (const section of liushi.plain) {
    expect(ladder.textContent ?? '').not.toContain(section.text);
  }
});
