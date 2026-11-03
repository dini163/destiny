import { Link } from 'react-router-dom';
import { useI18n } from '../../i18n/context';
import { REPORT_ENTRIES } from '../../lib/reportReading';
import { ROUTES } from '../../nav';
import type { ReportProduct } from '../../types/report';

export function ReportNotice({ product }: { product?: ReportProduct }) {
  const { t } = useI18n();
  const entry = product ? REPORT_ENTRIES[product] : null;
  return (
    <section className="route-error">
      <h1>{entry ? t('还没有可用的测算输入') : t('这份报告链接暂不可用')}</h1>
      <p>
        {entry
          ? t('请先到{{label}}页完成排盘，再从结果区进入报告。', { label: t(entry.label) })
          : t('请检查链接，或回到首页继续探索。')}
      </p>
      <Link className="btn-primary" to={entry?.path ?? ROUTES.overview}>
        {entry ? t('去{{label}}查询', { label: t(entry.label) }) : t('回到首页')}
      </Link>
    </section>
  );
}
