/**
 * `SynastryConsole`（西洋合盘输入台：一台两列）的可访问性**现状钉**——只钉，不修。
 *
 * 来路：`docs/superpowers/plans/2026-09-26-fullstack-test-walkthrough.md` 的
 * 「走查外缺口 · 合盘双人表单的 accessible name 不唯一」，原话是「属可访问性债，转 8B
 * 组件测与后续 a11y 计划」。本文件就是那次转交落地的地方。
 *
 * 现状：`SideColumn` 给称谓与时区偏移两个字段按 `${caption}` 加了前缀
 * （`SynastryConsole.tsx:61`、`:97`），日期时间也带了 `ariaLabel={caption}`（`:71`、`:76`），
 * 所以它们是 `甲方年`、`乙方分` 这种独一名；但 `LocationField` 的 props 里没有 `ariaLabel`
 * 入参，三个 `aria-label` 是写死的裸串——「出生城市搜索」（`LocationField.tsx:96`）、
 * 「纬度」（`:154`）、「经度」（`:169`）。于是同一张 `<form>` 里并排的两列各产出两份同名
 * 控件，读屏用户听到的都是「纬度」，靠 DOM 归属（哪个 `<fieldset>`）才分得清甲乙。
 * 本测把「重复 2 份 / 前缀 1 份」和「归属确实分得开」同时钉住：前者是债的形状，后者是
 * 这条债还没到「不可用」的证据。**不要**为了让测绿去给 `LocationField` 加 `ariaLabel`——
 * 那是 a11y 修复，属于后续计划，本轮 `frontend/src/**` 冻结（AGENTS §9）。
 *
 * `QueryClientProvider` 不是 mock：`LocationField` 用 `useCities`，其 `enabled` 是
 * `term.length > 0`，初始空串不发任何请求；包一层只是给那个 hook 提供它必需的 react-query
 * 上下文（`retry: false` 是防止将来真有查询时测试挂着重试）。响应数据一份都没喂：这是
 * 输入台，它渲染时不该需要响应。
 *
 * 简报原文有一处与树不符（已按实际形状实现，见报告「需要控制器裁定」）：简报写
 * `SynastryConsole({state, onChange, caption})`、「一造一块，页面渲染两次」，实测签名是
 * `SynastryConsole({pending, onSubmit})`（`:118`），甲乙两列是它内部私有 `SideColumn`
 * 渲染的，`SynastryPage.tsx:50` 只挂载**一次**。所以「渲染两份 console」既做不到也不是
 * 这页的真实形状；等价且更硬的断言是：挂载一份 console，量到 `纬度` 两份、前缀名各一份。
 *
 * 复测口径（2026-09-27 全绿，3 项）：
 *   cd frontend && npx vitest run tests/components/synastry/SynastryConsole.test.tsx
 */
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SynastryConsole } from '../../../src/components/synastry/SynastryConsole';
import type { SynastryRequest } from '../../../src/types/synastry';

// vitest 未开 globals，RTL 的自动 cleanup 注册不上（它探测的是全局 afterEach），故显式装。
afterEach(cleanup);

/** 挂载一份真实的两列输入台；`onSubmit` 只做收集，页面级请求不在此发生。 */
function mountConsole(): { container: HTMLElement; submitted: SynastryRequest[] } {
  const submitted: SynastryRequest[] = [];
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const { container } = render(
    <QueryClientProvider client={client}>
      <SynastryConsole pending={false} onSubmit={(request) => submitted.push(request)} />
    </QueryClientProvider>,
  );
  return { container, submitted };
}

/** 控件归属哪一造：看它所在 `<fieldset>` 的 `<legend>`，而不是按 DOM 顺序猜。 */
function ownerOf(field: HTMLElement): string {
  return field.closest('fieldset')?.querySelector('legend')?.textContent ?? '';
}

