import type { ReactNode, SVGProps } from 'react';

/**
 * Minimal inline-SVG icon set for the observatory chrome.
 *
 * Stroke-based glyphs drawn on a 24px grid with `currentColor`, so each icon
 * inherits the surrounding text tone. Kept dependency-free (no icon webfont) to
 * keep the bundle self-contained; later phases extend `GLYPHS` as pages need more.
 */
export type IconName =
  | 'history'
  | 'vault'
  | 'compass'
  | 'seal'
  | 'chevronDown'
  | 'arrowRight'
  | 'alert'
  | 'sun'
  | 'pin'
  | 'calendar'
  | 'clock'
  | 'search'
  | 'close'
  | 'check'
  | 'sparkle'
  | 'timeline'
  | 'gauge';

const GLYPHS: Record<IconName, ReactNode> = {
  history: (
    <>
      <path d="M3 12a9 9 0 1 0 2.6-6.4L3 8" />
      <path d="M3 3v5h5" />
      <path d="M12 7.5V12l3 1.8" />
    </>
  ),
  vault: (
    <>
      <path d="M12 3.2l1.9 4.6 4.6 1.9-4.6 1.9L12 16.2l-1.9-4.6L5.5 9.7l4.6-1.9z" />
      <path d="M18.2 14.6l.8 1.9 1.9.8-1.9.8-.8 1.9-.8-1.9-1.9-.8 1.9-.8z" />
    </>
  ),
  compass: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M15.6 8.4l-2.1 5.1-5.1 2.1 2.1-5.1z" />
    </>
  ),
  seal: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="M12 4v16M4 12h16" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  chevronDown: <path d="M6 9.5l6 6 6-6" />,
  arrowRight: (
    <>
      <path d="M4 12h15" />
      <path d="M13 6l6 6-6 6" />
    </>
  ),
  alert: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v5.5" />
      <path d="M12 16.4h.01" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4.2" />
      <path d="M12 2.6v2.4M12 19v2.4M2.6 12H5M19 12h2.4M5.4 5.4l1.7 1.7M16.9 16.9l1.7 1.7M18.6 5.4l-1.7 1.7M7.1 16.9l-1.7 1.7" />
    </>
  ),
  pin: (
    <>
      <path d="M12 21s6.8-5.2 6.8-10.6A6.8 6.8 0 0 0 5.2 10.4C5.2 15.8 12 21 12 21z" />
      <circle cx="12" cy="10.2" r="2.5" />
    </>
  ),
  calendar: (
    <>
      <rect x="3.6" y="5.2" width="16.8" height="15.2" rx="2" />
      <path d="M3.6 10h16.8M8.2 3.4v3.6M15.8 3.4v3.6" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="8.4" />
      <path d="M12 7.2V12l3.2 1.9" />
    </>
  ),
  search: (
    <>
      <circle cx="10.8" cy="10.8" r="6.2" />
      <path d="M15.4 15.4l4.9 4.9" />
    </>
  ),
  close: <path d="M6.4 6.4l11.2 11.2M17.6 6.4L6.4 17.6" />,
  check: <path d="M4.8 12.4l4.8 4.8L19.2 7.2" />,
  sparkle: (
    <>
      <path d="M11 3.5l1.9 5.1 5.1 1.9-5.1 1.9L11 17.5l-1.9-5.1L4 10.5l5.1-1.9z" />
      <path d="M18.2 15.4l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z" />
    </>
  ),
  timeline: (
    <>
      <path d="M3.6 12h16.8" />
      <circle cx="8" cy="12" r="2.2" />
      <circle cx="16" cy="12" r="2.2" />
    </>
  ),
  gauge: (
    <>
      <path d="M4.2 17.5a8.4 8.4 0 1 1 15.6 0" />
      <path d="M12 17.5l3.8-4.8" />
      <circle cx="12" cy="17.5" r="1.3" />
    </>
  ),
};

export interface IconProps extends SVGProps<SVGSVGElement> {
  /** Which glyph to draw. */
  name: IconName;
  /** Rendered size in pixels (square). Defaults to 20. */
  size?: number;
}

/** A single monochrome line icon; spreads extra SVG props (className, etc.). */
export function Icon({ name, size = 20, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {GLYPHS[name]}
    </svg>
  );
}
