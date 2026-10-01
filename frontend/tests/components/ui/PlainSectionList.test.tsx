import { cleanup, render } from '@testing-library/react';
import { afterEach, expect, it } from 'vitest';

import { PlainSectionList } from '../../../src/components/ui/PlainSectionList';
import { paragraphByExact } from '../../lib/prose';

// `vitest.config.ts` 没有开 `globals`，所以 `it`/`expect` 一律显式 import，`cleanup`
// 走 `afterEach`——复测（2026-10-01）：`cd frontend && find tests -name '*.test.ts*' | wc -l`
// → 25 个测文件全部显式 import；其中 16 个用 `afterEach(cleanup)`
// （`grep -rl 'afterEach(cleanup)' tests --include='*.test.ts*' | wc -l`）。
// 写法凭据：`tests/components/numerology/PlainSummary.test.tsx:15`。
afterEach(cleanup);

const SECTIONS = [
  { title: '命宫', text: '第一行。\n第二行。' },
  { title: '兄弟', text: '只有一行。' },
];

it('renders one heading and one paragraph per section, in order', () => {
  const { container } = render(<PlainSectionList sections={SECTIONS} />);
  const headings = [...container.querySelectorAll('h3')];
  expect(headings.map((h) => h.textContent)).toEqual(['命宫', '兄弟']);
  const paragraphs = [...container.querySelectorAll('p')];
  expect(paragraphs.map((p) => p.textContent)).toEqual(['第一行。\n第二行。', '只有一行。']);
});

it('keeps the paragraph verbatim, including the newline', () => {
  render(<PlainSectionList sections={SECTIONS} />);
  // 用 `paragraphByExact` 而不是 `getByText`：后者的缺省 normalizer 会把 `\n` 折成空格，
  // 于是「换行有没有保住」这条判据在它自己手里就失效了（`tests/lib/prose.ts:25-29` 立这件的理由）。
  expect(paragraphByExact(SECTIONS[0].text).className).toContain('whitespace-pre-line');
});

it('renders nothing for an empty list instead of an empty shell', () => {
  const { container } = render(<PlainSectionList sections={[]} />);
  expect(container.querySelectorAll('p')).toHaveLength(0);
  expect(container.querySelectorAll('h3')).toHaveLength(0);
});
