/**
 * Five-element (五行) presentation helpers shared by the Eastern systems.
 *
 * The backend reports elements as Chinese characters (木火土金水). These maps
 * translate one to Celestial Obsidian colour classes and Latin labels so every
 * chart stays visually consistent. Class strings are written out in full (never
 * concatenated at runtime) so Tailwind's content scanner keeps them in the build.
 */

/** Latin names for the five elements. */
const WUXING_LABEL_EN: Record<string, string> = {
  木: 'Wood',
  火: 'Fire',
  土: 'Earth',
  金: 'Metal',
  水: 'Water',
};

/** Solid fill (bars, indicator dots) per element. */
const WUXING_BG: Record<string, string> = {
  木: 'bg-wuxing-wood',
  火: 'bg-wuxing-fire',
  土: 'bg-wuxing-earth',
  金: 'bg-wuxing-metal',
  水: 'bg-wuxing-water',
};

/** Foreground text colour per element. */
const WUXING_TEXT: Record<string, string> = {
  木: 'text-wuxing-wood',
  火: 'text-wuxing-fire',
  土: 'text-wuxing-earth',
  金: 'text-wuxing-metal',
  水: 'text-wuxing-water',
};

/** Tinted chip (background + text) per element, for 喜用神/忌神 tags. */
const WUXING_CHIP: Record<string, string> = {
  木: 'bg-wuxing-wood/15 text-wuxing-wood',
  火: 'bg-wuxing-fire/15 text-wuxing-fire',
  土: 'bg-wuxing-earth/15 text-wuxing-earth',
  金: 'bg-wuxing-metal/15 text-wuxing-metal',
  水: 'bg-wuxing-water/15 text-wuxing-water',
};

/** Solid fill class for an element, with a neutral fallback. */
export function wuxingBg(element: string): string {
  return WUXING_BG[element] ?? 'bg-ink-muted';
}

/** Foreground text class for an element, with a neutral fallback. */
export function wuxingText(element: string): string {
  return WUXING_TEXT[element] ?? 'text-ink-variant';
}

/** Tinted chip classes for an element, with a neutral fallback. */
export function wuxingChip(element: string): string {
  return WUXING_CHIP[element] ?? 'bg-surface text-ink-variant';
}

/** Latin label for an element, echoing the input when unknown. */
export function wuxingLabelEn(element: string): string {
  return WUXING_LABEL_EN[element] ?? element;
}
