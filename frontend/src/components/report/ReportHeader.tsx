import type { ReportDocument, ReportPreview } from '../../types/report';

/**
 * 报告页头部：标题 / 定位语 / 版本 / 生成日期 / 脱敏输入摘要 / 交付链接有效期。
 *
 * 预览与完整文档共用（两边的这些字段同源）。`expiresAt` 只在完整文档在场时显示
 * （交付链接的过期时间），预览阶段不画一个空的有效期。
 */
export function ReportHeader({ doc }: { doc: ReportDocument | ReportPreview }) {
  return (
    <header className="flex flex-col gap-3 rounded-card border border-gold/25 bg-gradient-to-br from-[#141823] to-[#0e111a] p-4 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="font-display text-2xl font-bold tracking-wide text-gold-bright">
          {doc.title}
        </h1>
        <span className="label-caps text-ink-variant">v{doc.version}</span>
      </div>
      <p className="text-sm text-ink-variant">{doc.tagline}</p>
      <dl className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-variant">
        <div>
          <dt className="label-caps">生成日期</dt>
          <dd className="mt-0.5">{doc.generated_date}</dd>
        </div>
        <div>
          <dt className="label-caps">输入摘要</dt>
          <dd className="mt-0.5">{doc.input_summary}</dd>
        </div>
        {'expires_at' in doc ? (
          <div>
            <dt className="label-caps">交付链接有效期至</dt>
            <dd className="mt-0.5">{new Date(doc.expires_at).toLocaleDateString('zh-CN')}</dd>
          </div>
        ) : null}
      </dl>
    </header>
  );
}
