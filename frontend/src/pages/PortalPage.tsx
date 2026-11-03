import { useState } from 'react';
import { DailyTimePanel } from '../components/portal/DailyTimePanel';
import { PortalHero } from '../components/portal/PortalHero';
import { QuestionEntries } from '../components/portal/QuestionEntries';
import { SystemCard } from '../components/portal/SystemCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { useI18n } from '../i18n/context';
import {
  PORTAL_CATEGORIES,
  PORTAL_SYSTEMS,
  type PortalCategoryId,
} from '../lib/portal';
type SystemFilter = PortalCategoryId | 'all';
// Filter labels are source keys; each is looked up via `t()` at render time so
// category names translate alongside the rest of the portal chrome.
const FILTERS = [
  { value: 'all' as const, label: '全部体系' },
  ...PORTAL_CATEGORIES.map((item) => ({ value: item.id, label: item.label })),
];
export function PortalPage() {
  const { t } = useI18n();
  const [filter, setFilter] = useState<SystemFilter>('all');
  const systems = PORTAL_SYSTEMS.filter(
    (item) => filter === 'all' || item.category === filter,
  );
  const localizedFilters = FILTERS.map((f) => ({ ...f, label: t(f.label) }));
  return (
    <div className="discovery-page">
      <PortalHero />
      <QuestionEntries />
      <section className="discovery-method">
        <span className="method-symbol" aria-hidden="true">
          知
        </span>
        <div>
          <h2>{t('先读结论，再看它从何而来。')}</h2>
          <p>
            {t('排盘依据、传统解释与生活建议，分层阅读。你可以参考，也可以保留不同的看法。')}
          </p>
        </div>
        <a href="#matrix-section" className="quiet-link">
          {t('探索全部 {{count}} 个体系', { count: PORTAL_SYSTEMS.length })} ↗
        </a>
      </section>
      <section id="matrix-section" className="catalogue-section">
        <div className="discovery-heading">
          <div>
            <h2>{t('找到你熟悉的那一种视角。')}</h2>
          </div>
          <SegmentedControl
            options={localizedFilters}
            value={filter}
            onChange={setFilter}
            ariaLabel={t('体系类目筛选')}
          />
        </div>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {systems.map((system) => (
            <SystemCard key={system.slug} system={system} />
          ))}
        </div>
      </section>
      <details className="time-details">
        <summary>{t('了解本次授时与历算基准')}</summary>
        <DailyTimePanel />
      </details>
    </div>
  );
}
