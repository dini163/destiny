import { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';

import { ReportHeader } from '../components/report/ReportHeader';
import { ReportPreviewGate } from '../components/report/ReportPreviewGate';
import { ReportSectionCard } from '../components/report/ReportSectionCard';
import { useReport } from '../hooks/useReport';
import { reportInputKey } from '../types/report';
import type { ReportDocument, ReportProduct } from '../types/report';
import { ROUTES } from '../nav';

/**
 * 付费报告阅读页（v2.1 §3A）：/report/:product（r1/r2/r3）。
 *
 * 入口在各测算结果页：按钮把该页的当前输入 JSON 存入 sessionStorage（`report_input_<p>`）
 * 后跳转本页；本页读取输入 → 自动请求免费预览 → 用户点「申请完整报告」后生成全文。
 * 生成结果带无状态签名链接（order_id/token/过期时间）；v1 人工交付，页面提供打印/存 PDF。
 */
export function ReportPage() {
  const { product } = useParams<{ product: string }>();
  const typed = (product as ReportProduct | undefined) ?? 'r1';
  const {
    preview,
    document: doc,
    previewError,
    generateError,
    isPreviewPending,
    isGenerating,
    requestPreview,
    generate,
  } = useReport();

  const stored = readStoredInput(typed);

  useEffect(() => {
    if (stored && !preview && !doc && !isPreviewPending && !previewError) {
      requestPreview(typed, stored);
    }
  }, [typed, stored, preview, doc, isPreviewPending, previewError, requestPreview]);

  if (!stored) {
    return <MissingInputNotice product={typed} />;
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-4 px-4 py-6">
      {preview ? <ReportHeader doc={preview} /> : null}

      {previewError ? <ErrorNote message={previewError.message} /> : null}
      {generateError ? <ErrorNote message={generateError.message} /> : null}

      {isPreviewPending ? <p className="text-sm text-ink-variant">正在生成预览…</p> : null}

      {!doc && preview ? (
        <ReportPreviewGate
          preview={preview}
          isGenerating={isGenerating}
          onGenerate={() => generate(typed, stored)}
        />
      ) : null}

      {doc ? <FullReport doc={doc} /> : null}
    </div>
  );
}

/** 完整报告视图：订单/有效期 + 打印入口 + 全部分章（摘要 → 主体 → 行动 → 证据 → 边界）。 */
function FullReport({ doc }: { doc: ReportDocument }) {
  return (
    <>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-ink-variant">
          报告订单号 {doc.order_id} · 链接有效期至{' '}
          {new Date(doc.expires_at).toLocaleDateString('zh-CN')}
        </p>
        <button
          type="button"
          onClick={() => window.print()}
          className="rounded-element border border-gold/40 bg-gold/15 px-3 py-1.5 text-xs font-medium text-gold-bright transition-colors hover:bg-gold/25"
        >
          打印 / 保存为 PDF
        </button>
      </div>

      <div className="flex flex-col gap-4">
        {doc.sections.map((section, index) => (
          <ReportSectionCard key={section.id} section={section} index={index} />
        ))}
      </div>
    </>
  );
}

/** 从 sessionStorage 读入口页交过来的输入；损坏/缺失都返回 undefined 走引导。 */
function readStoredInput(product: ReportProduct): unknown | undefined {
  try {
    const raw = sessionStorage.getItem(reportInputKey(product));
    if (!raw) return undefined;
    return JSON.parse(raw) as unknown;
  } catch {
    return undefined;
  }
}

/** 本页没有可用输入时的引导：告诉用户先到对应测算页查询。 */
function MissingInputNotice({ product }: { product: ReportProduct }) {
  const entries: Record<ReportProduct, { path: string; label: string }> = {
    r1: { path: ROUTES.baziHehun, label: '八字合婚' },
    r2: { path: ROUTES.baziNatal, label: '八字命理' },
    r3: { path: ROUTES.baziTransit, label: '八字岁运' },
  };
  const entry = entries[product];
  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-3 rounded-card border border-gold/20 bg-[#0e111a] p-6">
      <h1 className="font-display text-xl font-semibold text-ink">还没有可用的测算输入</h1>
      <p className="text-sm leading-relaxed text-ink-variant">
        报告需要你先在对应的测算页完成一次排盘。请到{entry.label}页查询后，再从结果区点击
        「生成报告」进入本页。
      </p>
      <Link
        to={entry.path}
        className="w-fit rounded-element border border-gold/40 bg-gold/15 px-4 py-2 text-sm font-medium text-gold-bright transition-colors hover:bg-gold/25"
      >
        去{entry.label}查询
      </Link>
    </div>
  );
}

function ErrorNote({ message }: { message: string }) {
  return (
    <div className="rounded-card border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
      {message}
    </div>
  );
}
