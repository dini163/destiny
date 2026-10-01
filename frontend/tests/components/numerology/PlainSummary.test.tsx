/**
 * 灵数总论的呈现（多系统白话 spec §10）。
 *
 * 页面里那段挂在 `NumerologyResults` 内部（与 `NamePage` 的 `NameSummary` 同形，刻意不升成
 * `components/numerology/` 的第十个文件，见 `NumerologyPage.tsx:40-43`「两个页内局部组件」
 * 那段原注），而整页渲染要走 hook + HTTP，本仓零 mock（AGENTS.md §9），所以这里拆两条：
 * ① 夹具里那段进 `PlainProse` 逐行全等（呈现件不折不加）；
 * ② 挂载点存在性读页面源码（同 `tests/architecture/` 那批读源码的测的做法）。
 * **查不到**：段落在页面上的实际位置与视觉——那需要人工走查，本计划的收尾笔已记录。
 * 复测：cd frontend && npx vitest run tests/components/numerology/PlainSummary.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import { cleanup, render } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { PlainProse } from '../../../src/components/ui/PlainProse';
import type { NumerologyChart } from '../../../src/types/numerology';
import { paragraphByExact } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const chart = readFixture('numerology') as NumerologyChart;

afterEach(cleanup);

describe('灵数白话总论', () => {
  it('夹具那段逐行进 DOM，文本全等且行数与后端一致', () => {
    render(<PlainProse text={chart.plain_summary} />);
    const lines = chart.plain_summary.split('\n');
    expect(lines.length).toBeGreaterThanOrEqual(5);
    const paragraph = paragraphByExact(chart.plain_summary);
    expect(paragraph.textContent).toBe(chart.plain_summary);
    for (const line of lines) expect(paragraph.textContent).toContain(line);
  });

  it('总论里不出现建议句用字（G18 在前端的对应物）', () => {
    for (const token of ['宜', '忌']) expect(chart.plain_summary).not.toContain(token);
  });

  it('页面在事实格之前渲染了它', () => {
    // 路径必须先拼成变量再交给 `new URL`：本文件走 jsdom 环境的客户端资源改写，字面量形式
    // 会在转译期被改成 dev-server 的 `http:` 资源地址，读文件即 ENOENT（`tests/lib/readFixture.ts`
    // 头注的实录陷阱；同形状的写法见 `tests/architecture/compliance_disclaimer.test.tsx:36`）。
    const specifier = '../../../src/pages/NumerologyPage.tsx';
    const path = fileURLToPath(new URL(specifier, import.meta.url));
    const src = readFileSync(path, 'utf8');
    expect(src).toContain('<PlainProse text={chart.plain_summary} />');
    expect(src.indexOf('<PlainProse text={chart.plain_summary} />')).toBeLessThan(
      src.indexOf('<ChartSummary chart={chart} />'),
    );
  });
});
