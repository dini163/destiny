import { Icon } from '../ui/Icon';
import { BrandMark } from './BrandMark';

/** PRD §4.3 — the site-wide compliance disclaimer, reproduced verbatim. */
const DISCLAIMER =
  '本平台所有命理排盘、星历计算及推演结果均基于数理模型与民俗哲学古籍整理，结果仅供娱乐与文化参考，不构成任何医疗、法律、财务或重大人生命运决策建议。';

interface Seal {
  title: string;
  caption: string;
  body: string;
}

/** Astronomical / classical-provenance seals (天文历法印鉴) — real stack facts. */
const SEALS: Seal[] = [
  {
    title: '天文与时空基准',
    caption: 'EPHEMERIS & TRUE SOLAR TIME',
    body: '瑞士星历 pyswisseph 计算行星黄经与均时差 E(t)；真太阳时按经度时差（每度 4 分钟）与轨道偏心率动态校准，经纬度解析全球坐标。',
  },
  {
    title: '古籍历法溯源',
    caption: 'CLASSICAL PROVENANCE',
    body: 'lunar-python 严谨二十四节气换气定柱；卦爻辞锚定《周易》通行本原文，杜绝虚构易辞与生搬硬造的星盘断语。',
  },
  {
    title: '隐私与天机安全',
    caption: 'PRIVACY · STATELESS',
    body: '后端为无状态纯计算 API：无账号、无数据库、不下发 cookie，排盘与推演结果算完即弃、不在服务端留存；浏览器端同样不做本地持久化，关闭页面即无痕。',
  },
];

/**
 * Global footer (PRD §2): the compliance disclaimer, the astronomical/calendar
 * provenance seals and the identity bar. Shared verbatim across every route.
 */
export function SiteFooter() {
  return (
    <footer className="border-t border-rim bg-void/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1536px] flex-col gap-gutter px-gutter py-margin">
        <div className="panel flex flex-col gap-4 p-5 md:flex-row md:items-center md:gap-6">
          <div className="flex shrink-0 items-center gap-2 text-gold">
            <Icon name="seal" size={20} />
            <span className="font-display text-base text-gold-soft">合规免责声明</span>
          </div>
          <p className="text-sm leading-relaxed text-ink-variant">{DISCLAIMER}</p>
        </div>

        <div className="grid grid-cols-1 gap-gutter md:grid-cols-3">
          {SEALS.map((seal) => (
            <div key={seal.title} className="flex flex-col gap-2">
              <span className="label-caps text-gold">{seal.caption}</span>
              <span className="font-display text-base text-ink">{seal.title}</span>
              <p className="text-sm leading-relaxed text-ink-muted">{seal.body}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col items-center justify-between gap-4 border-t border-rim pt-6 sm:flex-row">
          <BrandMark />
          <div className="label-caps flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-center">
            <span>VERSION 0.1.0 · PHASE 1</span>
            <span className="hidden h-3 w-px bg-rim sm:block" />
            <span>PRECISION CELESTIAL CALCULATOR</span>
            <span className="hidden h-3 w-px bg-rim sm:block" />
            <span>© 2025 DESTINY</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
