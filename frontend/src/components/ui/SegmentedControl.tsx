import { useI18n } from '../../i18n/context';

interface SegmentedOption<T extends string> {
  value: T;
  label: string;
}

interface SegmentedControlProps<T extends string> {
  /** The selectable segments. */
  options: ReadonlyArray<SegmentedOption<T>>;
  /** Currently selected value. */
  value: T;
  /** Selection handler. */
  onChange: (value: T) => void;
  /** Accessible name for the radio group. */
  ariaLabel: string;
  /** Extra wrapper classes. */
  className?: string;
}

/**
 * A compact segmented toggle (e.g. 公历/农历, 乾造（男）/坤造（女）).
 *
 * Uses real radiogroup semantics for accessibility while presenting the
 * observatory's pill-group styling; the active segment is filled with brass gold.
 * Option labels and the group aria-name flow through `t()` so callers keep
 * authoring them in source Chinese.
 */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
  className,
}: SegmentedControlProps<T>) {
  const { t } = useI18n();
  return (
    <div
      role="radiogroup"
      aria-label={t(ariaLabel)}
      className={`inline-flex shrink-0 rounded-element border border-rim bg-[var(--field-bg)] p-0.5 ${className ?? ''}`}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(option.value)}
            className={
              active
                ? 'whitespace-nowrap rounded-[3px] bg-gradient-to-b from-gold-bright to-gold px-3 py-1.5 text-sm font-semibold text-[var(--on-gold)] transition'
                : 'whitespace-nowrap rounded-[3px] px-3 py-1.5 text-sm text-ink-muted transition hover:text-ink'
            }
          >
            {t(option.label)}
          </button>
        );
      })}
    </div>
  );
}
