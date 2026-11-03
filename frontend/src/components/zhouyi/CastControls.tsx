import type { FormEvent } from 'react';

import type { CastMethod } from '../../types/zhouyi';
import { CAST_METHODS, coinLabel, lineValueMeta } from '../../lib/zhouyi';
import type { CoinFace } from '../../lib/zhouyi';
import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { ChineseDateTimeField } from '../ui/DateTimeFieldCombined';
import { SegmentedControl } from '../ui/SegmentedControl';
import { useI18n } from '../../i18n/context';

interface CastControlsProps {
  /** Chosen casting method. */
  method: CastMethod;
  onMethodChange: (method: CastMethod) => void;
  /** Optional divination question (free text). */
  question: string;
  onQuestionChange: (value: string) => void;
  /** Optional cast moment (`datetime-local` value); empty means "now" on the backend. */
  castTime: string;
  onCastTimeChange: (value: string) => void;
  /** Six throws of three coins — used only by the manual method. */
  manualCoins: CoinFace[][];
  onManualCoinsChange: (coins: CoinFace[][]) => void;
  /** A cast is in flight. */
  pending: boolean;
  /** Cast the hexagram. */
  onSubmit: () => void;
}

const METHOD_OPTIONS = CAST_METHODS.map((option) => ({ value: option.value, label: option.label }));

/**
 * The divination console (周易六爻 input stage).
 *
 * Zhouyi has no birth data, so this replaces the shared InputBar: the querent
 * picks one of the three real casting methods, optionally frames a question and a
 * cast moment, and — for the manual method only — enters the six coin throws.
 * Method labels and hints mirror `app.engines.zhouyi`; the coin faces (字=2 阴 /
 * 背=3 阳) are the engine's own encoding, so nothing about the cast is invented.
 */
export function CastControls({
  method,
  onMethodChange,
  question,
  onQuestionChange,
  castTime,
  onCastTimeChange,
  manualCoins,
  onManualCoinsChange,
  pending,
  onSubmit,
}: CastControlsProps) {
  const { t } = useI18n();
  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (pending) {
      return;
    }
    onSubmit();
  }

  const activeMethod = CAST_METHODS.find((option) => option.value === method);

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="compass" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">{t('周易六爻神机')}</h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                {t('纳甲六爻 · 真随机')}
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              {t('铜钱六掷起卦，定本卦、变卦、互卦，配世应、六亲、六神与纳甲干支，并附《周易》通行本卦辞、爻辞原文。三法皆由后端真实推演，绝无虚构。')}
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={pending}>
          <Icon name="compass" size={18} />
          {pending ? t('起卦推演中…') : t('起卦 · 排盘')}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">
        <LabeledField className="xl:col-span-7" label="起卦之法 / METHOD">
          <SegmentedControl
            ariaLabel="起卦方法"
            options={METHOD_OPTIONS}
            value={method}
            onChange={onMethodChange}
          />
          <p className="mt-1.5 text-xs leading-relaxed text-ink-muted">{activeMethod ? t(activeMethod.hint) : null}</p>
        </LabeledField>

        <div className="flex flex-col gap-4 xl:col-span-5">
          <LabeledField label="所占之事 / QUESTION" hint={<span className="text-ink-muted">可选</span>}>
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[var(--field-bg)] px-3 py-2 transition focus-within:border-rim-strong">
              <Icon name="seal" size={16} className="shrink-0 text-ink-muted" />
              <input
                type="text"
                value={question}
                onChange={(event) => onQuestionChange(event.target.value)}
                title={t('问题文字用于记录关注点；系统提供牌义或盘面规则参考，不会理解或验证现实事件。')}
                placeholder={t('例如：本月求谋可否得成？')}
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                aria-label={t('所占之事')}
              />
            </div>
          <p className="text-xs leading-relaxed text-ink-muted">{t('问题文字只用于记录关注点；解读来自盘面规则，请结合真实情境核对。')}</p>
          </LabeledField>

          <LabeledField label="起卦时刻 / CAST TIME" hint={<span className="text-ink-muted">留空取当前</span>}>
            <ChineseDateTimeField value={castTime} onChange={onCastTimeChange} ariaLabel="起卦" />
          </LabeledField>
        </div>
      </div>

      {method === 'manual' ? (
        <CoinThrowEditor coins={manualCoins} onChange={onManualCoinsChange} />
      ) : null}

      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 rounded-element border border-rim-soft bg-surface px-3 py-2 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold" />
          {t('铜钱摇卦与梅花时间由权威算法真实推算，每次起卦独立不可复现。')}
        </span>
        <span>{t('纳甲、六亲、六神、世应与卦爻辞均取自策展经典数据，未作运行时虚构。')}</span>
      </div>
    </form>
  );
}

/**
 * Six-throw coin editor for the manual method.
 *
 * Each throw is three toggleable coins (背=3 阳 / 字=2 阴); the live sum (6/7/8/9)
 * and its classical line name preview exactly how the engine will read the throw.
 */
function CoinThrowEditor({
  coins,
  onChange,
}: {
  coins: CoinFace[][];
  onChange: (coins: CoinFace[][]) => void;
}) {
  const { t } = useI18n();
  function toggleCoin(throwIndex: number, coinIndex: number): void {
    const next = coins.map((throwCoins) => throwCoins.slice());
    next[throwIndex][coinIndex] = next[throwIndex][coinIndex] === 3 ? 2 : 3;
    onChange(next);
  }

  return (
    <div className="flex flex-col gap-2 rounded-element border border-rim-soft bg-surface p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="label-caps">{t('手动铜钱六掷 · MANUAL COINS')}</span>
        <span className="text-[11px] text-ink-muted">{t('点选铜钱：字=2（阴）· 背=3（阳）')}</span>
      </div>
      <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2 lg:grid-cols-3">
        {coins.map((throwCoins, throwIndex) => {
          const sum = throwCoins.reduce((total, face) => total + face, 0);
          const meta = lineValueMeta(sum);
          return (
            <div
              key={throwIndex}
              className="flex items-center gap-2 rounded-element border border-rim bg-[var(--field-bg)]/60 px-2.5 py-2"
            >
              <span className="numeric w-11 shrink-0 text-[11px] text-ink-muted">{t('第 {{n}} 掷', { n: throwIndex + 1 })}</span>
              <div className="flex items-center gap-1">
                {throwCoins.map((face, coinIndex) => (
                  <button
                    key={coinIndex}
                    type="button"
                    onClick={() => toggleCoin(throwIndex, coinIndex)}
                    aria-pressed={face === 3}
                    aria-label={t('第{{m}}掷第{{c}}枚：{{label}}', { m: throwIndex + 1, c: coinIndex + 1, label: coinLabel(face) })}
                    className={
                      face === 3
                        ? 'flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-b from-gold-bright to-gold text-xs font-bold text-[var(--on-gold)] transition'
                        : 'flex h-7 w-7 items-center justify-center rounded-full border border-rim-strong bg-surface text-xs text-ink-muted transition hover:text-ink'
                    }
                  >
                    {coinLabel(face)}
                  </button>
                ))}
              </div>
              <span className="numeric ml-auto text-xs text-gold-bright">={sum}</span>
              <span
                className={`w-9 shrink-0 text-right text-[11px] ${meta.moving ? 'text-gold-soft' : 'text-ink-muted'}`}
              >
                {meta.name}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
