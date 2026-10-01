import { expect } from 'vitest';

/**
 * 源码扫的「字面次序」钉：先把每个锚点各自钉一遍存在性，再逐对钉 `indexOf` 递增。
 *
 * 为什么要拆成两步：`String.prototype.indexOf` 在锚点缺席时返回 -1，而 `-1` 小于任何正数——
 * 只写 `expect(src.indexOf(a)).toBeLessThan(src.indexOf(b))` 的钉，在 `a` 被整行删掉后照样绿。
 * 本计划里这个形状栽了四次（终审的 I-1 是最后一次），故把它收成一个函数：次序钉自带存在性钉，
 * 想漏都漏不掉。锚点一律挑**看得见的字**或整段 JSX 挂载字面，不挑 Tailwind 类名子串——
 * 类名是纯样式，改一次配色就该绿的钉会假红。
 * 件只管字面与次序；「第一子元素」「同块」这类结构断言归渲染测，别往这里塞。
 */
export function pinLiteralOrder(src: string, anchors: string[]): void {
  for (const anchor of anchors) {
    expect(src).toContain(anchor);
  }
  for (let i = 0; i + 1 < anchors.length; i += 1) {
    expect(src.indexOf(anchors[i])).toBeLessThan(src.indexOf(anchors[i + 1]));
  }
}
