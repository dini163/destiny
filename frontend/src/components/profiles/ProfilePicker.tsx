import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import type { PersonProfile } from '../../lib/profiles';
import { Icon } from '../ui/Icon';
import { ROUTES } from '../../nav';

interface ProfilePickerProps {
  /** The saved profiles to offer. */
  profiles: PersonProfile[];
  /** Called with the profile the user chose; null clears the selection. */
  onPick: (profile: PersonProfile | null) => void;
  /** Optional button label, e.g. `选择档案`. */
  label?: string;
}

/** Short birth-data summary shown under the profile label in the menu. */
function summarize(profile: PersonProfile): string {
  const parts: string[] = [];
  if (profile.birth_date) {
    parts.push(profile.calendar === 'lunar' ? `农历 ${profile.birth_date}` : profile.birth_date);
    if (profile.birth_time) parts.push(profile.birth_time);
  }
  if (profile.city) parts.push(profile.city);
  if (parts.length === 0) parts.push('未填生辰');
  return parts.join(' · ');
}

/**
 * Dropdown that fills the host console from a saved profile.
 *
 * One control reused by every birth-data console: pick a person and the page maps
 * the profile onto its own state (birth fields, gender, …). The list is empty-state
 * aware, pointing straight at the profiles page to create the first entry.
 */
export function ProfilePicker({ profiles, onPick, label = '选择档案' }: ProfilePickerProps) {
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onPointerDown(event: MouseEvent): void {
      if (boxRef.current && !boxRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onPointerDown);
    return () => document.removeEventListener('mousedown', onPointerDown);
  }, []);

  return (
    <div ref={boxRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-element border border-rim bg-surface/60 px-3 py-1.5 text-sm text-ink-variant transition hover:border-rim-strong hover:text-ink"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <Icon name="vault" size={16} className="text-gold" />
        {label}
        <Icon name="chevronDown" size={14} className="text-ink-muted" />
      </button>

      {open ? (
        <ul
          role="menu"
          className="absolute left-0 top-full z-30 mt-1 w-72 overflow-hidden rounded-element border border-rim bg-surface-raised/95 py-1 shadow-xl backdrop-blur-xl"
        >
          {profiles.length > 0 ? (
            <>
              {profiles.map((profile) => (
                <li key={profile.id} role="none">
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      onPick(profile);
                      setOpen(false);
                    }}
                    className="flex w-full flex-col gap-0.5 px-3 py-2 text-left transition hover:bg-gold/10"
                  >
                    <span className="text-sm text-ink">
                      {profile.label}
                      {profile.name ? (
                        <span className="ml-1.5 text-ink-muted">{profile.name}</span>
                      ) : null}
                      {profile.gender ? (
                        <span className="ml-1.5 text-xs text-gold-soft">
                          {profile.gender === 'male' ? '男' : '女'}
                        </span>
                      ) : null}
                    </span>
                    <span className="text-xs text-ink-muted">{summarize(profile)}</span>
                  </button>
                </li>
              ))}
              <li role="none">
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    onPick(null);
                    setOpen(false);
                  }}
                  className="w-full px-3 py-2 text-left text-sm text-ink-muted transition hover:bg-gold/10 hover:text-ink"
                >
                  不使用档案（清空）
                </button>
              </li>
              <li role="none" className="border-t border-rim/60">
                <Link
                  to={ROUTES.profiles}
                  onClick={() => setOpen(false)}
                  className="flex w-full items-center gap-1.5 px-3 py-2 text-sm text-gold transition hover:bg-gold/10"
                >
                  <Icon name="arrowRight" size={14} />
                  管理档案
                </Link>
              </li>
            </>
          ) : (
            <li role="none" className="flex flex-col gap-2 px-3 py-3">
              <span className="text-sm text-ink-muted">还没有档案。先去建一个，测算时就能一键填充。</span>
              <Link
                to={ROUTES.profiles}
                onClick={() => setOpen(false)}
                className="flex items-center gap-1.5 text-sm text-gold transition hover:text-gold-bright"
              >
                <Icon name="arrowRight" size={14} />
                去创建档案
              </Link>
            </li>
          )}
        </ul>
      ) : null}
    </div>
  );
}
