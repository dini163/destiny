import { annotateGenderTerms } from '../../../lib/gender';
import { wuxingChip } from '../../../lib/wuxing';
import type { HehunYiJi } from '../../../types/baziHehun';

/**
 * 宜忌板（spec §7.4）。
 *
 * 六组恒在、序即响应给的阅读序（同宜 → 乾独宜 → 坤独宜 → 同忌 → 乾独忌 → 坤独忌）；
 * 页面不重排也不合并。一行 = 一个五行的通说配属（方位 / 五色 / 四时），那三样逐字来自
 * 后端配属表，不是这里现推的。
 *
 * 底部那句 `declaration` 逐字转录（后端 `HEHUN_YIJI_DECLARATION`）：它是这一段的
 * 覆盖范围声明 —— 宜忌取的是两造**喜用**的通说配属，不是玄空飞星那一套日课，两者的
 * 名字相同而算法无关，不写清楚就是让读者带走一个错的期待。空格照样出现（某一对的
 * 六组里可能有两组是空的），并如实标「无」——「查过了，这一组没有五行」也是结论。
 */
export function HehunYiJiPanel({ yiJi }: { yiJi: HehunYiJi }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {yiJi.groups.map((group) => (
          <div key={group.kind} className="flex flex-col gap-2 rounded-element bg-[#0e111a] p-3">
            <span className="label-caps text-gold">{annotateGenderTerms(group.kind)}</span>
            {group.items.length === 0 ? (
              <span className="text-xs text-ink-muted">无</span>
            ) : (
              <ul className="flex flex-col gap-1.5">
                {group.items.map((item) => (
                  <li key={`${group.kind}-${item.element}`} className="flex flex-wrap items-baseline gap-2 text-xs">
                    <span className={`rounded-element px-2 py-0.5 ${wuxingChip(item.element)}`}>
                      {item.element}
                    </span>
                    <span className="text-ink-variant">
                      {item.direction} · {item.color} · {item.season}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
      <p className="text-xs leading-relaxed text-ink-muted">{yiJi.declaration}</p>
    </div>
  );
}
