import {
  Link,
  useLocation,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import { ReportReader } from '../components/report/ReportReader';
import { ReportNotice } from '../components/report/ReportNotice';
import { ReportHeader } from '../components/report/ReportHeader';
import { ReportPreviewGate } from '../components/report/ReportPreviewGate';
import { useReportReading } from '../hooks/useReportReading';
import { useI18n } from '../i18n/context';
import { isReportProduct } from '../lib/reportReading';
import type { ReportProduct } from '../types/report';
import { ROUTES } from '../nav';

export function ReportPage() {
  const { t } = useI18n();
  const { product } = useParams();
  const location = useLocation();
  const [query, setQuery] = useSearchParams();
  if (!isReportProduct(product)) return <ReportNotice />;
  // Remount per identity so a previous product/input cannot remain visible under a new URL.
  const startDate = query.get('start') ?? undefined;
  const stage = query.get('stage') ?? undefined;
  return (
    <>
      {product === 'r1' &&
        !location.hash.includes('delivery=') &&
        query.get('sample') !== '1' && (
          <label className="report-start-date">
            {t('关系阶段（可选）')}
            <select
              value={stage ?? 'unspecified'}
              onChange={(event) => {
                const next = new URLSearchParams(query);
                next.set('stage', event.target.value);
                setQuery(next);
              }}
            >
              <option value="unspecified">{t('暂不提供')}</option>
              <option value="dating">{t('相识或交往')}</option>
              <option value="long_term">{t('长期相处')}</option>
              <option value="repair">{t('修复分歧')}</option>
            </select>
            <span>{t('只用于组织沟通建议，不改变盘面计算。')}</span>
          </label>
        )}
      {product === 'r3' &&
        !location.hash.includes('delivery=') &&
        query.get('sample') !== '1' && (
          <label className="report-start-date">
            {t('报告起始日')}
            <input
              type="date"
              value={startDate ?? ''}
              onChange={(event) => {
                const next = new URLSearchParams(query);
                if (event.target.value) next.set('start', event.target.value);
                else next.delete('start');
                setQuery(next);
              }}
            />
            <span>{t('不选则从今天开始，连续十二个月。')}</span>
          </label>
        )}
      <ReportSession
        key={`${product}:${location.key}`}
        product={product}
        sample={query.get('sample') === '1'}
        fragment={location.hash}
        startDate={startDate}
        stage={stage}
      />
    </>
  );
}

function ReportSession({
  product,
  sample,
  fragment,
  startDate,
  stage,
}: {
  product: ReportProduct;
  sample: boolean;
  fragment: string;
  startDate?: string;
  stage?: string;
}) {
  const { t } = useI18n();
  const report = useReportReading(product, sample, fragment, startDate, stage);
  const doc =
    report.document ?? report.deliveredDocument ?? report.sampleDocument;
  const error =
    report.previewError ??
    report.generateError ??
    report.deliveryError ??
    report.sampleError;
  if (!report.input && !report.delivered && !sample)
    return <ReportNotice product={product} />;
  return (
    <div className="report-page">
      <div className="report-top">
        <Link to={ROUTES.overview}>← {t('返回发现')}</Link>
        <span>
          {sample
            ? t('真实计算样例 · 非个人测评')
            : report.delivered
              ? t('私密报告交付')
              : t('报告预览')}
        </span>
      </div>
      {error && (
        <div className="report-error" role="alert">
          {error.message}
        </div>
      )}
      {(report.isPreviewPending ||
        report.isFetchingDelivery ||
        report.isFetchingSample) && (
        <p className="page-loading" role="status">
          {t('正在准备报告…')}
        </p>
      )}
      {doc ? (
        <ReportReader doc={doc} delivered={report.delivered} />
      ) : report.preview ? (
        <div className="report-preview">
          <ReportHeader doc={report.preview} />
          <ReportPreviewGate
            preview={report.preview}
            isGenerating={report.isGenerating}
            onGenerate={() => report.generate(product, report.input)}
          />
        </div>
      ) : null}
    </div>
  );
}
