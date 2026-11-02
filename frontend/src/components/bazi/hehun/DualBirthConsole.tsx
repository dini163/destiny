import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';

import { Icon } from '../../ui/Icon';
import { LabeledField } from '../../ui/LabeledField';
import { ChineseDateField, ChineseTimeField } from '../../ui/DateTimeField';
import { LocationField } from '../../ui/LocationField';
import type { LocationValue } from '../../ui/LocationField';
import { SegmentedControl } from '../../ui/SegmentedControl';
import { TrueSolarTimeBadge } from '../../ui/TrueSolarTimeBadge';
import { GENDER_LABEL } from '../../../lib/gender';
import type { CalendarType } from '../../../types/common';
import type { HehunSide } from '../../../types/baziHehun';
import type { HehunSideLink, HehunSides } from '../../../lib/transitLink';

/** 两半都齐才谈得上提交：合婚没有"半张盘"这种东西（spec §9.1）。 */
export type CompleteSides = Record<HehunSide, HehunSideLink>;

const CALENDAR_OPTIONS: ReadonlyArray<{ value: CalendarType; label: string }> = [
  { value: 'solar', label: '公历' },
  { value: 'lunar', label: '农历' },
];

/** 一列的表单状态。与 `HehunSideLink` 同义，只是各字段的形状跟着控件走。 */
export interface SideState {
  name: string;
  birthDate: string;
  birthTime: string;
  calendar: CalendarType;
  location: LocationValue;
  applyTrueSolarTime: boolean;
}

const EMPTY_SIDE: SideState = {
  name: '',
  birthDate: '',
  birthTime: '',
  calendar: 'solar',
  location: { city: null, latitude: null, longitude: null },
  applyTrueSolarTime: true,
};

/** 链接里的一造 → 表单里的一列；没给即空列（预填落点正是这里）。 */
function seedOf(link: HehunSideLink | null): SideState {
  if (!link) {
    return EMPTY_SIDE;
  }
  return {
    name: link.name ?? '',
    birthDate: link.values.birth_date,
    birthTime: link.values.birth_time,
    calendar: link.values.calendar ?? 'solar',
    location: {
      city: link.values.city ?? null,
      latitude: link.values.latitude ?? null,
      longitude: link.values.longitude ?? null,
    },
    applyTrueSolarTime: link.applyTrueSolarTime,
  };
}

interface SideColumnProps {
  side: HehunSide;
  state: SideState;
  onChange: (next: Partial<SideState>) => void;
  /** 提供时在列尾渲染「存入档案」：把这一列当前的输入交给页面持久化。 */
  onSaveProfile?: (() => void) | undefined;
}

/** 一造的字段块。`side` 只作标题与 accessible name —— 造向是键位，不是字段。 */
function SideColumn({ side, state, onChange, onSaveProfile }: SideColumnProps) {
  const caption = side === 'male' ? GENDER_LABEL.male : GENDER_LABEL.female;
  const saveable = state.birthDate !== '' && state.birthTime !== '' && state.location.longitude != null;
  return (
    <fieldset className="flex flex-col gap-3 rounded-card border border-rim bg-[var(--field-bg)] p-4">
      <legend className="label-caps px-1 text-gold">{caption}</legend>

      <LabeledField label={`称谓（${caption}，仅回显）`}>
        <input
          value={state.name}
          onChange={(event) => onChange({ name: event.target.value })}
          maxLength={40}
          placeholder={side === 'male' ? '如：夫' : '如：妻'}
          className="w-full rounded-element border border-rim bg-[var(--field-bg)] px-3 py-2 text-sm text-ink outline-none focus:border-rim-strong"
        />
      </LabeledField>

      <LabeledField
        label="生辰（精准至分）"
        hint={
          <SegmentedControl
            ariaLabel={`${caption}历法`}
            options={CALENDAR_OPTIONS}
            value={state.calendar}
            onChange={(next) => onChange({ calendar: next })}
          />
        }
      >
        <div className="flex flex-col gap-2">
          <ChineseDateField
            value={state.birthDate}
            onChange={(next) => onChange({ birthDate: next })}
            calendar={state.calendar}
            ariaLabel={`${caption}出生`}
          />
          <ChineseTimeField
            value={state.birthTime}
            onChange={(next) => onChange({ birthTime: next })}
            ariaLabel={`${caption}出生`}
          />
        </div>
      </LabeledField>

      <LabeledField label="出生基准地（全球坐标）">
        <LocationField value={state.location} onChange={(next) => onChange({ location: next })} />
      </LabeledField>

      <label className="flex cursor-pointer items-center gap-2 text-sm text-ink-variant">
        <input
          type="checkbox"
          checked={state.applyTrueSolarTime}
          onChange={(event) => onChange({ applyTrueSolarTime: event.target.checked })}
          className="h-4 w-4 accent-[#d4af37]"
        />
        真太阳时校正（各造一份）
      </label>

      <TrueSolarTimeBadge
        date={state.birthDate || null}
        time={state.birthTime || null}
        longitude={state.location.longitude ?? null}
      />

      {onSaveProfile ? (
        <button
          type="button"
          className="btn-ghost"
          disabled={!saveable}
          title={`把这一造的输入存入本地档案（需生辰齐备）`}
          onClick={onSaveProfile}
        >
          <Icon name="vault" size={16} />
          存入档案
        </button>
      ) : null}
    </fieldset>
  );
}

