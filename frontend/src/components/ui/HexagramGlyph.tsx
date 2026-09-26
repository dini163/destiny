import { LineBar } from './LineBar';

interface HexagramGlyphProps {
  /** Six lines bottom-to-top, 1 = yang, 0 = yin (the backend `lines` array). */
  lines: number[];
  /** Positions (1-6) to mark as moving with ○/×; empty for a static hexagram. */
  moving?: number[];
  /** Tailwind background class for the bars. */
  barClass?: string;
  /** Extra wrapper classes (width). */
  className?: string;
}

/** The six display positions, top (上爻) first, as line indices. */
const TOP_DOWN = [6, 5, 4, 3, 2, 1] as const;

/**
 * A compact six-line hexagram figure, drawn top line (上爻) to bottom (初爻) —
 * the conventional reading orientation. Used for the 变卦 / 互卦 identity cards,
 * which carry structure but no najia dressing.
 *
 * `moving` marks the lines that changed from the primary hexagram so the 变卦
 * figure shows exactly where the transformation landed; markers reuse ○ (old
 * yang) / × (old yin) keyed off the line's resulting polarity.
 */
export function HexagramGlyph({ lines, moving, barClass, className }: HexagramGlyphProps) {
  const movingSet = new Set(moving ?? []);

  return (
    <div className={`flex flex-col gap-1.5 ${className ?? 'w-20'}`} aria-hidden="true">
      {TOP_DOWN.map((position) => {
        const yang = lines[position - 1] === 1;
        const isMoving = movingSet.has(position);
        return (
          <LineBar
            key={position}
            yang={yang}
            barClass={barClass}
            glow={isMoving}
            mark={isMoving ? (yang ? '○' : '×') : null}
          />
        );
      })}
    </div>
  );
}
