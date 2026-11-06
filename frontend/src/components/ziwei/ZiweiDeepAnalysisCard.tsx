import { useI18n } from '../../i18n/context';
import { ResultCard } from '../ui/ResultCard';

export interface ZiweiTopicTab {
  key: string;
  label: string;
  palaceName: string;
}

export const ZIWEI_TOPIC_TABS: ZiweiTopicTab[] = [
  { key: 'mingGong', label: '命格', palaceName: '命宫' },
  { key: 'personality', label: '性格', palaceName: '命宫' },
  { key: 'fuQi', label: '感情', palaceName: '夫妻' },
  { key: 'guanLu', label: '事业', palaceName: '官禄' },
  { key: 'caiBo', label: '财运', palaceName: '财帛' },
  { key: 'jiE', label: '健康', palaceName: '疾厄' },
  { key: 'xiongDi', label: '兄弟', palaceName: '兄弟' },
  { key: 'ziNv', label: '子女', palaceName: '子女' },
  { key: 'qianYi', label: '迁移', palaceName: '迁移' },
  { key: 'jiaoYou', label: '交友', palaceName: '仆役' },
  { key: 'tianZhai', label: '田宅', palaceName: '田宅' },
  { key: 'fuDe', label: '福德', palaceName: '福德' },
  { key: 'fuMu', label: '父母', palaceName: '父母' },
];

interface ZiweiDeepAnalysisCardProps {
  analysis: Record<string, string> | null;
  activeTopic: string;
  onSelectTopic: (topic: string) => void;
  loading?: boolean;
}

export function ZiweiDeepAnalysisCard({
  analysis,
  activeTopic,
  onSelectTopic,
  loading = false,
}: ZiweiDeepAnalysisCardProps) {
  const { t } = useI18n();
  const currentContent = analysis ? analysis[activeTopic] ?? '' : '';

  return (
    <ResultCard
      title="十三维深度详批 · 经典断语库"
      icon="compass"
      elevated
    >
      {/* ── Topic Switcher Tabs ── */}
      <div className="flex flex-wrap gap-1.5 border-b border-rim pb-3">
        {ZIWEI_TOPIC_TABS.map((tab) => {
          const isActive = tab.key === activeTopic;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => onSelectTopic(tab.key)}
              className={`rounded-element px-3 py-1.5 text-xs font-medium transition-all ${
                isActive
                  ? 'border border-gold/40 bg-gold/15 text-gold-bright shadow-sm'
                  : 'border border-rim bg-surface/40 text-ink-variant hover:border-rim-strong hover:text-ink'
              }`}
            >
              {t(tab.label)}
            </button>
          );
        })}
      </div>

      {/* ── Content Body ── */}
      {loading ? (
        <div className="flex h-40 items-center justify-center text-sm text-ink-muted">
          <span className="animate-pulse">{t('正在载入断语推演…')}</span>
        </div>
      ) : currentContent ? (
        <div className="flex flex-col gap-3 text-sm leading-relaxed text-ink">
          <MarkdownViewer text={currentContent} />
        </div>
      ) : (
        <div className="py-6 text-center text-sm text-ink-muted">
          {t('暂无推演内容')}
        </div>
      )}
    </ResultCard>
  );
}

function MarkdownViewer({ text }: { text: string }) {
  const lines = text.split('\n');

  return (
    <div className="flex flex-col gap-2">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} className="h-1.5" />;
        }

        // Section header: **【...】**
        const sectionMatch = trimmed.match(/^\*\*【(.+?)】\*\*$/);
        if (sectionMatch) {
          return (
            <div key={idx} className="pt-3 pb-1 first:pt-0 border-b border-rim/30">
              <span className="font-display text-base font-semibold text-gold-bright">
                【{sectionMatch[1]}】
              </span>
            </div>
          );
        }

        // Horizontal rule
        if (trimmed === '---') {
          return <hr key={idx} className="my-3 border-rim" />;
        }

        // H2 Header
        if (trimmed.startsWith('## ')) {
          return (
            <div key={idx} className="pt-2 pb-0.5">
              <h3 className="font-display text-base font-semibold text-gold">
                {trimmed.slice(3)}
              </h3>
            </div>
          );
        }

        // H3 Header
        if (trimmed.startsWith('### ')) {
          return (
            <div key={idx} className="pt-1.5 pb-0.5">
              <h4 className="font-display text-sm font-semibold text-ink">
                {trimmed.slice(4)}
              </h4>
            </div>
          );
        }

        // Blockquote
        if (trimmed.startsWith('> ')) {
          return (
            <blockquote
              key={idx}
              className="my-1.5 rounded-r-element border-l-2 border-gold/40 bg-surface/60 px-3.5 py-2 font-body text-sm leading-relaxed text-ink-variant"
            >
              {trimmed.slice(2)}
            </blockquote>
          );
        }

        // Render line with bold inline **text**
        const parts = line.split(/\*\*(.+?)\*\*/);
        return (
          <p key={idx} className="font-body text-sm sm:text-[15px] leading-[1.8] text-ink">
            {parts.map((part, pIdx) =>
              pIdx % 2 === 1 ? (
                <strong key={pIdx} className="font-semibold text-gold-bright">
                  {part}
                </strong>
              ) : (
                part
              )
            )}
          </p>
        );
      })}
    </div>
  );
}

