import { useEffect, useState } from 'react';
import { computeBaziZangfu, type BaziZangfuItem } from '../../api/bazi';
import { useI18n } from '../../i18n/context';
import { Icon } from '../ui/Icon';

interface ZangfuGuideCardProps {
  branches: string[];
}

export function ZangfuGuideCard({ branches }: ZangfuGuideCardProps) {
  const { t } = useI18n();
  const [items, setItems] = useState<BaziZangfuItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    if (!branches || branches.length === 0) {
      setItems([]);
      return;
    }
    setLoading(true);
    computeBaziZangfu(branches)
      .then((res) => {
        if (active) {
          setItems(res.items);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [branches.join(',')]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4 text-xs text-ink-muted">
        <Icon name="clock" className="animate-spin text-gold" size={14} />
        <span>{t('正在根据四柱地支推演子午流注脏腑经络…')}</span>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="rounded-card border border-rim/60 bg-surface/40 p-4 text-xs text-ink-variant">
        {t('四柱地支气机调和，未见明显六冲或单支偏旺，按各季顺时调养即可。')}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((item, idx) => (
        <div
          key={idx}
          className={`rounded-card border p-4 transition-all ${
            item.type === 'clash'
              ? 'border-wuxing-fire/30 bg-wuxing-fire/[0.04]'
              : 'border-gold/30 bg-gold/[0.04]'
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rim/40 pb-2">
            <span className="font-display text-base font-semibold text-ink">
              {item.label}
            </span>
            <div className="flex items-center gap-2 text-xs">
              <span className="rounded-element bg-surface px-2.5 py-0.5 text-xs text-gold-soft border border-rim/50">
                {t('受累脏腑：')}{item.organs}
              </span>
              <span className="rounded-element bg-surface px-2.5 py-0.5 text-xs text-ink-variant border border-rim/50">
                {item.meridians}
              </span>
            </div>
          </div>
          <p className="mt-2.5 font-body text-sm leading-relaxed text-ink-variant">
            <strong className="text-ink font-medium">{t('气机焦点：')}</strong>
            {item.focus}
          </p>
          <p className="mt-1.5 font-body text-sm leading-relaxed text-gold-bright">
            <strong className="font-medium">{t('养生调护：')}</strong>
            {item.advice}
          </p>
        </div>
      ))}
      <p className="text-xs text-ink-muted">
        {t('* 依据传统经方五行与十二经脉子午流注当令时辰推演，供作起居调摄参考，不作临床医学诊断。')}
      </p>
    </div>
  );
}
