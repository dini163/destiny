import { Icon } from '../ui/Icon';
import type { ReportPreview } from '../../types/report';

/**
 * 免费预览门（v1：不接支付与试用）：预览说明 + 关键结论 + 完整报告章节清单 +
 * 内测生成入口。点击后由页面回调生成完整报告并切换到全文视图。
 */
export function ReportPreviewGate({
  preview,
  isGenerating,
  onGenerate,
}: {
  preview: ReportPreview;
  isGenerating: boolean;
  onGenerate: () => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-2 rounded-card border border-gold/25 bg-[var(--field-bg)] px-4 py-3">
        <Icon name="sparkle" size={16} className="mt-0.5 shrink-0 text-gold" />
        <p className="text-sm leading-relaxed text-ink-variant">
          {preview.notice}
        </p>
      </div>

      <section className="flex flex-col gap-2 rounded-card border border-gold/15 bg-gradient-to-b from-surface to-[var(--field-bg)] p-4 sm:p-5">
        <h2 className="label-caps text-gold">关键结论</h2>
        <ul className="flex flex-col gap-2">
          {preview.key_points.map((point) => {
            const split = point.indexOf('：');
            if (split <= 0)
              return (
                <li key={point} className="text-sm text-ink">
                  {point}
                </li>
              );
            return (
              <li
                key={point}
                className="flex flex-col gap-0.5 sm:flex-row sm:gap-3"
              >
                <span className="label-caps shrink-0 pt-0.5 text-gold">
                  {point.slice(0, split)}
                </span>
                <span className="text-sm leading-relaxed text-ink">
                  {point.slice(split + 1)}
                </span>
              </li>
            );
          })}
        </ul>
        <p className="text-xs text-ink-variant">
          完整报告共 {preview.section_count} 章。
        </p>
      </section>

      {preview.can_generate ? (
        <button
          type="button"
          onClick={onGenerate}
          disabled={isGenerating}
          className="rounded-card border border-gold/40 bg-gold/15 px-5 py-3 font-display text-sm font-semibold text-gold-bright transition-colors hover:bg-gold/25 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isGenerating ? '正在生成…' : '内测生成完整报告'}
        </button>
      ) : (
        <p className="text-base leading-loose text-ink-variant">
          完整报告由交付人员确认后提供。收到私密链接后，可直接打开阅读。
        </p>
      )}
    </div>
  );
}
