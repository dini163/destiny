import { PlainProse } from '../ui/PlainProse';
import { useI18n } from '../../i18n/context';
import type { CardRef, LenormandReading, SignificatorInfo } from '../../types/lenormand';

/**
 * The 组合直读透镜 — Lenormand's core reading surface.
 *
 * It opens with the whole-spread plain retelling, then shows the polarity balance,
 * the combination pairs the engine derived for this layout (each read as
 * `subject × modifier → phrase`), and — when a 指示牌 was set — where the querent
 * sits with the cards behind / ahead / above / below. Every phrase, paragraph and
 * card comes straight from the response; nothing is invented here.
 */
export function CombinationLens({ reading }: { reading: LenormandReading }) {
  const { t } = useI18n();
  const { combinations, significator, positive_count, neutral_count, negative_count } = reading;

  return (
    <div className="flex flex-col gap-5">
      {/* 整阵白话排在最前：spec §10 的「白话在上、专业判语在下」在这一张卡里的形状。
          段落的字全部由后端装配（T8：阵开篇句 + 按位序逐张牌义），本件一个字都不组、
          一行都不折——`PlainProse` 的 `whitespace-pre-line` 就是「不折」的机器保证。
          这里不引 T9 的 `PlainSectionList`：那是「一格一段」的列表件，整阵只有一段。 */}
      <div className="flex flex-col gap-2">
        <span className="label-caps">{t('整阵白话 · IN PLAIN WORDS')}</span>
        <PlainProse text={reading.plain_summary} />
      </div>

      <PolarityBar positive={positive_count} neutral={neutral_count} negative={negative_count} />

      {significator ? <SignificatorPanel significator={significator} /> : null}

      <div className="flex flex-col gap-2">
        <span className="label-caps">{t('组合直读 · COMBINATIONS')}</span>
        {combinations.length === 0 ? (
          <p className="text-sm text-ink-muted">{t('此牌阵只有一张牌，暂无组合可读。')}</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {combinations.map((combo, index) => (
              <li
                key={index}
                className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 rounded-element border border-rim-soft bg-surface px-3 py-2"
              >
                <span className="font-display text-sm text-ink">
                  {combo.left.name_zh}
                  <span className="mx-1 text-gold">×</span>
                  {combo.right.name_zh}
                </span>
                <span className="text-gold-soft">→</span>
                <span className="font-display text-sm text-gold-bright">{combo.phrase}</span>
                <span className="label-caps ml-auto text-ink-muted">{combo.context}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/** A stacked bar of the 积极 / 中性 / 消极 card counts. */
function PolarityBar({ positive, neutral, negative }: { positive: number; neutral: number; negative: number }) {
  const { t } = useI18n();
  const total = Math.max(positive + neutral + negative, 1);
  const segments = [
    { label: '积极', count: positive, className: 'bg-gold-bright' },
    { label: '中性', count: neutral, className: 'bg-ink-muted' },
    { label: '消极', count: negative, className: 'bg-wuxing-fire' },
  ];
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="label-caps">{t('吉凶极性 · POLARITY')}</span>
        <span className="numeric text-xs text-ink-muted">
          {t('积极 {{p}} · 中性 {{n}} · 消极 {{neg}}', { p: positive, n: neutral, neg: negative })}
        </span>
      </div>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-surface-raised">
        {segments.map((segment) =>
          segment.count > 0 ? (
            <span
              key={segment.label}
              className={segment.className}
              style={{ width: `${(segment.count / total) * 100}%` }}
            />
          ) : null,
        )}
      </div>
    </div>
  );
}

/** Where the 指示牌 landed and the cards along its row and column. */
function SignificatorPanel({ significator }: { significator: SignificatorInfo }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-2 rounded-element border border-gold/25 bg-gold/5 px-3 py-2.5">
      <span className="label-caps text-gold">
        {t('指示牌 · {{name}}（第 {{r}} 行第 {{c}} 列）', { name: significator.name_zh, r: significator.row + 1, c: significator.col + 1 })}
      </span>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <DirectionRow label={t('身后 · 过去')} refs={significator.behind} />
        <DirectionRow label={t('眼前 · 未来')} refs={significator.ahead} />
        <DirectionRow label={t('其上 · 显意识')} refs={significator.above} />
        <DirectionRow label={t('其下 · 潜意识')} refs={significator.below} />
      </div>
    </div>
  );
}

/** One direction's card list beside the significator. */
function DirectionRow({ label, refs }: { label: string; refs: CardRef[] }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-0.5">
      <span className="label-caps text-ink-muted">{label}</span>
      <span className={`text-xs leading-relaxed ${refs.length ? 'text-ink-variant' : 'text-ink-muted'}`}>
        {refs.length ? refs.map((ref) => `${ref.number} ${ref.name_zh}`).join(' · ') : t('（无）')}
      </span>
    </div>
  );
}
