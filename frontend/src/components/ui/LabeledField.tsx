import type { ReactNode } from 'react';

interface LabeledFieldProps {
  /** Uppercase telemetry caption rendered above the control. */
  label: string;
  /** The form control (input, select, segmented control…). */
  children: ReactNode;
  /** Optional right-aligned node beside the caption (e.g. a calendar toggle). */
  hint?: ReactNode;
  /** Extra wrapper classes (e.g. grid spans). */
  className?: string;
}

/**
 * A caption + control pair used across the input consoles.
 *
 * Centralises the label styling (`.label-caps`) and the label/control spacing so
 * every field lines up, and lets a field carry a right-aligned hint.
 */
export function LabeledField({ label, children, hint, className }: LabeledFieldProps) {
  return (
    <div className={`flex flex-col gap-1.5 ${className ?? ''}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="label-caps">{label}</span>
        {hint}
      </div>
      {children}
    </div>
  );
}
