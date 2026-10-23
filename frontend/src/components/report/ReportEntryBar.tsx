import { Link } from 'react-router-dom';

import { Icon } from '../ui/Icon';

/**
 * 测算结果区的报告入口条：一行说明 + 跳转报告页的链接按钮。
 *
 * 三个入口页（八字命理 R2 / 八字合婚 R1 / 八字岁运 R3）共用；链接由
 * `lib/reportEntry.ts` 在提交时生成（输入已随链接存入 sessionStorage）。
 */
export function ReportEntryBar({ href, productName }: { href: string; productName: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-gold/25 bg-gradient-to-r from-gold/10 to-transparent px-4 py-3">
      <div className="flex items-center gap-2 text-sm text-ink-variant">
        <Icon name="sparkle" size={16} className="shrink-0 text-gold" />
        <span>
          本盘已排定，可进一步生成《{productName}》——按问题组织的深度解读报告。
        </span>
      </div>
      <Link
        to={href}
        className="rounded-element border border-gold/40 bg-gold/15 px-4 py-2 text-sm font-medium text-gold-bright transition-colors hover:bg-gold/25"
      >
        生成报告
      </Link>
    </div>
  );
}
