import { useState } from 'react';
import { DailyTimePanel } from '../components/portal/DailyTimePanel';
import { PortalHero } from '../components/portal/PortalHero';
import { QuestionEntries } from '../components/portal/QuestionEntries';
import { SystemCard } from '../components/portal/SystemCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import {
  PORTAL_CATEGORIES,
  PORTAL_SYSTEMS,
  type PortalCategoryId,
} from '../lib/portal';
type SystemFilter = PortalCategoryId | 'all';
const FILTERS = [
  { value: 'all' as const, label: '全部体系' },
  ...PORTAL_CATEGORIES.map((item) => ({ value: item.id, label: item.label })),
];
export function PortalPage() {
  const [filter, setFilter] = useState<SystemFilter>('all');
  const systems = PORTAL_SYSTEMS.filter(
    (item) => filter === 'all' || item.category === filter,
  );
  return (
    <div className="discovery-page">
      <PortalHero />
      <QuestionEntries />
      <section className="discovery-method">
        <span className="method-symbol" aria-hidden="true">
          知
        </span>
        <div>
          <h2>先读结论，再看它从何而来。</h2>
          <p>
            排盘依据、传统解释与生活建议，分层阅读。你可以参考，也可以保留不同的看法。
          </p>
        </div>
        <a href="#matrix-section" className="quiet-link">
          探索全部 {PORTAL_SYSTEMS.length} 个体系 ↗
        </a>
      </section>
      <section id="matrix-section" className="catalogue-section">
        <div className="discovery-heading">
          <div>
            <h2>找到你熟悉的那一种视角。</h2>
          </div>
          <SegmentedControl
            options={FILTERS}
            value={filter}
            onChange={setFilter}
            ariaLabel="体系类目筛选"
          />
        </div>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          {systems.map((system) => (
            <SystemCard key={system.slug} system={system} />
          ))}
        </div>
      </section>
      <details className="time-details">
        <summary>了解本次授时与历算基准</summary>
        <DailyTimePanel />
      </details>
    </div>
  );
}
