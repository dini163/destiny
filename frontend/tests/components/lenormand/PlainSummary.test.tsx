/**
 * 雷诺曼整阵白话的呈现（多系统白话 spec §10 / G25「就地嵌」那一支）。
 *
 * 三种凭据各管各的，读的时候别混：
 * **渲染凭据**管结构——整段全文进 DOM（行数 = 牌位 + 1，等式由测自己钉）、白话块是透镜件的第一个
 * 子元素、标题在正文之前且与正文同块、紧接其下的是极性条、白话排在「组合直读」专业层之前、
 * `synthesis` 不被白话顶掉（G17：那是受控引擎文案，一个字不改）。逐行与牌位的对账在后端
 * golden（T8），前端不重复钉，否则同一件事两份口径。
 * **源码扫凭据**管挂点——整页渲染要走 hook + HTTP，本仓零 mock（AGENTS §9），形状同
 * `tests/components/numerology/PlainSummary.test.tsx`。这里踩过两个坑，都记在测里：① `indexOf`
 * 在字符串缺席时返回 -1，而 -1 小于任何正数——只钉次序不先钉存在性，删掉那行 JSX 照样绿
 * （T9 的 I-1，口径记在 ledger 的 `6379a74` 那条）；② 源码扫只看得到字面、看不到结构——往白话块
 * 前面插一个兄弟、或把标题搬出外层 div，源码里那两串字面还原样在，所以位置与「同块」归渲染管，
 * 源码扫只钉透镜件的字面形状与页面挂点的次序两半。锚点挑看得见的字而不挑 className：Tailwind
 * 类名是纯样式，改一次配色就该绿的钉会假红。
 * **夹具内容凭据**：`tables` 的行序就是页面上的展示契约。
 * **查不到**：段落在页面上的视觉（间距、字有没有被折行）——那要人工走查。
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
    // Step 5 的挂点规则是「在出处块里、在那排 chips 之前」。锚点用**看得见的字**（块的标题与
    // `ENGINE ·` 那条 chip），不用 className：Tailwind 类名是纯样式，改一次配色就该绿的钉会假红，
    // 而「表清单被挪出出处块」这条真漂移反倒没人看（复审 trial i 量的正是这个假红）。
    const title = page.indexOf('抽牌溯源与口径');
    const chips = page.indexOf('ENGINE · ');
    expect(title).toBeGreaterThan(-1);
    expect(chips).toBeGreaterThan(-1);
    const panel = page.indexOf('<ProvenancePanel tables=');
    expect(panel).toBeGreaterThan(title);
    expect(panel).toBeLessThan(chips);
  });

  it('透镜件源码里白话块的字面形状与标题', () => {
    const lens = readFileSync(fileURLToPath(new URL(LENS, import.meta.url)), 'utf8');
    // 属性顺序逐字如此：这一串是「件递白话」的字面凭据，改写它就该红（G25 的「不折」由
    // `PlainProse` 的 `whitespace-pre-line` 兜着，那条另有自己的测）。
    expect(lens).toContain('<PlainProse text={reading.plain_summary} />');
    expect(lens).toContain('整阵白话 · IN PLAIN WORDS');
  });

  it('白话块是渲染出来的第一个子元素，标题在正文之前且与正文同块', () => {
    const { container } = render(<CombinationLens reading={reading} />);
    // 「第一个子元素」「标题与正文同住」只有渲染出来的结构量得到，源码扫量不到：往块前面再插
    // 一个兄弟、把标题挪到正文后面、把标题搬出外层 div，那两串字面在源码里都还原样在
    // （复审的 trial f/g/h 就是靠这三下抓出「钉了一半」）。
    const block = container.firstElementChild?.firstElementChild;
    expect(block?.firstElementChild?.textContent).toBe('整阵白话 · IN PLAIN WORDS');
    expect(block?.textContent).toContain(reading.plain_summary);
  });

  it('白话块紧接其下的是极性条，专业判语留在下面', () => {
    const { container } = render(<CombinationLens reading={reading} />);
    // Step 4 的原话是极性条「一个位置都不动」，它的位置就在白话块正下方；这条钉的是**相邻的两件**，
    // 所以把极性条整块删掉会红。上一版用源码扫（`PlainProse` 的字符早于 `<PolarityBar`）顺带兜着
    // 这件事，换成渲染凭据之后不补这一条就把那道顺带的保护丢了（pass 2 的 P2-1）。
    const block = container.firstElementChild?.firstElementChild;
    expect(block?.nextElementSibling?.textContent).toContain('吉凶极性 · POLARITY');
  });

  it('出处把两张读过的表都递出', () => {
    expect(reading.provenance.tables.map((t) => t.name)).toEqual(['lenormand', 'lenormand_plain']);
  });
});
