import { useState } from 'react';

import { useI18n } from '../i18n/context';
import { ZiweiChartGrid } from '../components/ziwei/ZiweiChartGrid';
import { Icon } from '../components/ui/Icon';
import { InputBar } from '../components/ui/InputBar';
import type { BirthInputValues } from '../components/ui/InputBar';
import { LabeledField } from '../components/ui/LabeledField';
import { PlainSectionList } from '../components/ui/PlainSectionList';
import { ResultCard } from '../components/ui/ResultCard';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { VerdictCard } from '../components/ui/VerdictCard';
import { useZiwei } from '../hooks/useZiwei';
import { useProfileFill } from '../hooks/useProfileFill';
import { GENDER_OPTIONS } from '../lib/gender';
import { calendarLabel, genderLabel } from '../lib/ziwei';
import type { Gender } from '../types/common';
import type { ZiweiChart, ZiweiRequest } from '../types/ziwei';

/**
 * 紫微斗数 chart page (Zi Wei Dou Shu).
 *
 * The console collects birth data; on submit the backend engine fixes the 命宫 /
 * 身宫, derives the 五行局, seats the fourteen 主星 and the 乙级 吉煞 stars into the
 * twelve 地支 palaces, applies the 生年干 四化 and marks every 大限 range. The page
 * renders exactly that board in the classical 4×4 square — nothing interpretive is
 * composed on the client (PRD no-mock rule). 农历 is read directly for 安星, so the
 * calendar toggle matters here more than for 八字.
 */
export function ZiweiPage() {
  const { t } = useI18n();
  const [gender, setGender] = useState<Gender>('male');
  const [applyTrueSolarTime, setApplyTrueSolarTime] = useState(true);
  const [name, setName] = useState('');
  const profile = useProfileFill({
    onPick: (picked) => {
      if (picked?.gender) setGender(picked.gender);
    },
  });
  const ziwei = useZiwei();

  function handleSubmit(values: BirthInputValues): void {
    const request: ZiweiRequest = {
      ...values,
      gender,
      apply_true_solar_time: applyTrueSolarTime,
      name: name.trim() || null,
    };
    ziwei.mutate(request);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <InputBar
        title="紫微斗数命盘"
        badge="权威历算"
        subtitle="以农历生月生时定命身二宫，纳音定五行局，安紫微天府十四主星与左辅右弼、禄马魁钺、羊陀火铃空劫诸曜，起生年四化与大限。示例：1988-02-15 23:30 · 成都 · 乾造（男）。"
        showCalendar
        preset={profile.preset}
        profilePicker={profile.picker}
        onSaveProfile={(values) =>
          profile.openSave({
            gender,
            name: name.trim() || undefined,
            birth_date: values.birth_date,
            birth_time: values.birth_time,
            calendar: values.calendar,
            city: values.city,
            latitude: values.latitude,
            longitude: values.longitude,
          })
        }
        submitLabel={ziwei.isPending ? '排盘中…' : '排定命盘'}
        pending={ziwei.isPending}
        onSubmit={handleSubmit}
      >
        <LabeledField label="造向（性别）">
          <SegmentedControl
            ariaLabel="性别"
            options={GENDER_OPTIONS}
            value={gender}
            onChange={(next) => setGender(next)}
          />
        </LabeledField>
        <LabeledField label="命主称谓（可选，仅回显）">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            maxLength={40}
            placeholder={t('如：示例命主')}
            className="w-full rounded-element border border-rim bg-[var(--field-bg)] px-3 py-2 text-sm text-ink outline-none focus:border-rim-strong"
          />
        </LabeledField>
        <label className="flex cursor-pointer items-center gap-2 text-sm text-ink-variant">
          <input
            type="checkbox"
            checked={applyTrueSolarTime}
            onChange={(event) => setApplyTrueSolarTime(event.target.checked)}
            className="h-4 w-4 accent-[#d4af37]"
          />
          {t('真太阳时校正（推荐）')}
        </label>
      </InputBar>

      {ziwei.error ? (
        <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
          <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
          <span>{ziwei.error.message}</span>
        </div>
      ) : null}

      {ziwei.isPending && !ziwei.data ? (
        <p className="label-caps text-ink-muted">{t('正在安星排盘，布列十二宫垣…')}</p>
      ) : null}

      {ziwei.data ? <ZiweiResults chart={ziwei.data} /> : null}

      {profile.editor}
    </div>
  );
}

