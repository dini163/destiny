import { Link } from 'react-router-dom';

import { useI18n } from '../../i18n/context';
import { Icon } from '../ui/Icon';

/**
 * Report entry strip below a cast result.
 *
 * Shared by three entry pages (BaZi natal R2 / hehun R1 / transit R3); the
 * destination href is generated at submit time by `lib/reportEntry.ts` (the
 * input travels with the link through sessionStorage). `productName` stays a
 * raw source-Chinese string at the call site — this component owns its
 * translation so pages do not have to import `useI18n` just for the two
 * strings living here.
 */
export function ReportEntryBar({ href, productName }: { href: string; productName: string }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-gold/25 bg-gradient-to-r from-gold/10 to-transparent px-4 py-3">
      <div className="flex items-center gap-2 text-sm text-ink-variant">
        <Icon name="sparkle" size={16} className="shrink-0 text-gold" />
        <span>
          {t('本盘已排定，可进一步生成《{{productName}}》——按问题组织的深度解读报告。', {
            productName: t(productName),
          })}
        </span>
      </div>
      <Link
        to={href}
        className="rounded-element border border-gold/40 bg-gold/15 px-4 py-2 text-sm font-medium text-gold-bright transition-colors hover:bg-gold/25"
      >
        {t('生成报告')}
      </Link>
    </div>
  );
}
