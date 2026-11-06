import { useEffect, useState } from 'react';
import { computeZhouyiYangzhai, type YangzhaiMeaning } from '../../api/zhouyi';
import { useI18n } from '../../i18n/context';
import { Icon } from '../ui/Icon';

interface YangzhaiCardProps {
  hexagramName: string;
}

/**
 * 周易六十四卦 · 阳宅九宫与家庭角色化命取象卡片。
 *
 * 规范化排版：
 * - 标题：font-display text-base font-semibold text-gold-bright
 * - 角色与方位：标准微型标签
 * - 正文解析：font-body text-sm leading-[1.8] text-ink
 */
export function YangzhaiCard({ hexagramName }: YangzhaiCardProps) {
  const { t } = useI18n();
  const [data, setData] = useState<YangzhaiMeaning | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    if (!hexagramName) {
      setData(null);
      return;
    }
    setLoading(true);
    computeZhouyiYangzhai(hexagramName)
      .then((res) => {
        if (active) {
          setData(res.meaning);
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [hexagramName]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-3 text-xs text-ink-muted">
        <Icon name="clock" className="animate-spin text-gold" size={14} />
        <span>{t('正在解析后天八卦阳宅化命方位取象…')}</span>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="flex flex-col gap-3 rounded-card border border-rim/70 bg-surface/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-rim/40 pb-2.5">
        <div className="flex items-center gap-2">
          <Icon name="compass" size={18} className="text-gold" />
          <h4 className="font-display text-base font-semibold text-gold-bright">
            {t('阳宅九宫 · 家庭角色与居所方位化命')}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-element px-2 py-0.5 text-xs font-medium border ${
              data.is_name_position_equal
                ? 'border-wuxing-wood/40 bg-wuxing-wood/10 text-wuxing-wood'
                : 'border-gold/40 bg-gold/10 text-gold-soft'
            }`}
          >
            {data.is_name_position_equal ? t('名位相等 · 本位正卦') : t('居位化命 · 借位成卦')}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
        <div className="rounded-element border border-rim/50 bg-[var(--field-bg)] p-3">
          <span className="label-caps">{t('上卦（人道 / 家庭身份）')}</span>
          <div className="mt-1 font-display text-sm font-semibold text-ink">
            {data.upper_trigram}卦 · {data.person_role}
          </div>
        </div>
        <div className="rounded-element border border-rim/50 bg-[var(--field-bg)] p-3">
          <span className="label-caps">{t('下卦（地道 / 居住方位）')}</span>
          <div className="mt-1 font-display text-sm font-semibold text-ink">
            {data.lower_trigram}宫 · {data.position_direction}
          </div>
        </div>
      </div>

      <p className="font-body text-sm leading-[1.8] text-ink">
        {data.summary}
      </p>

      <p className="border-t border-rim/30 pt-2 text-xs leading-relaxed text-ink-muted">
        {data.principle}
      </p>
    </div>
  );
}
