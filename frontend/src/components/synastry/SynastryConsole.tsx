import { useState } from 'react';
import type { FormEvent } from 'react';

import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { ChineseDateField, ChineseTimeField } from '../ui/DateTimeField';
import { LocationField } from '../ui/LocationField';
import type { LocationValue } from '../ui/LocationField';
import { SelectMenu } from '../ui/SelectMenu';
import type { SynastryPerson, SynastryRequest } from '../../types/synastry';

/** House systems the backend engine accepts (Swiss Ephemeris codes). */
const HOUSE_SYSTEM_OPTIONS: ReadonlyArray<{ value: string; label: string }> = [
  { value: 'P', label: '普拉西度 Placidus' },
  { value: 'K', label: '科赫 Koch' },
  { value: 'R', label: '雷吉奥蒙塔努斯 Regiomontanus' },
  { value: 'E', label: '等宫制 Equal' },
  { value: 'W', label: '全星座 Whole Sign' },
];

/** 一台两列共用一份分宫制：合盘的两人必须落在同一套宫位口径上，比较才有意义。 */
interface SideState {
  name: string;
  birthDate: string;
  birthTime: string;
  location: LocationValue;
  utcOffset: string;
}

const EMPTY_SIDE: SideState = {
  name: '',
  birthDate: '',
  birthTime: '',
  location: { city: null, latitude: null, longitude: null },
  utcOffset: '',
};

/** 一造的字段块。`caption` 只作标题与 accessible name，不进计算。 */
function SideColumn({
  caption,
  placeholder,
  state,
  onChange,
}: {
  caption: string;
  placeholder: string;
  state: SideState;
  onChange: (next: Partial<SideState>) => void;
}) {
  return (
    <fieldset className="flex flex-col gap-3 rounded-card border border-rim bg-[#0e111a] p-4">
      <legend className="label-caps px-1 text-gold">{caption}</legend>

      <LabeledField label={`称谓（${caption}，仅回显）`}>
        <input
          value={state.name}
          onChange={(event) => onChange({ name: event.target.value })}
          maxLength={40}
          placeholder={placeholder}
          className="w-full rounded-element border border-rim bg-[#0e111a] px-3 py-2 text-sm text-ink outline-none focus:border-rim-strong"
          aria-label={`${caption}称谓`}
        />
      </LabeledField>

      <LabeledField label="生辰（公历，精准至分）">
        <div className="flex flex-col gap-2">
          <ChineseDateField
            value={state.birthDate}
            onChange={(next) => onChange({ birthDate: next })}
            calendar="solar"
            ariaLabel={caption}
          />
          <ChineseTimeField
            value={state.birthTime}
            onChange={(next) => onChange({ birthTime: next })}
            ariaLabel={caption}
          />
        </div>
      </LabeledField>

      <LabeledField label="出生基准地（全球坐标）">
        <LocationField value={state.location} onChange={(next) => onChange({ location: next })} />
      </LabeledField>

      <LabeledField label="时区 / UTC OFFSET" hint={<span className="text-ink-muted">小时</span>}>
        <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
          <Icon name="clock" size={16} className="shrink-0 text-ink-muted" />
          <input
            type="number"
            min={-14}
            max={14}
            step={0.5}
            value={state.utcOffset}
            onChange={(event) => onChange({ utcOffset: event.target.value })}
            placeholder="自动（按经度）"
            className="numeric w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
            aria-label={`${caption}时区偏移（小时）`}
          />
        </div>
      </LabeledField>
    </fieldset>
  );
}

interface SynastryConsoleProps {
  pending: boolean;
  onSubmit: (request: SynastryRequest) => void;
}

/**
 * 双人合盘输入台（西洋合盘 · PRD 无 mock 铁律）。
 *
 * 一台两列，共用一个 `<form>` 与一份分宫制：合盘没有「只查一人」这种半张盘，所以提交闸门是
 * **两造生辰与经纬度都齐**。与八字合婚台不同的是这里一律公历、不做真太阳时校正，改以每造
 * 一份的 UTC 偏移（留空即按经度推算）——西洋盘的宫头与上升依赖真实经纬度，故纬度同样必填。
 * 状态全在本件里，页面只接一份可直接下发的 {@link SynastryRequest}。
 */
export function SynastryConsole({ pending, onSubmit }: SynastryConsoleProps) {
  const [sideA, setSideA] = useState<SideState>(EMPTY_SIDE);
  const [sideB, setSideB] = useState<SideState>(EMPTY_SIDE);
  const [houseSystem, setHouseSystem] = useState('P');

  const incomplete = (state: SideState): boolean =>
    state.birthDate === '' ||
    state.birthTime === '' ||
    state.location.latitude == null ||
    state.location.longitude == null;

  const missing: string[] = [];
  if (incomplete(sideA)) missing.push('甲方');
  if (incomplete(sideB)) missing.push('乙方');
  const ready = missing.length === 0;

  function personOf(state: SideState): SynastryPerson {
    return {
      birth_date: state.birthDate,
      birth_time: state.birthTime,
      city: state.location.city ?? null,
      latitude: state.location.latitude ?? null,
      longitude: state.location.longitude ?? null,
      utc_offset_hours: state.utcOffset.trim() === '' ? null : Number(state.utcOffset),
      name: state.name.trim() || null,
    };
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!ready || pending) {
      return;
    }
    onSubmit({
      person_a: personOf(sideA),
      person_b: personOf(sideB),
      house_system: houseSystem,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="panel-raised flex flex-col gap-5 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
            <Icon name="compass" size={22} />
          </span>
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-xl font-semibold text-ink sm:text-2xl">
                西洋合盘 · 双人比较盘
              </h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                瑞士星历
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              两张本命盘同屏：人对人相位（合盘）、短弧中点组合盘（Composite）与相契度总分，
              每一条命中都落进可核对的赋分账本。示例：甲 1990-06-15 08:30 × 乙 1992-11-20 18:45 · 格林尼治 (51.4769, -0.0005) · UTC 0。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={!ready || pending}>
          <Icon name="sparkle" size={18} />
          {pending ? '推演中…' : '开始合盘'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <SideColumn
          caption="甲方"
          placeholder="如：先生"
          state={sideA}
          onChange={(next) => setSideA((prev) => ({ ...prev, ...next }))}
        />
        <SideColumn
          caption="乙方"
          placeholder="如：女士"
          state={sideB}
          onChange={(next) => setSideB((prev) => ({ ...prev, ...next }))}
        />
      </div>

      <div className="flex flex-col gap-3 rounded-card border border-rim-soft bg-surface px-4 py-3 sm:flex-row sm:items-end sm:justify-between">
        <LabeledField className="sm:max-w-xs" label="共用分宫制 / HOUSE SYSTEM">
          <SelectMenu
            variant="field"
            value={houseSystem}
            onChange={(next) => setHouseSystem(next)}
            ariaLabel="分宫制"
            options={HOUSE_SYSTEM_OPTIONS}
          />
        </LabeledField>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-ink-muted">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-gold" />
            黄道基准：热带黄道 (Tropical)
          </span>
          <span>时区留空时按各自出生经度推算 UTC 偏移（每 15° ≈ 1 小时）。</span>
        </div>
      </div>

      {!ready ? (
        <p className="label-caps text-ink-muted">
          {missing.join('与')}的公历年月日、时间或经纬度未填齐 —— 合盘需要两张完整的本命盘。
        </p>
      ) : null}
    </form>
  );
}
