import { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { KeyboardEvent as ReactKeyboardEvent } from 'react';
import { createPortal } from 'react-dom';

import { Icon } from './Icon';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectMenuProps {
  /** Currently selected option value (`''` reads as "unset"). */
  value: string;
  onChange: (value: string) => void;
  options: readonly SelectOption[];
  /** Accessible name — preserves the aria-label the native `<select>` carried. */
  ariaLabel: string;
  /** `'inline'` = compact trigger for the date/time boxes; `'field'` = full-width bordered control. */
  variant?: 'inline' | 'field';
  /** Label shown when `value` matches no option. */
  placeholder?: string;
  disabled?: boolean;
}

const POPUP_MAX_HEIGHT = 288;

interface Coords {
  left: number;
  width: number;
  top?: number;
  bottom?: number;
  up: boolean;
}

/**
 * A theme-rendered replacement for `<select>`.
 *
 * The native `<select>` popup is painted by the OS: against this dark UI it comes up
 * white with light-gray option text (unreadable), and it cannot be recoloured,
 * animated, or scrolled to match Celestial Obsidian. This keeps the trigger as a
 * button but renders the list as a portaled, fixed-position listbox we fully control
 * — obsidian surface, gilded hover, a check on the selected row, a pop-in animation
 * and the slim gold scrollbar — while honouring the select-only combobox contract
 * (`role=combobox` + `aria-activedescendant` over a `role=listbox` popup) and full
 * keyboard operation. The emitted value is the same string the `<select>` produced,
 * so callers and the wire format are unchanged.
 */
export function SelectMenu({
  value,
  onChange,
  options,
  ariaLabel,
  variant = 'inline',
  placeholder = '—',
  disabled = false,
}: SelectMenuProps) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [coords, setCoords] = useState<Coords>({ left: 0, width: 0, up: false });

  const buttonRef = useRef<HTMLButtonElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const listId = useId();

  // Why `activeIndex` last changed. Centring the highlighted row is only correct for
  // keyboard/programmatic moves. If a wheel scroll also re-centred the row that slid
  // under a stationary cursor, the list would chase the pointer and scroll forever, so
  // a pointer-driven change opts out of the auto-centre effect below.
  const activeSourceRef = useRef<'key' | 'pointer'>('key');

  const selectedIndex = useMemo(
    () => options.findIndex((option) => option.value === value),
    [options, value],
  );
  const selected = selectedIndex >= 0 ? options[selectedIndex] : undefined;
  const displayLabel = selected ? selected.label : placeholder;
  const safeActive = options.length === 0 ? 0 : Math.max(0, Math.min(activeIndex, options.length - 1));

  const place = useCallback(() => {
    const button = buttonRef.current;
    if (!button) return;
    const rect = button.getBoundingClientRect();
    const width = variant === 'field' ? rect.width : Math.max(rect.width, 92);
    const spaceBelow = window.innerHeight - rect.bottom;
    const up = spaceBelow < POPUP_MAX_HEIGHT + 16 && rect.top > spaceBelow;
    const maxLeft = Math.max(8, window.innerWidth - width - 8);
    const left = Math.min(Math.max(8, rect.left), maxLeft);
    setCoords(
      up
        ? { left, width, bottom: window.innerHeight - rect.top + 6, up }
        : { left, width, top: rect.bottom + 6, up },
    );
  }, [variant]);

  function openMenu(): void {
    activeSourceRef.current = 'key';
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
    setOpen(true);
  }

  function closeMenu(refocus = true): void {
    setOpen(false);
    if (refocus) buttonRef.current?.focus();
  }

  function moveActive(delta: number): void {
    activeSourceRef.current = 'key';
    setActiveIndex((prev) => Math.max(0, Math.min(options.length - 1, prev + delta)));
  }

  function choose(index: number): void {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    closeMenu();
  }

  function handleToggle(): void {
    if (disabled) return;
    if (open) closeMenu(false);
    else openMenu();
  }

  function handleKeyDown(event: ReactKeyboardEvent<HTMLButtonElement>): void {
    if (disabled) return;
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!open) openMenu();
        else moveActive(1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (!open) openMenu();
        else moveActive(-1);
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (!open) openMenu();
        else choose(safeActive);
        break;
      case 'Escape':
        if (open) {
          event.preventDefault();
          closeMenu();
        }
        break;
      case 'Home':
        if (open) {
          event.preventDefault();
          activeSourceRef.current = 'key';
          setActiveIndex(0);
        }
        break;
      case 'End':
        if (open) {
          event.preventDefault();
          activeSourceRef.current = 'key';
          setActiveIndex(options.length - 1);
        }
        break;
      case 'Tab':
        if (open) closeMenu(false);
        break;
      default:
        break;
    }
  }

  // Keep the popup glued to the trigger: position on open, then follow any scroll/resize.
  useLayoutEffect(() => {
    if (!open) return;
    place();
    // A scroll inside the popup's own list never moves the fixed popup, so ignore it;
    // only page/ancestor scrolls (which do move the trigger) need a reposition.
    function onScroll(event: Event): void {
      const target = event.target;
      if (target instanceof Node && popupRef.current?.contains(target)) return;
      place();
    }
    window.addEventListener('scroll', onScroll, true);
    window.addEventListener('resize', place);
    return () => {
      window.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', place);
    };
  }, [open, place]);

  // Centre the highlighted row when it moves via keyboard/open, never on a pointer
  // hover, or the list would keep scrolling itself under a stationary cursor.
  useLayoutEffect(() => {
    if (!open) return;
    if (activeSourceRef.current === 'pointer') return;
    const list = listRef.current;
    const row = list?.querySelector<HTMLElement>(`[data-index="${safeActive}"]`);
    if (list && row) {
      list.scrollTop = Math.max(0, row.offsetTop - list.clientHeight / 2 + row.clientHeight / 2);
    }
  }, [open, safeActive]);

  // Close on any pointer press outside the trigger and popup.
  useEffect(() => {
    if (!open) return;
    function onPointerDown(event: PointerEvent): void {
      const target = event.target as Node;
      if (buttonRef.current?.contains(target)) return;
      if (popupRef.current?.contains(target)) return;
      setOpen(false);
    }
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, [open]);

  const triggerClass =
    variant === 'field'
      ? `w-full justify-between gap-2 rounded-element border bg-[#0e111a] px-3 py-2 text-sm ${
          open ? 'border-rim-strong' : 'border-rim'
        } focus-visible:border-rim-strong focus-visible:ring-1 focus-visible:ring-gold/40`
      : `min-w-0 gap-0.5 rounded-md bg-transparent px-1 py-1 text-sm ${
          open ? 'bg-gold/10' : 'hover:bg-gold/10'
        } focus-visible:bg-gold/10 focus-visible:ring-1 focus-visible:ring-gold/40`;

  const labelClass =
    variant === 'field'
      ? 'truncate text-ink'
      : `numeric truncate ${value === '' ? 'text-ink-muted' : 'text-ink'}`;

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        aria-label={ariaLabel}
        aria-activedescendant={open ? `${listId}-opt-${safeActive}` : undefined}
        disabled={disabled}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={`flex cursor-pointer items-center outline-none transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${triggerClass}`}
      >
        <span className={labelClass}>{displayLabel}</span>
        <Icon
          name="chevronDown"
          size={variant === 'field' ? 16 : 13}
          className={`shrink-0 text-ink-muted transition-transform duration-150 ${
            open ? 'rotate-180 text-gold-soft' : ''
          }`}
        />
      </button>

      {open
        ? createPortal(
            <div
              ref={popupRef}
              id={listId}
              role="listbox"
              aria-label={ariaLabel}
              className="select-pop fixed z-[9999] overflow-hidden rounded-card border border-rim-strong bg-surface-raised/95 shadow-[var(--shadow-focus)] backdrop-blur-xl"
              style={{
                left: coords.left,
                top: coords.top,
                bottom: coords.bottom,
                width: coords.width,
                transformOrigin: coords.up ? 'bottom' : 'top',
              }}
            >
              <div
                ref={listRef}
                className="overflow-y-auto py-1"
                style={{ maxHeight: POPUP_MAX_HEIGHT }}
              >
                {options.map((option, index) => {
                  const isSelected = index === selectedIndex;
                  const isActive = index === safeActive;
                  return (
                    <div
                      key={option.value}
                      id={`${listId}-opt-${index}`}
                      role="option"
                      aria-selected={isSelected}
                      data-index={index}
                      onMouseEnter={() => {
                        activeSourceRef.current = 'pointer';
                        setActiveIndex(index);
                      }}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => choose(index)}
                      className={`flex cursor-pointer items-center justify-between gap-3 px-3 py-1.5 text-sm transition-colors ${
                        isActive ? 'bg-gold/10' : 'bg-transparent'
                      } ${isSelected ? 'text-gold-bright' : 'text-ink-variant'} ${
                        isActive ? 'text-gold-bright' : ''
                      }`}
                    >
                      <span
                        className={
                          variant === 'inline'
                            ? `numeric ${isSelected ? 'font-semibold' : ''}`
                            : isSelected
                              ? 'font-medium'
                              : ''
                        }
                      >
                        {option.label}
                      </span>
                      {isSelected ? <Icon name="check" size={14} className="shrink-0 text-gold" /> : null}
                    </div>
                  );
                })}
              </div>
            </div>,
            document.body,
          )
        : null}
    </>
  );
}
