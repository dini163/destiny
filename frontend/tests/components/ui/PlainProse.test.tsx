/**
 * `PlainProse` 只做一件事：把引擎那段多行文本整段搬进 DOM，一行不丢、一字不加。
 *
 * `whitespace-pre-line` 这条 class 断言是本件唯一一条按 class 断的测，因为 jsdom 不渲染
 * white-space——「换行真的断开了」在这个环境里不可观测，能观测的只有那个类在不在。
 * （全站不是只有这一处：`tests/components/meihua/TiYongPanel.test.tsx:39` 也按类断梅花自家件。）
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
    // 空串也能满足下面的相等断言，所以先钉「引擎确实说了话」：一句白话不短于 40 字是语料契约。
    expect(text.length).toBeGreaterThan(40);
    const { container } = render(<PlainProse text={text} />);
    const paragraph = container.querySelector('p');
    if (!paragraph) throw new Error('PlainProse 必须渲染一个 <p>');
    expect(paragraph.textContent).toBe(text);
    for (const line of text.split('\n')) expect(paragraph.textContent).toContain(line);
    expect(paragraph.className).toContain('whitespace-pre-line');
  });
});
