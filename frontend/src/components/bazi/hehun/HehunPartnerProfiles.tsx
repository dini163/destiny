import type { ReactNode } from 'react';

import { SourceNote } from '../../ui/SourceNote';
import { wuxingChip, wuxingText } from '../../../lib/wuxing';
import type { HehunNayin, HehunPartner, HehunSide } from '../../../types/baziHehun';

/** 一造的档案：档案是"这两个人是谁"，年命纳音是这一对的第三条事实，同区呈现（§8）。 */
export function HehunPartnerProfiles({
  male,
  female,
  nayin,
}: {
  male: HehunPartner;
  female: HehunPartner;
  nayin: HehunNayin;
}) {
  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ProfileBlock partner={male} side="male" />
        <ProfileBlock partner={female} side="female" />
      </div>
      <NayinBlock nayin={nayin} />
    </div>
  );
}

function ProfileBlock({ partner, side }: { partner: HehunPartner; side: HehunSide }) {
  const caption = side === 'male' ? '乾造' : '坤造';
  const current = partner.dayun.find((step) => step.is_current) ?? partner.dayun[0];
  return (
    <div className="flex flex-col gap-3 rounded-card border border-rim bg-[#0e111a] p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="label-caps text-gold">{caption}</span>
        <span className="text-sm text-ink-variant">{partner.name ?? '未署称谓'}</span>
      </div>

      <p className="numeric font-display text-lg text-ink">{partner.four_pillars}</p>

      <dl className="flex flex-col gap-1.5 text-sm">
        <Fact label="生肖">
          <span className="text-ink">{partner.zodiac}</span>
        </Fact>
        <Fact label="日主">
          <span className={`text-ink`}>
            {partner.day_master}
            <span className={`numeric ml-1 ${wuxingText(partner.day_master_element)}`}>
              {partner.day_master_element}
            </span>
          </span>
        </Fact>
        <Fact label="喜用">
          <ChipRow items={partner.favorable_elements} />
        </Fact>
        <Fact label="忌神">
          <ChipRow items={partner.unfavorable_elements} />
        </Fact>
        <Fact label="五行分布">
          <span className="flex flex-wrap gap-1.5">
            {partner.elements.map((row) => (
              <span
                key={row.element}
                className={`rounded-element px-2 py-0.5 text-xs ${wuxingChip(row.element)}`}
              >
                {row.element}
                <span className="numeric ml-1 opacity-80">{row.score.toFixed(1)}</span>
              </span>
            ))}
          </span>
        </Fact>
        {current ? (
          <Fact label={partner.dayun.some((step) => step.is_current) ? '当前大运' : '起运前'}>
            <span className="numeric text-ink">
              {current.ganzhi === '' ? '童限' : current.ganzhi} · {current.start_age}—
              {current.end_age} 岁 · {current.start_year}—{current.end_year}
            </span>
          </Fact>
        ) : null}
        <Fact label="起柱时刻">
          <span className="numeric text-ink">
            {partner.true_solar_time ?? '未校正（标准时直排）'}
          </span>
        </Fact>
      </dl>

      <table className="w-full text-xs">
        <caption className="sr-only">{`${caption}四柱`}</caption>
        <thead>
          <tr className="text-left text-ink-muted">
            {['柱', '干支', '十神', '纳音'].map((head) => (
              <th key={head} scope="col" className="font-normal">
                {head}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {partner.pillars.map((pillar) => (
            <tr key={pillar.position} className="border-t border-rim">
              <td className="py-1.5 text-ink-muted">{pillar.label}</td>
              <td className="numeric py-1.5 text-ink">{pillar.ganzhi}</td>
              <td className="py-1.5 text-ink-variant">{pillar.shishen_gan}</td>
              <td className="py-1.5 text-ink-muted">{pillar.nayin}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p className="text-xs text-ink-muted">
        {partner.tst_applied ? '本柱按真太阳时校正后起' : '本柱按标准时直排'}
      </p>
    </div>
  );
}

/** 年命纳音：两造的取象原文并置，关系与那一行账同段给出（§7.2）。 */
function NayinBlock({ nayin }: { nayin: HehunNayin }) {
  return (
    <div className="flex flex-col gap-2 rounded-card border border-rim bg-surface p-4">
      <span className="label-caps text-ink-muted">年命纳音 · 宜忌之外的第三条轴</span>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {([['乾', nayin.male], ['坤', nayin.female]] as const).map(([caption, side]) => (
          <div key={caption} className="flex flex-col gap-1">
            <span className="text-sm text-ink">
              <span className="text-ink-muted">{caption} · </span>
              <span className="numeric">{side.ganzhi}</span>
              {' '}
              <span className="font-display">{side.nayin}</span>
              <span className={`numeric ml-1 ${wuxingText(side.element)}`}>{side.element}</span>
            </span>
            <p className="text-xs leading-relaxed text-ink-variant">{side.imagery}</p>
            <SourceNote source={side.source} />
          </div>
        ))}
      </div>
      <div className="flex flex-wrap items-baseline gap-2 text-sm">
        <span className="text-ink">{nayin.phrase}</span>
        <span className="label-caps text-ink-muted">{nayin.relation}</span>
        <span className={`numeric ${nayin.delta < 0 ? 'text-wuxing-fire' : 'text-wuxing-wood'}`}>
          {nayin.delta < 0 ? `-${nayin.delta.toFixed(1)}` : `+${nayin.delta.toFixed(1)}`}
        </span>
      </div>
      <p className="text-xs leading-relaxed text-ink-muted">{nayin.reading}</p>
    </div>
  );
}

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-right">{children}</dd>
    </div>
  );
}

function ChipRow({ items }: { items: string[] }) {
  if (items.length === 0) {
    return <span className="text-xs text-ink-muted">该造本命盘未给出</span>;
  }
  return (
    <span className="flex flex-wrap gap-1.5">
      {items.map((element) => (
        <span key={element} className={`rounded-element px-2 py-0.5 text-xs ${wuxingChip(element)}`}>
          {element}
        </span>
      ))}
    </span>
  );
}
