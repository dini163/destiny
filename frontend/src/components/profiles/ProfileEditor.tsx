import { useState } from 'react';
import type { FormEvent } from 'react';

import type { CalendarType, Gender } from '../../types/common';
import type { ProfileDraft } from '../../lib/profiles';
import { ChineseDateField, ChineseTimeField } from '../ui/DateTimeField';
import { Icon } from '../ui/Icon';
import { LabeledField } from '../ui/LabeledField';
import { LocationField, type LocationValue } from '../ui/LocationField';
import { SegmentedControl } from '../ui/SegmentedControl';

const CALENDAR_OPTIONS: ReadonlyArray<{ value: CalendarType; label: string }> = [
  { value: 'solar', label: '公历' },
  { value: 'lunar', label: '农历' },
];

const GENDER_OPTIONS: ReadonlyArray<{ value: Gender; label: string }> = [
  { value: 'male', label: '男' },
  { value: 'female', label: '女' },
];

interface ProfileEditorProps {
  /**
   * The profile being edited, or a partial prefill for a brand-new one (e.g. the
   * birth fields captured by a 存入档案 button), or null for a blank form.
   */
  initial?: ProfileDraft | null;
  /** Persist the draft (the caller runs the store `upsert`). */
  onSave: (draft: ProfileDraft) => void;
  /** Dismiss the editor. */
  onClose: () => void;
}

/**
 * Create/edit dialog for a person profile.
 *
 * Lives in the same dialog whatever the entry point — the profiles page and every
 * "存入档案" button on a natal console — so a save always goes through the same
 * form. Birth/coordinate fields mirror the `InputBar` contract, and a profile may
 * be partial (e.g. a name without a birth date, for the name consoles).
 */
export function ProfileEditor({ initial, onSave, onClose }: ProfileEditorProps) {
  const editing = Boolean(initial?.id);
  const [label, setLabel] = useState(initial?.label ?? '');
  const [name, setName] = useState(initial?.name ?? '');
  const [surname, setSurname] = useState(initial?.surname ?? '');
  const [given, setGiven] = useState(initial?.given ?? '');
  const [gender, setGender] = useState<Gender>(initial?.gender ?? 'male');
  const [calendar, setCalendar] = useState<CalendarType>(initial?.calendar ?? 'solar');
  const [birthDate, setBirthDate] = useState(initial?.birth_date ?? '');
  const [birthTime, setBirthTime] = useState(initial?.birth_time ?? '');
  const [location, setLocation] = useState<LocationValue>({
    city: initial?.city ?? null,
    latitude: initial?.latitude ?? null,
    longitude: initial?.longitude ?? null,
  });

  const labelOk = label.trim() !== '';

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    if (!labelOk) return;
    onSave({
      ...(initial?.id ? { id: initial.id } : {}),
      label: label.trim(),
      name: name.trim() || undefined,
      surname: surname.trim() || undefined,
      given: given.trim() || undefined,
      gender,
      calendar,
      birth_date: birthDate,
      birth_time: birthTime,
      city: location.city ?? null,
      latitude: location.latitude ?? null,
      longitude: location.longitude ?? null,
    });
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={editing ? '编辑档案' : '新建档案'}
    >
      <button
        type="button"
        aria-label="关闭"
        className="absolute inset-0 cursor-default bg-void/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <form
        onSubmit={handleSubmit}
        className="panel-raised relative flex max-h-[90vh] w-full max-w-lg flex-col gap-5 overflow-y-auto p-5 sm:p-6"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-rim bg-surface text-gold">
              <Icon name="vault" size={22} />
            </span>
            <div className="flex flex-col gap-1">
              <h2 className="font-display text-xl font-semibold text-ink">
                {editing ? '编辑档案' : '新建档案'}
              </h2>
              <p className="text-sm text-ink-muted">
                仅保存在本机浏览器，不上传服务器，可随时编辑或删除。
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="关闭"
            className="shrink-0 rounded-element border border-rim bg-surface/60 p-1.5 text-ink-muted transition hover:text-ink"
          >
            <Icon name="close" size={16} />
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <LabeledField label="档案名（必填）" hint="如 我自己 / 父亲 / 长子">
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <input
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                placeholder="给自己起个称呼"
                aria-label="档案名"
              />
            </div>
          </LabeledField>
          <LabeledField label="姓名" hint="供姓名学 / 毕氏灵数使用">
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <input
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="如 陆青玄"
                aria-label="姓名"
              />
            </div>
          </LabeledField>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <LabeledField label="姓氏（供姓名学拆分）">
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <input
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                value={surname}
                onChange={(event) => setSurname(event.target.value)}
                placeholder="如 陸"
                aria-label="姓氏"
              />
            </div>
          </LabeledField>
          <LabeledField label="名字">
            <div className="flex items-center gap-2 rounded-element border border-rim bg-[#0e111a] px-3 py-2 transition focus-within:border-rim-strong">
              <input
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted"
                value={given}
                onChange={(event) => setGiven(event.target.value)}
                placeholder="如 青玄"
                aria-label="名字"
              />
            </div>
          </LabeledField>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <LabeledField label="性别">
            <SegmentedControl
              ariaLabel="性别"
              options={GENDER_OPTIONS}
              value={gender}
              onChange={setGender}
            />
          </LabeledField>
          <LabeledField label="历法">
            <SegmentedControl
              ariaLabel="历法"
              options={CALENDAR_OPTIONS}
              value={calendar}
              onChange={setCalendar}
            />
          </LabeledField>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <LabeledField label="出生日期">
            <ChineseDateField value={birthDate} onChange={setBirthDate} calendar={calendar} />
          </LabeledField>
          <LabeledField label="出生时间">
            <ChineseTimeField value={birthTime} onChange={setBirthTime} />
          </LabeledField>
        </div>

        <LabeledField label="出生地（全球坐标）">
          <LocationField value={location} onChange={setLocation} />
        </LabeledField>

        <div className="flex items-center justify-end gap-3">
          <button type="button" onClick={onClose} className="btn-ghost">
            取消
          </button>
          <button type="submit" className="btn-primary" disabled={!labelOk}>
            <Icon name="check" size={18} />
            {editing ? '保存修改' : '存入档案'}
          </button>
        </div>
      </form>
    </div>
  );
}
