import { Icon } from '../ui/Icon';
import { BrandMark } from './BrandMark';
import { LocalDataControls } from '../ui/LocalDataControls';

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
    body: '以权威星历推算行星黄经与宫头；真太阳时按经度时差（每度 4 分钟）与均时差动态校准，经纬度解析全球坐标。',
  },
  {
    title: '古籍历法溯源',
    caption: 'CLASSICAL PROVENANCE',
    body: '依权威历法严谨推算二十四节气换气定柱；卦爻辞锚定《周易》通行本原文，杜绝虚构易辞与生搬硬造的星盘断语。',
  },
  {
    title: '隐私与天机安全',
    caption: 'PRIVACY · STATELESS',
    body: '普通排盘不在服务端保存。我的档案、卢恩秘匣和主题偏好保存在本机浏览器；报告输入在当前标签页暂存。人工确认交付的报告会在服务端保存固定版本直至到期清理。下钻链接可能包含生辰和地点，请勿公开转发；浏览器历史、下载文件和服务访问日志需分别管理。',
  },
];

/**
 * Global footer (PRD §2): the compliance disclaimer, the astronomical/calendar
 * provenance seals and the identity bar. Shared verbatim across every route.
 */
export function SiteFooter() {
  return (
    <footer className="site-footer border-t border-rim bg-void/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1536px] flex-col gap-gutter px-gutter py-margin">
        <div className="panel flex flex-col gap-4 p-5 md:flex-row md:items-center md:gap-6">
          <div className="flex shrink-0 items-center gap-2 text-gold">
            <Icon name="seal" size={20} />
            <span className="font-display text-base text-gold-soft">合规免责声明</span>
          </div>
          <p className="text-sm leading-relaxed text-ink-variant">{DISCLAIMER}</p>
        </div>

        <details className="footer-details"><summary>了解排盘依据与隐私保存</summary><div className="grid grid-cols-1 gap-gutter md:grid-cols-3">
          {SEALS.map((seal) => (
            <div key={seal.title} className="flex flex-col gap-2">
              <span className="label-caps text-gold">{seal.caption}</span>
              <span className="font-display text-base text-ink">{seal.title}</span>
              <p className="text-sm leading-relaxed text-ink-muted">{seal.body}</p>
            </div>
          ))}
        </div>

        </details><LocalDataControls />
        <div className="flex flex-col items-center justify-between gap-4 border-t border-rim pt-6 sm:flex-row">
          <BrandMark />
          <div className="label-caps flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-center">
            <span>VERSION 0.1.0 · PHASE 1</span>
            <span className="hidden h-3 w-px bg-rim sm:block" />
            <span>PRECISION CELESTIAL CALCULATOR</span>
            <span className="hidden h-3 w-px bg-rim sm:block" />
            <span>© DESTINY</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
