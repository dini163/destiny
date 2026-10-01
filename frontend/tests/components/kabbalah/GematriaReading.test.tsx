/**
 * `overview()` 装配出的卡巴拉总论到底有没有印到页面上（Plan B 终审随附债之二）。
 *
 * 渲染点在 `GematriaConsole.tsx:143`，但那一行住在 `GematriaResult` 里而不是同文件的
 * `GematriaConsole`（后者是输入表单，props 里没有 `reading`）——计划稿把两个组件名弄混了，
 * 以文件实际导出为准。`<p>{reading.synthesis}</p>` 是 `engines/kabbalah.py` 的 `overview()`
 * 那次逐字节收编（Plan B G13）唯一的产品出口，收编前它只被后端 golden 钉着。
 * 全文相等而不是子串：`tests/lib/prose.ts` 的理由在这里同样成立；
 * `paragraphByExactIn` 找不到时抛错而不是返回 null，所以断言写成「不抛错即存在」。
 * 复测：cd frontend && npx vitest run tests/components/kabbalah/GematriaReading.test.tsx
 */
import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { GematriaResult } from '../../../src/components/kabbalah/GematriaConsole';
import type { GematriaReading } from '../../../src/types/kabbalah';
import { paragraphByExactIn } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const reading = readFixture('kabbalah-gematria') as GematriaReading;

afterEach(cleanup);

describe('GematriaResult 的总论段', () => {
  it('把引擎装配好的 synthesis 整段原样印出，一字不改', () => {
    const { container } = render(<GematriaResult reading={reading} onSelect={() => {}} />);
    expect(reading.synthesis.length).toBeGreaterThan(80);
    expect(container.textContent).toContain(reading.synthesis);
    expect(() => paragraphByExactIn(container, reading.synthesis)).not.toThrow();
  });
});