/** The full chart composition rendered once a real result is available. */
function ZiweiResults({ chart }: { chart: ZiweiChart }) {
  return (
    <>
      <ChartSummary chart={chart} />

      <VerdictCard verdict={chart.verdict} />

      <ResultCard title="全盘白话" icon="sparkle" elevated>
        <PlainSectionList sections={chart.plain} />
      </ResultCard>

      <ResultCard title="十二宫命盘" icon="vault" elevated>
        <ZiweiChartGrid chart={chart} />
      </ResultCard>

      <ResultCard title="十二宫白话" icon="sparkle" elevated>
        <PlainSectionList
          sections={chart.palaces.map((palace) => ({ title: palace.name, text: palace.plain }))}
        />
      </ResultCard>
    </>
  );
}

/** Headline strip: 命宫 / 五行局 / 命主身主 / 紫微天府落宫 plus the birth facts. */
function ChartSummary({ chart }: { chart: ZiweiChart }) {
  const { t } = useI18n();
  const tst =
    chart.tst_applied && chart.true_solar_time
      ? t('真太阳时 {{tst}}（校正 {{offset}} 分）', {
          tst: chart.true_solar_time,
          offset: chart.tst_offset_minutes?.toFixed(1) ?? '0',
        })
      : t('未校正（标准时直排）');

  return (
    <div className="panel-raised flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          {chart.name ? <span className="text-sm text-ink-variant">{chart.name}</span> : null}
          <span className="label-caps">{t('紫微斗数命盘 · ZI WEI DOU SHU')}</span>
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="font-display text-3xl font-bold tracking-wide text-gold-bright text-glow-gold sm:text-4xl">
              {chart.wuxing_ju}
            </span>
            <span className="font-display text-xl text-ink">
              {t('命宫')} {chart.ming_gong_ganzhi} · {chart.ming_gong_nayin}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Chip label="造向" value={genderLabel(chart.gender)} />
          <Chip label="命主" value={chart.ming_zhu} />
          <Chip label="身主" value={chart.shen_zhu} />
          <Chip label="紫微" value={`${chart.ziwei_zhi}${t('宫')}`} />
          <Chip label="天府" value={`${chart.tianfu_zhi}${t('宫')}`} />
        </div>
      </div>

      <div className="gold-rule" />

      <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-variant">
        <span>
          {t('农历：')}<span className="text-ink">{chart.lunar_date}</span>
          {chart.lunar_leap ? <span className="text-gold-soft">{t('（闰）')}</span> : null}
          <span className="numeric text-ink-muted">
            {' '}
            · {chart.lunar_month}{t('月')}{chart.lunar_day}{t('日')} · {chart.time_zhi}{t('时')}
          </span>
        </span>
        <span>
          {t('身宫：')}<span className="text-ink">{chart.shen_gong_name}（{chart.shen_gong_zhi}）</span>
        </span>
        <span>
          {t('大限：')}<span className="text-ink">{chart.dayun_direction}</span>
          <span className="numeric text-ink-muted"> · {chart.dayun_start_age}{t('岁起运')}</span>
        </span>
        <span>
          {t('标准时：')}<span className="numeric text-ink">{chart.standard_datetime}</span>
        </span>
        <span className="text-gold-soft">{tst}</span>
        <span>
          {t('经度：')}<span className="numeric text-ink">{chart.longitude.toFixed(2)}°</span>
        </span>
        <span>
          {t('历法：')}<span className="text-ink">{calendarLabel(chart.calendar)}</span>
        </span>
      </div>
    </div>
  );
}

/** A compact label/value chip used in the summary header. */
function Chip({ label, value }: { label: string; value: string }) {
  const { t } = useI18n();
  return (
    <span className="flex items-center gap-1.5 rounded-element border border-rim bg-[var(--field-bg)] px-2.5 py-1 text-xs">
      <span className="label-caps">{t(label)}</span>
      <span className="text-ink">{value}</span>
    </span>
  );
}
