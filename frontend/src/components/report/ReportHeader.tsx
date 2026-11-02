import type { ReportDocument, ReportPreview } from '../../types/report';
export function ReportHeader({ doc }: { doc: ReportDocument | ReportPreview }) {
  const summary =
    'sections' in doc
      ? doc.sections.find((section) => section.kind === 'summary')?.bullets
      : doc.summary;
  const observation =
    doc.product === 'r2'
      ? summary
          ?.find((line) => line.startsWith('先看重点：'))
          ?.slice('先看重点：'.length)
      : undefined;
  return (
    <header className="report-cover">
      <div className="cover-meta">
        <span>PERSONAL READING</span>
        <span>传统文化 · 自我观察</span>
      </div>
      <p className="cover-subtitle">{doc.title}</p>
      <h1>{observation ?? doc.tagline}</h1>
      <p className="cover-description">
        给自己多一种理解的视角，把选择留在现实生活里。
      </p>
      <div className="cover-facts">
        <span>版本 {doc.version}</span>
        <span>{doc.generated_date}</span>
        <span>{doc.input_summary}</span>
      </div>
    </header>
  );
}
