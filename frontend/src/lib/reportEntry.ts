import { reportInputKey } from '../types/report';
import type { ReportProduct } from '../types/report';

/**
 * 报告入口：把当前测算页的输入存进 sessionStorage，返回报告页链接。
 *
 * 报告页（/report/:product）无状态读取这份输入自动生成预览。输入与测算页请求体
 * 逐字相同（r1=BaziHehunRequest / r2=BaziNatalRequest / r3=BaziTransitRequest），
 * 所以后端能用同一份 JSON 复算，前端也没有第二套序列化。
 */
export function reportEntryHref(product: ReportProduct, input: unknown): string {
  sessionStorage.setItem(reportInputKey(product), JSON.stringify(input));
  return `/report/${product}`;
}
