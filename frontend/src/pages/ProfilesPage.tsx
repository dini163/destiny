import { useState } from 'react';

import { useProfiles } from '../hooks/useProfiles';
import type { PersonProfile } from '../lib/profiles';
import { ProfileEditor } from '../components/profiles/ProfileEditor';
import { Icon } from '../components/ui/Icon';
import { ResultCard } from '../components/ui/ResultCard';

/** Compact birth-data line for a profile card. */
function birthLine(profile: PersonProfile): string {
  const parts: string[] = [];
  if (profile.birth_date) {
    parts.push(`${profile.calendar === 'lunar' ? '农历' : '公历'} ${profile.birth_date} ${profile.birth_time ?? ''}`);
  }
  if (profile.city) {
    parts.push(profile.city);
    if (profile.latitude != null && profile.longitude != null) {
      parts.push(`${profile.latitude.toFixed(2)}°N/${profile.longitude.toFixed(2)}°E`);
    }
  }
  return parts.length > 0 ? parts.join(' · ') : '未填生辰';
}

/**
 * 我的档案 — the local person-profiles manager.
 *
 * Pure client-side CRUD over `useProfiles` (localStorage): create, edit and delete
 * the profiles that every natal console can fill from. No request is ever sent;
 * the privacy seals in the footer state exactly this.
 */
export function ProfilesPage() {
  const { profiles, upsert, remove } = useProfiles();
  const [editing, setEditing] = useState<PersonProfile | null | undefined>(undefined);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <ResultCard
        title="我的档案"
        icon="vault"
        elevated
      >
        <div className="flex flex-col gap-3">
          <p className="max-w-3xl text-sm leading-relaxed text-ink-muted">
            把常用之人的生辰与出生地存成本地档案：八字、紫微、西洋占星等任一测算页点「选择档案」即可一键填充，测算后也可把当前输入一键存入。
            档案只写在你这台设备的浏览器里，不上传服务器，不随账号漫游，可随时编辑或删除。
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <button type="button" className="btn-primary" onClick={() => setEditing(null)}>
              <Icon name="sparkle" size={18} />
              新建档案
            </button>
            <span className="label-caps text-ink-muted">
              {profiles.length} 份档案 · 本机存储
            </span>
          </div>
        </div>
      </ResultCard>

      {profiles.length === 0 ? (
        <div className="panel-raised flex flex-col items-center gap-4 p-10 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-full border border-rim bg-surface text-gold">
            <Icon name="vault" size={28} />
          </span>
          <div className="flex flex-col gap-1">
            <h2 className="font-display text-lg text-ink">还没有档案</h2>
            <p className="max-w-md text-sm leading-relaxed text-ink-muted">
              点击「新建档案」录入第一位家人或朋友，之后在任何测算页都能从「选择档案」一键带入其生辰。
            </p>
          </div>
          <button type="button" className="btn-primary" onClick={() => setEditing(null)}>
            <Icon name="sparkle" size={18} />
            新建第一份档案
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="panel-raised flex flex-col gap-3 p-5 transition hover:border-rim-strong"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 flex-col gap-1">
                  <h2 className="truncate font-display text-lg text-ink">{profile.label}</h2>
                  {profile.name ? (
                    <p className="truncate text-sm text-ink-muted">{profile.name}</p>
                  ) : null}
                </div>
                <span className="label-caps shrink-0 rounded-element bg-gold/15 px-2 py-0.5 text-gold">
                  {profile.gender ? (profile.gender === 'male' ? '男' : '女') : '未填性别'}
                </span>
              </div>

              <p className="min-h-[2.5rem] text-sm leading-relaxed text-ink-muted">
                {birthLine(profile)}
              </p>

              <div className="mt-auto flex items-center justify-between gap-2 border-t border-rim/60 pt-3">
                <span className="label-caps text-ink-muted">
                  更新于 {profile.updated_at.slice(0, 10)}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="btn-ghost rounded-element px-2.5 py-1.5 text-sm"
                    onClick={() => setEditing(profile)}
                  >
                    编辑
                  </button>
                  {confirmingId === profile.id ? (
                    <button
                      type="button"
                      className="rounded-element bg-wuxing-fire/15 px-2.5 py-1.5 text-sm text-wuxing-fire transition hover:bg-wuxing-fire/25"
                      onClick={() => {
                        remove(profile.id);
                        setConfirmingId(null);
                      }}
                    >
                      确认删除
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="btn-ghost rounded-element px-2.5 py-1.5 text-sm text-ink-muted transition hover:text-ink"
                      onClick={() => setConfirmingId(profile.id)}
                    >
                      删除
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {editing !== undefined ? (
        <ProfileEditor
          initial={editing}
          onSave={(draft) => upsert(draft)}
          onClose={() => setEditing(undefined)}
        />
      ) : null}
    </div>
  );
}
