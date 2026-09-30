/**
 * 引擎拼好的一段白话：`whitespace-pre-line` 把 `\n` 原样断成多行，组件不增一字。
 *
 * 段落里的每一句都来自受控语料（`content/<sys>_plain.py`），拼接住在
 * `engines/plain_compose.py`——本件只固定「怎么读」，不固定「说什么」。
 * `DimensionGrid.tsx` 里那两处同款 `<p>` 属丙组计划的收编对象（spec §10 裁定 R7）：
 * 本轮随甲组首个消费者把件建起来，否则三个新页面各写一份才是真的重复。
 */
export function PlainProse({ text, className = '' }: { text: string; className?: string }) {
  return (
    <p className={`whitespace-pre-line font-display text-sm leading-relaxed text-ink ${className}`}>
      {text}
    </p>
  );
}
