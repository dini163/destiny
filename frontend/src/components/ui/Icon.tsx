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
  | 'alert';

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
