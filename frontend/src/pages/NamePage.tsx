import type { ReactNode } from 'react';

import { CharProvenanceTable } from '../components/name/CharProvenanceTable';
import { FiveGrids } from '../components/name/FiveGrids';
import { NameInputForm } from '../components/name/NameInputForm';
import { NameSummaryScore } from '../components/name/NameSummaryScore';
import { SancaiStrip } from '../components/name/SancaiStrip';
import { Icon } from '../components/ui/Icon';
import type { IconName } from '../components/ui/Icon';
import { ProvenancePanel } from '../components/ui/ProvenancePanel';
import { ResultCard } from '../components/ui/ResultCard';
import { useNameAnalysis } from '../hooks/useNameAnalysis';
import type { NameAnalysis } from '../types/name';

/**
 * 姓名学五格剖象页（PRD §6.5，设计稿 #NAME-KX-812025）。
 *
 * 一次提交换一整套可核对的推导：字级笔画算式 → 五格 → 三才 → 综合指数 → 溯源。
 * 设计稿里的 字性流注 / 姓名内五行环流 / 贵人辅弼系数 / 财禄拓疆潜能 / 改名备选字库
 * 一律不做——它们没有可署名的规则（spec §2.5、决策七），宁可页面少一块。
 */
export function NamePage() {
  const name = useNameAnalysis();

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <NameInputForm
        pending={name.isPending}
        error={name.error}
        onSubmit={(request) => name.mutate(request)}
      />

      {name.isPending && !name.data ? (
        <p className="label-caps text-ink-muted">正在核定康熙笔画并推演五格…</p>
      ) : null}

      {name.data ? <NameResults analysis={name.data} /> : null}
    </div>
  );
}

/** 上游 spec §8.2 的一个区块：锚点、卡面与内容。 */
interface SectionSpec {
  id: string;
  label: string;
  title: string;
  eyebrow: string;
  icon: IconName;
  body: ReactNode;
}

/**
 * 区块顺序即锚点顺序；算不出的区块从这张表里就消失，
 * 于是导航与正文同时少一项（spec §8.2 规则 2、3）。
 */
function sectionsFor(analysis: NameAnalysis): SectionSpec[] {
  const specs: Array<SectionSpec | null> = [
    {
      id: 'chars',
      label: '字级溯源',
      title: '康熙笔画核定',
      eyebrow: 'STROKE PROVENANCE',
      icon: 'search',
      body: <CharProvenanceTable chars={analysis.chars} />,
    },
    {
      id: 'grids',
      label: '五格',
      title: '五格剖象全景图谱',
      eyebrow: 'FIVE GRIDS',
      icon: 'compass',
      body: <FiveGrids grids={analysis.grids} />,
    },
    analysis.sancai
      ? {
          id: 'sancai',
          label: '三才',
          title: '三才配置深度研判',
          eyebrow: 'SANCAI · 生克关系',
          icon: 'seal',
          body: <SancaiStrip sancai={analysis.sancai} grids={analysis.grids} />,
        }
      : null,
    analysis.score
      ? {
          id: 'index',
          label: '综合指数',
          title: '姓名综合气象指数',
          eyebrow: 'INDEX · 五格加权',
          icon: 'gauge',
          body: <NameSummaryScore score={analysis.score} />,
        }
      : null,
    {
      id: 'provenance',
      label: '数据溯源',
      title: '数据溯源',
      eyebrow: 'PROVENANCE',
      icon: 'vault',
      body: (
        <ProvenancePanel
          tables={analysis.provenance.tables}
          meta={[
            {
              label: '笔画语料',
              value: `Unihan ${analysis.provenance.corpus.unicode_version}（${analysis.provenance.corpus.size.toLocaleString('en-US')} 条）`,
              title: analysis.provenance.corpus.source,
            },
            {
              label: '语料生成日',
              value: analysis.provenance.corpus.corpus_date,
              title: '固化入库的 Unihan 发布日期，非本次请求时间',
            },
          ]}
          notes={[
            '字级五行、姓名内五行环流与贵人/财禄系数未实现：无可署名的规则来源（spec 决策七）。',
            '一简对多繁由用户指定正体后才有笔画；本系统不代作主张（spec 决策六）。',
          ]}
        />
      ),
    },
  ];

  return specs.filter((spec): spec is SectionSpec => spec !== null);
}

function NameResults({ analysis }: { analysis: NameAnalysis }) {
  const sections = sectionsFor(analysis);

  return (
    <>
      <NameSummary analysis={analysis} />

      <nav
        aria-label="姓名学分区"
        className="sticky top-0 z-10 flex flex-wrap items-center gap-x-4 gap-y-2 border-y border-rim bg-void/85 py-2 backdrop-blur"
      >
        {sections.map((section) => (
          <a
            key={section.id}
            href={`#${section.id}`}
            className="label-caps text-ink-muted hover:text-gold-soft"
          >
            {section.label}
          </a>
        ))}
      </nav>

      <div className="flex flex-col gap-6">
        {sections.map((section) => (
          <div key={section.id} id={section.id} className="scroll-mt-20">
            <ResultCard title={section.title} eyebrow={section.eyebrow} icon={section.icon} elevated>
              {section.body}
            </ResultCard>
          </div>
        ))}
      </div>
    </>
  );
}

/** 姓名 + 正体 + 模态公式：让"用了哪条分支"在最上面就能核对（spec §6.2）。 */
function NameSummary({ analysis }: { analysis: NameAnalysis }) {
  const { input, warnings } = analysis;

  return (
    <div className="panel-raised flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="label-caps">核定姓名 · RESOLVED</span>
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-display text-2xl font-semibold text-gold-bright text-glow-gold sm:text-3xl">
              {input.surname}
              {input.given}
            </span>
            <Icon name="arrowRight" size={20} className="text-gold" />
            <span className="font-display text-2xl text-ink sm:text-3xl">
              {input.resolved_traditional}
            </span>
            <span className="label-caps rounded-element bg-gold/15 px-2 py-1 text-gold">
              {input.modality}
            </span>
          </div>
        </div>
      </div>

      <div className="gold-rule" />

      <p className="text-sm leading-relaxed text-ink-variant">{input.modality_formula}</p>

      {warnings.length > 0 ? (
        <p className="flex items-start gap-2 text-sm text-wuxing-fire">
          <Icon name="alert" size={16} className="mt-0.5 shrink-0" />
          <span>
            以下字的康熙笔画不在本语料范围内，相关五格与指数不予推算：
            {warnings.map((code) => code.split(':')[1]).join('、')}
          </span>
        </p>
      ) : null}
    </div>
  );
}
