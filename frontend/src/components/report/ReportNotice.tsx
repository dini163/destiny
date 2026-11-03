import { Link } from 'react-router-dom';
import { REPORT_ENTRIES } from '../../lib/reportReading';
import { ROUTES } from '../../nav';
import type { ReportProduct } from '../../types/report';

export function ReportNotice({ product }: { product?: ReportProduct }) {
  const entry = product ? REPORT_ENTRIES[product] : null;
  return (
    <section className="route-error">
      <h1>{entry ? '还没有可用的测算输入' : '这份报告链接暂不可用'}</h1>
      <p>
        {entry
          ? `请先到${entry.label}页完成排盘，再从结果区进入报告。`
          : '请检查链接，或回到首页继续探索。'}
      </p>
      <Link className="btn-primary" to={entry?.path ?? ROUTES.overview}>
        {entry ? `去${entry.label}查询` : '回到首页'}
      </Link>
    </section>
  );
}