interface DualBirthConsoleProps {
  /** 链接里的两半，任一半可为空（`以此造合婚` 只带来一张盘）。 */
  initial: HehunSides;
  /**
   * 外部档案填充（profile picker）：每造一个 preset，变化时覆盖对应一列。
   * 选档案是显式动作，故每次变化都重写整列；null 不动。
   */
  malePreset?: HehunSideLink | null;
  femalePreset?: HehunSideLink | null;
  /** 提供时两列各渲染「存入档案」；回调解锁的是对应一列的表单状态。 */
  onSaveProfile?: (side: HehunSide, state: SideState) => void;
  pending: boolean;
  onSubmit: (sides: CompleteSides) => void;
}

/**
 * 乾坤两台并置的合婚输入台（PRD §6.1.5、spec §8 的第一段）。
 *
 * 一台一列，共用一个 `<form>`：合婚没有"只查一造"这种一半的请求，所以提交闸门是
 * **两半都齐**，而不是一列一按钮。列内的字段与 `InputBar` 同一套控件、同一套类名，
 * 为的是读者从主命盘页过来时不必重学一遍表单；不同的是校正开关在每一列上 ——
 * `apply_true_solar_time` 各造一份（§5.1），主盘那一个开关管不到别人的盘。
 *
 * 状态在本件里，初值由 `initial` 落一次（`useState` 的初值只在挂载时取一次）：挂载之后这一列就归
 * 用户编辑，链接再变（`send` 自己写回的那两键）都不该把已填的字段抹回去。
 */
export function DualBirthConsole({
  initial,
  malePreset,
  femalePreset,
  onSaveProfile,
  pending,
  onSubmit,
}: DualBirthConsoleProps) {
  const [sides, setSides] = useState<Record<HehunSide, SideState>>({
    male: seedOf(initial.male),
    female: seedOf(initial.female),
  });

  function patch(side: HehunSide, next: Partial<SideState>): void {
    setSides((prev) => ({ ...prev, [side]: { ...prev[side], ...next } }));
  }

  useEffect(() => {
    if (malePreset) patch('male', seedOf(malePreset));
  }, [malePreset]);
  useEffect(() => {
    if (femalePreset) patch('female', seedOf(femalePreset));
  }, [femalePreset]);

  const missing = (['male', 'female'] as const).filter((side) => {
    const state = sides[side];
    return state.birthDate === '' || state.birthTime === '' || state.location.longitude == null;
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (missing.length > 0 || pending) {
      return;
    }
    const linkOf = (side: HehunSide): HehunSideLink => {
      const state = sides[side];
      return {
        values: {
          birth_date: state.birthDate,
          birth_time: state.birthTime,
          calendar: state.calendar,
          city: state.location.city ?? null,
          latitude: state.location.latitude ?? null,
          longitude: state.location.longitude ?? null,
        },
        applyTrueSolarTime: state.applyTrueSolarTime,
        name: state.name.trim() || null,
      };
    };
    onSubmit({ male: linkOf('male'), female: linkOf('female') });
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
                八字合婚 · 双人合盘
              </h1>
              <span className="label-caps rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                权威历算
              </span>
            </div>
            <p className="max-w-2xl text-sm leading-relaxed text-ink-muted">
              两张盘同屏：跨造关系扫描、五行互补、年命纳音、同频演进轴与宜忌，一次推演给全，
              每一条命中都落进可核对的账本。示例：{GENDER_LABEL.male} 1988-02-15 23:30 成都 ×{' '}
              {GENDER_LABEL.female} 1985-07-22 14:30 上海。
            </p>
          </div>
        </div>
        <button type="submit" className="btn-primary shrink-0" disabled={missing.length > 0 || pending}>
          <Icon name="sparkle" size={18} />
          {pending ? '推演中…' : '开始合婚'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <SideColumn
          side="male"
          state={sides.male}
          onChange={(next) => patch('male', next)}
          onSaveProfile={
            onSaveProfile ? () => onSaveProfile('male', sides.male) : undefined
          }
        />
        <SideColumn
          side="female"
          state={sides.female}
          onChange={(next) => patch('female', next)}
          onSaveProfile={
            onSaveProfile ? () => onSaveProfile('female', sides.female) : undefined
          }
        />
      </div>

      {missing.length > 0 ? (
        <p className="label-caps text-ink-muted">
          {missing.map((side) => (side === 'male' ? GENDER_LABEL.male : GENDER_LABEL.female)).join('与')}
          的生辰或定位未填齐 —— 合婚需要两张盘。
        </p>
      ) : null}
    </form>
  );
}