describe('SynastryConsole 的可访问名现状（Task 8B 判据 7）', () => {
  it('地点三件的 accessible name 在两列里各重复一次，带前缀的四件各自唯一', () => {
    const { container } = mountConsole();
    const scope = within(container);

    // 裸串：LocationField 没有 ariaLabel 入参，两列各产出两份。
    expect(scope.getAllByLabelText('纬度')).toHaveLength(2);
    expect(scope.getAllByLabelText('经度')).toHaveLength(2);
    expect(scope.getAllByLabelText('出生城市搜索')).toHaveLength(2);

    // 前缀串：称谓、偏移、公历五段，两列共 14 个名字，每个只出现一次。
    const prefixed = [
      '甲方称谓',
      '乙方称谓',
      '甲方时区偏移（小时）',
      '乙方时区偏移（小时）',
      '甲方年',
      '甲方月',
      '甲方日',
      '甲方时',
      '甲方分',
      '乙方年',
      '乙方月',
      '乙方日',
      '乙方时',
      '乙方分',
    ];
    expect(prefixed).toHaveLength(14);
    prefixed.forEach((name) => expect(scope.getAllByLabelText(name)).toHaveLength(1));

    // 全页共用的分宫制只有一份（两造必须同口径）。
    expect(scope.getAllByLabelText('分宫制')).toHaveLength(1);
    // 未填坐标时不产出「清除地点」，故它的缺席也一并钉住，免得将来重复两份没人发现。
    expect(scope.queryAllByLabelText('清除地点')).toHaveLength(0);
  });

  it('重复的两份「纬度」分属甲方与乙方 fieldset：读屏听到的名字不区分，DOM 归属才区分', () => {
    const { container } = mountConsole();
    const scope = within(container);
    // WHY 不用 getByRole('legend')：本栈（@testing-library/dom 10.4.2 / jsdom 25.0.1 携带的
    // aria-query）不把 HTML 隐式角色 `legend` 暴露给 getByRole，按角色查必然 0 命中——
    // `<legend>` 确实在 DOM 里（SynastryConsole.tsx:52，两列共两个），被拒的是查询方法不是产品。
    // 复测：cd frontend && npx vitest run tests/components/synastry/SynastryConsole.test.tsx
    expect([...container.querySelectorAll('legend')].map((el) => el.textContent)).toEqual(['甲方', '乙方']);

    const latitudes = scope.getAllByLabelText('纬度');
    const longitudes = scope.getAllByLabelText('经度');
    expect(latitudes.map(ownerOf)).toEqual(['甲方', '乙方']);
    expect(longitudes.map(ownerOf)).toEqual(['甲方', '乙方']);
    expect(scope.getAllByLabelText('出生城市搜索').map(ownerOf)).toEqual(['甲方', '乙方']);
  });

  it('一列填了自己的坐标不会影响另一列，两造未齐时提交闸门仍然关着', () => {
    const { container, submitted } = mountConsole();
    const scope = within(container);
    const latitudes = scope.getAllByLabelText('纬度');
    const longitudes = scope.getAllByLabelText('经度');

    fireEvent.change(latitudes[0], { target: { value: '51.4769' } });
    fireEvent.change(longitudes[0], { target: { value: '-0.0005' } });
    expect(latitudes[0]).toHaveValue(51.4769);
    expect(longitudes[0]).toHaveValue(-0.0005);
    expect(latitudes[1]).toHaveValue(null); // 乙方一列没被顺带填上
    expect(longitudes[1]).toHaveValue(null);

    const nameA = scope.getByLabelText('甲方称谓') as HTMLInputElement;
    fireEvent.change(nameA, { target: { value: '先生' } });
    expect(nameA).toHaveValue('先生');
    expect(scope.getByLabelText('乙方称谓')).toHaveValue('');

    // 闸门：两造的生辰（六段下拉）都还没填，缺谁就点什么名。
    const hint = scope.getByText(/未填齐/);
    expect(hint).toHaveTextContent('甲方与乙方的公历年月日、时间或经纬度未填齐');
    const submit = scope.getByRole('button', { name: /开始合盘/ });
    expect(submit).toBeDisabled();
    fireEvent.click(submit);
    expect(submitted).toHaveLength(0);
  });
});
