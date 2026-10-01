/**
 * 雷诺曼整阵白话的呈现（多系统白话 spec §10 / G25「就地嵌」那一支）。
 *
 * 三种凭据，别把它们当同一种读：
 * 「全文进 DOM / 在专业层之前 / 不顶掉 synthesis」是**渲染凭据**——只 render 透镜件。
 * 逐行与牌位的对账在后端 golden（T8），前端不重复钉，否则同一件事两份口径。
 * G17：`synthesis` 是受控引擎文案，一个字不改，所以这里钉的是「白话没有顶掉它」。
 * 「页面挂在哪、件内排在哪」是**源码扫凭据**——整页渲染要走 hook + HTTP，本仓零 mock
 * （AGENTS §9），形状同 `tests/components/numerology/PlainSummary.test.tsx`。钉的时候
 * **每一项都钉**：两处 JSX 挂载各一条、白话块标题一条、页面次序与件内次序的两半各一条。
 * 陷阱：`indexOf` 在字符串缺席时返回 -1，而 -1 小于任何正数——只钉次序、不钉存在性，删掉那行
 * JSX 照样绿（T9 的 I-1 就是这么漏的，口径记在 ledger 的 `6379a74` 那条）。
 * 「两张表」那条是**夹具内容凭据**：`tables` 的行序就是页面上的展示契约。
 * **查不到**：段落在页面上的实际位置与视觉——那要人工走查。
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

  it('页面把白话挂在透镜件里、把表清单挂在出处块，两处次序都在', () => {
    const page = readFileSync(fileURLToPath(new URL(PAGE, import.meta.url)), 'utf8');
    // 存在性先钉（`indexOf` 的 -1 会把下面的次序钉变成空跑）。
    expect(page).toContain('<CombinationLens reading={reading} />');
    expect(page).toContain('{reading.synthesis}');
    expect(page).toContain('<ProvenancePanel tables={reading.provenance.tables} />');
    // 页面不自己组白话：它只把整份 reading 交给透镜件。
    expect(page).not.toContain('plain_summary');
    expect(page.indexOf('<CombinationLens reading={reading} />')).toBeLessThan(
      page.indexOf('{reading.synthesis}'),
    );
    // Step 5 的挂点规则是「在 chips 行之前」，锚点自己的存在也得钉，否则锚点改名就变成空跑。
    const chips = page.indexOf('flex flex-wrap items-center gap-x-4');
    expect(chips).toBeGreaterThan(-1);
    expect(page.indexOf('<ProvenancePanel tables=')).toBeLessThan(chips);
  });

  it('白话块是透镜件的第一个子元素，标题与正文同住', () => {
    const lens = readFileSync(fileURLToPath(new URL(LENS, import.meta.url)), 'utf8');
    // 属性顺序逐字如此：这一串是「件递白话」的唯一凭据，改写它就该红。
    expect(lens).toContain('<PlainProse text={reading.plain_summary} />');
    expect(lens).toContain('整阵白话 · IN PLAIN WORDS');
    // `<PolarityBar` 带左尖括号：件内那行 `function PolarityBar` 定义不匹配，命中的只有 JSX 挂载点。
    // 极性条若被整块删掉，indexOf 变 -1，这条同样会红——那正是「白话必须在极性条之前」的字面意思，
    // 不是意外。
    expect(lens.indexOf('<PlainProse text={reading.plain_summary} />')).toBeLessThan(
      lens.indexOf('<PolarityBar'),
    );
  });

  it('出处把两张读过的表都递出', () => {
    expect(reading.provenance.tables.map((t) => t.name)).toEqual(['lenormand', 'lenormand_plain']);
  });
});
