/**
 * 合规免责声明的**逐字性**与**常驻性**（全栈测试 Task 13 Step 3；PRD §4.3）。
 *
 * 为什么值得钉：全站只有 `SiteFooter.tsx` 一处印这段文案，而它只挂在 `AppShell` 这一条
 * 布局路由下面。于是「每个页面都带免责声明」被拆成两条各自会红的腿：
 * ①渲染腿——`AppShell` 真的渲染 `SiteFooter`（用假页面占位也照印，证明它不依赖具体页）；
 * ②数据腿——全部路由都嵌在这**一条**布局路由里，而不是它的兄弟。将来有人加一条
 * 顶层路由（独立报表页、弹层页）漏在 shell 外面，第②条即红；走查看不到这种页，
 * 因为它还不存在。
 * 逐字性的基准取自 PRD 文件本身而不是测试里再抄一遍：改一个字要么连 PRD 一起改（合法），
 * 要么这条红（悄悄漂移）。为什么不钉 `SiteFooter` 里那三张印鉴的文案：那是设计稿参照物，
 * 不是契约（合婚 spec §12 教训），PRD 只约束这一句合规文案。
 *
 * 复测口径（2026-09-27 全绿，3 项）：
 *   cd frontend && npx vitest run tests/architecture/compliance_disclaimer.test.tsx
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { AppShell } from '../../src/components/layout/AppShell';
import { router } from '../../src/router';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

/** PRD §4.3 正文那一行（blockquote 内），逐字基准的权威来源。 */
function prdDisclaimer(): string {
  //  specifier 先成变量再交给 new URL：本文件走 jsdom，字面量会被 Vite 的
  //  import-analysis 改写成 http: 资源 URL（陷阱实录见 tests/lib/readFixture.ts:12-23）。
  const specifier = '../../../prd/destiny_prd_v2.0_detailed.md';
  const line = readFileSync(fileURLToPath(new URL(specifier, import.meta.url)), 'utf8')
    .split('\n')
    .find((l) => l.startsWith('> 本平台所有命理排盘'));
  if (!line) throw new Error('PRD §4.3 的免责声明行找不到：基准本身变了，先读 PRD 再改测');
  return line.slice('> '.length).trimEnd();
}

/** jsdom 未实现 `window.scrollTo`；AppShell 的滚动复位不是本测判据。 */
function stubScroll(): void {
  vi.stubGlobal('scrollTo', () => {});
}

/**
 * 本测只读路由表的三样：`path` / `element` / `children`。
 * 为什么要在测试里声明这个形状而不是直接用 `router.routes` 的类型：react-router 把
 * `AgnosticDataRouteObject` 定义成「index 分支」与「普通分支」的联合，而 **index 分支上没有
 * `element` 这个属性** —— 于是 `child.element` 在联合类型上就是 TS2339，而「每条子路由都带 element」
 * 恰恰是第③条断言的本体。在此收窄成本地形状，比在每个断言点写一遍 `'element' in child` 少一层噪声，
 * 且形状与本测的读法一一对应（多出来的属性本测不读，也不因它红）。
 */
interface RouteShape {
  path?: string;
  element?: unknown;
  children?: readonly RouteShape[];
}

describe('合规免责声明（PRD §4.3）', () => {
  it('全站唯一渲染点 SiteFooter 印的就是 PRD 那一行，一字不差', () => {
    stubScroll();
    render(
      <MemoryRouter initialEntries={['/bazi-natal']}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="*" element={<div>占位页面</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText('占位页面')).toBeInTheDocument();
    expect(screen.getByText(prdDisclaimer())).toBeInTheDocument();
  });

  it('路由表只有一个顶层路由，且它的 element 就是 AppShell', () => {
    expect(router.routes).toHaveLength(1);
    const layout = (router.routes as readonly RouteShape[])[0];
    expect(layout.path).toBe('/');
    const element = layout.element as { type?: { name?: string } };
    expect(element.type?.name).toBe('AppShell');
  });

  it('每个页面路由（含 404 兜底）都是 AppShell 的后代，没有一条漏在 shell 外', () => {
    const layout = (router.routes as readonly RouteShape[])[0];
    const children = layout.children ?? [];
    expect(children.length).toBeGreaterThan(0);
    // 每条子路由都得有可渲染的 element（index 路由的 Navigate 也是 element）。
    const bare = children.filter((child) => child.element === undefined);
    expect(bare.map((child) => child.path ?? '(index)')).toEqual([]);
    // 兜底 404 必须在 children 里：它是 shell 的孩子，未知路径才带得到免责声明。
    expect(children.some((child) => child.path === '*')).toBe(true);
  });
});
