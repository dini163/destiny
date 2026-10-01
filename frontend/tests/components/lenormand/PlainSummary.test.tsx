/**
 * 雷诺曼整阵白话的呈现（多系统白话 spec §10 / G25「就地嵌」那一支）。
 *
 * 三条呈现判据 + 两条挂点判据：① 大桌夹具那 37 行全文进 DOM（逐行与牌位的对账在后端
 * golden，T8，前端不重复钉，否则同一件事两份口径）；② 白话排在「组合直读」专业层之前；
 * ③ 透镜件只递白话、不顶掉 `synthesis`（G17：`synthesis` 是受控引擎文案，一个字不改）；
 * ④⑤ 挂载点存在性与页面次序读源码——整页渲染要走 hook + HTTP，本仓零 mock（AGENTS §9），
 * 所以页面级次序只能这样钉（同 `tests/components/numerology/PlainSummary.test.tsx:41-52`）。
 * **查不到**：段落在页面上的实际位置与视觉——那要人工走查，Step 7 已记录。
 * 复测：cd frontend && npx vitest run tests/components/lenormand/PlainSummary.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { CombinationLens } from '../../../src/components/lenormand/CombinationLens';
import type { LenormandReading } from '../../../src/types/lenormand';
import { paragraphByExact, precedes } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

// 路径必须先拼成变量再交给 `new URL`：本文件走 jsdom 环境的客户端资源改写，字面量形式会在
// 转译期被改成 dev-server 的 `http:` 资源地址，读文件即 ENOENT（`tests/lib/readFixture.ts:12-27`）。
const PAGE = '../../../src/pages/LenormandPage.tsx';
const LENS = '../../../src/components/lenormand/CombinationLens.tsx';

const reading = readFixture('lenormand') as LenormandReading;

afterEach(cleanup);

describe('雷诺曼整阵白话', () => {
  it('大桌那一段全文进 DOM，行数 = 牌位 + 1', () => {
    const { container } = render(<CombinationLens reading={reading} />);
    const lines = reading.plain_summary.split('\n');
    expect(reading.cards).toHaveLength(36);
    expect(lines).toHaveLength(37);
    expect(container.textContent).toContain(reading.plain_summary);
    for (const line of lines) expect(container.textContent).toContain(line);
  });

  it('白话在组合直读专业层之前', () => {
    const { container } = render(<CombinationLens reading={reading} />);
    const label = [...container.querySelectorAll('span')].find(
      (s) => s.textContent === '组合直读 · COMBINATIONS',
    );
    if (!label) throw new Error('组合直读那一层的标题不见了——专业层被搬走或改名了');
    expect(precedes(paragraphByExact(reading.plain_summary), label)).toBe(true);
  });

  it('透镜件递白话，不拿它顶掉 synthesis', () => {
    const { container } = render(<CombinationLens reading={reading} />);
    const texts = [...container.querySelectorAll('p')].map((p) => p.textContent);
    expect(reading.plain_summary).not.toBe(reading.synthesis);
    expect(texts).toContain(reading.plain_summary);
    expect(texts).not.toContain(reading.synthesis);
  });

  it('页面仍把 synthesis 留在它自己的卡里，白话住在透镜件', () => {
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    const lens = readFileSync(fileURLToPath(new URL(LENS, import.meta.url)), 'utf8');
    expect(page).toContain('{reading.synthesis}');
    expect(page).not.toContain('plain_summary');
    expect(lens).toContain('<PlainProse text={reading.plain_summary} />');
    expect(page.indexOf('<CombinationLens reading={reading} />')).toBeLessThan(
      page.indexOf('{reading.synthesis}'),
    );
  });

  it('出处把两张读过的表都递出', () => {
    expect(reading.provenance.tables.map((t) => t.name)).toEqual(['lenormand', 'lenormand_plain']);
  });
});
