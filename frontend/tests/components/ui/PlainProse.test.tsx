/**
 * `PlainProse` 只做一件事：把引擎那段多行文本整段搬进 DOM，一行不丢、一字不加。
 *
 * `whitespace-pre-line` 这条 class 断言是全站唯一一处按 class 断的测，因为 jsdom 不渲染
 * white-space——「换行真的断开了」在这个环境里不可观测，能观测的只有那个类在不在。
 * 复测：cd frontend && npx vitest run tests/components/ui/PlainProse.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { PlainProse } from '../../../src/components/ui/PlainProse';
import type { NameAnalysis } from '../../../src/types/name';
import { readFixture } from '../../lib/readFixture';

const name = readFixture('name') as NameAnalysis;

afterEach(cleanup);

describe('PlainProse 呈现件', () => {
  it('整段白话逐行进 DOM，文本全等于引擎输出', () => {
    const text = name.grids[1].plain;
    const { container } = render(<PlainProse text={text} />);
    const paragraph = container.querySelector('p');
    if (!paragraph) throw new Error('PlainProse 必须渲染一个 <p>');
    expect(paragraph.textContent).toBe(text);
    for (const line of text.split('\n')) expect(paragraph.textContent).toContain(line);
    expect(paragraph.className).toContain('whitespace-pre-line');
  });
});
