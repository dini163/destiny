import { useEffect, useState, type MouseEvent } from 'react';
import type { ReportDocument } from '../../types/report';
import {
  deliveryLink,
  reportAction,
  reportHighlights,
} from '../../lib/reportReading';
import { ReportHeader } from './ReportHeader';
import { ReportSectionCard } from './ReportSectionCard';

export function ReportReader({
  doc,
  delivered = false,
}: {
  doc: ReportDocument;
  delivered?: boolean;
}) {
  const [notice, setNotice] = useState('');
  const action = reportAction(doc);
  function navigateWithinReport(event: MouseEvent<HTMLElement>) {
    const link = (event.target as Element).closest('a');
    const target = link?.getAttribute('href');
    if (target?.startsWith('#')) {
      event.preventDefault();
      document
        .getElementById(target.slice(1))
        ?.scrollIntoView({ block: 'start' });
    }
  }
  useEffect(() => {
    const opened: HTMLDetailsElement[] = [];
    const before = () =>
      document
        .querySelectorAll<HTMLDetailsElement>(
          '.report-main details:not([open])',
        )
        .forEach((node) => {
          opened.push(node);
          node.open = true;
        });
    const after = () =>
      opened.splice(0).forEach((node) => {
        node.open = false;
      });
    window.addEventListener('beforeprint', before);
    window.addEventListener('afterprint', after);
    return () => {
      window.removeEventListener('beforeprint', before);
      window.removeEventListener('afterprint', after);
    };
  }, []);
  async function copyLink() {
    try {
      await navigator.clipboard.writeText(deliveryLink(doc));
      setNotice(
        '交付链接已复制；任何持有此链接的人都可以在有效期内阅读，请仅私下转发。',
      );
    } catch {
      setNotice('无法复制，请使用收到的原始交付链接。');
    }
  }
  return (
    <div className="reader-layout">
      <aside className="reader-toc" aria-label="报告目录">
        <h2>{doc.title}</h2>
        <nav onClick={navigateWithinReport}>
          <a href="#report-overview">报告概览</a>
          <a href="#reading-insights">三个重点</a>
          <a href="#reading-action">今天的小行动</a>
          <a href="#reading-full">完整章节</a>
        </nav>
        <p className="reader-toc-note">
          这是一份观察的邀请，
          <br />
          选择始终在你自己手里。
        </p>
      </aside>
      <article className="report-main">
        <div id="report-overview">
          <ReportHeader doc={doc} />
        </div>
        <section className="reader-section" id="reading-insights">
          <h2>把注意力，放在真正有用的地方。</h2>
          <ol className="insight-list">
            {reportHighlights(doc).map((point, index) => {
              const colon = point.indexOf('：');
              return (
                <li className="insight" key={point}>
                  <span className="insight-number">0{index + 1}</span>
                  <div>
                    <h3>{colon > 0 ? point.slice(0, colon) : '一个观察'}</h3>
                    <p>{colon > 0 ? point.slice(colon + 1) : point}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        </section>
        {action && (
          <section id="reading-action" className="action-block">
            <h2>从一件可以试试的小事开始。</h2>
            <p>{action}</p>
            <label className="action-check">
              <input type="checkbox" />
              我想试试
            </label>
          </section>
        )}
        <p className="reader-boundary">
          历法排盘可以复算；传统解释不等于经过验证的性格测评或未来预测。请用现实经历判断它是否适合你。
        </p>
        <section className="reader-section" id="reading-full">
          <h2>按你的节奏，慢慢读完。</h2>
          <div className="report-chapters">
            {doc.sections.map((section, index) => (
              <ReportSectionCard
                key={section.id}
                section={section}
                index={index}
              />
            ))}
          </div>
        </section>
      </article>
      <aside className="reader-companion">
        <h2>
          读完之后，
          <br />
          再回到生活里。
        </h2>
        <p>挑出一条对你有用的观察，尝试记录，再看看它是否真的适合自己。</p>
        <button
          className="btn-ghost"
          type="button"
          onClick={() => window.print()}
        >
          打印 / 保存为 PDF
        </button>
        {delivered && (
          <button className="btn-ghost" type="button" onClick={copyLink}>
            复制私密交付链接
          </button>
        )}
        <p role="status">{notice}</p>
        <small>
          版本 {doc.version} · {doc.generated_date}
          <br />
          {delivered ? '人工确认交付' : '内测生成，尚未人工审核'}
        </small>
      </aside>
      <nav
        className="mobile-reading-bar"
        aria-label="阅读快捷导航"
        onClick={navigateWithinReport}
      >
        <a href="#report-overview">概览</a>
        <a href="#reading-insights">重点</a>
        <a href="#reading-action">小行动</a>
        <a href="#reading-full">看依据</a>
      </nav>
    </div>
  );
}
