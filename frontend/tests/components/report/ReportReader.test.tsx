import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ReportReader } from '../../../src/components/report/ReportReader';
import { readFixture } from '../../lib/readFixture';
import type { ReportDocument } from '../../../src/types/report';

describe('真实报告阅读', () => {
  it('展示所有真实章节和生活建议，依据默认折叠且可展开', () => {
    const doc = readFixture('report-r2') as ReportDocument;
    const { container } = render(<ReportReader doc={doc} />);
    for (const section of doc.sections)
      expect(
        screen.getByRole('heading', { name: section.title }),
      ).toBeInTheDocument();
    expect(screen.getByText('从一件可以试试的小事开始。')).toBeInTheDocument();
    const details = container.querySelector('details')!;
    expect(details.open).toBe(false);
    fireEvent.click(details.querySelector('summary')!);
    expect(details.open).toBe(true);
    expect(screen.queryByText('盘面事实')).not.toBeInTheDocument();
  });
  it('样例没有可复制的个人交付凭据', () => {
    const doc = readFixture('report-r3') as ReportDocument;
    render(<ReportReader doc={doc} />);
    expect(
      screen.queryByRole('button', { name: '复制私密交付链接' }),
    ).not.toBeInTheDocument();
  });
});
