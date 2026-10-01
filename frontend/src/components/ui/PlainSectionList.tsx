import { PlainProse } from './PlainProse';

/** 一个小节：`title` 是盘面那一格的名字（宫名/卦宫），`text` 是引擎拼好的整段白话。 */
export interface PlainSection {
  title: string;
  text: string;
}

/**
 * 「一格一段」的共用列表（多系统白话 spec §10 丙组）。
 *
 * 存在的理由是一条实测事实：紫微十二宫与奇门九宫是同一形状——每格一段、段内以 `\n`
 * 分行、标题就是盘面那一格的名字。两边各写一份，就会有一边先漂掉 `whitespace-pre-line`
 * 或者偷偷加一句连接词（那正是 spec §10 给 `PlainProse` 立的禁区）。
 * 本件只固定「怎么排」，一个字也不写。
 */
export function PlainSectionList({ sections }: { sections: PlainSection[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
      {sections.map((section) => (
        <article key={section.title} className="flex flex-col gap-2 rounded-card border border-rim bg-surface p-4">
          <h3 className="font-display text-base text-gold-bright">{section.title}</h3>
          <PlainProse text={section.text} />
        </article>
      ))}
    </div>
  );
}
