import { wuxingBg, wuxingText } from '../../lib/wuxing';
import type { BaziPillar, HiddenStemWeight } from '../../types/bazi';

/** Fixed palace captions per pillar position (standard 四柱 terminology). */
const PALACE_CAPTION: Record<string, string> = {
  year: '祖荫宫',
  month: '提纲令',
  day: '本身宫',
  hour: '归宿宫',
};

interface PillarCardProps {
  pillar: BaziPillar;
  /**
   * Ledger rows for this pillar (spec §6.6), carrying the role and weight the
   * strength engine consumed. Empty for callers that never assemble the ledger
   * (流月/合盘), which then fall back to the bare hidden-stem list.
   */
  hidden_stem_rows?: HiddenStemWeight[];
}

/**
 * One of the four pillars (年/月/日/时) as a vertical card.
 *
 * Renders only real engine output: the stem and branch with their ten-gods (十神) and
 * five-element colours, the branch hidden stems (藏干) with their ledger weights when
 * supplied, 纳音, 地势 (十二长生), 旬 and 空亡. The day pillar is promoted as the day
 * master (命主日元).
 */
export function PillarCard({ pillar, hidden_stem_rows }: PillarCardProps) {
  const isDay = pillar.position === 'day';
  const palace = PALACE_CAPTION[pillar.position] ?? '';
  const ledger = hidden_stem_rows ?? [];
  // 账本行只带干名，五行仍取自本柱的 hidden_stem_elements（同一地支的两份视图）。
  const elementOf = (stem: string): string =>
    pillar.hidden_stem_elements[pillar.hidden_stems.indexOf(stem)] ?? '';

  return (
    <div
      className={
        isDay
          ? 'relative flex flex-col gap-3 overflow-hidden rounded-card border border-rim-strong bg-surface-raised p-4 shadow-[var(--shadow-card)]'
          : 'relative flex flex-col gap-3 rounded-card border border-rim bg-surface p-4 transition hover:border-rim-strong'
      }
    >
      {isDay ? <div className="absolute inset-x-0 top-0 h-1 bg-gold" /> : null}

      <div className="flex items-center justify-between gap-2">
        <span className={`label-caps ${isDay ? 'text-gold' : ''}`}>
          {pillar.label} · {palace}
        </span>
        {isDay ? (
          <span className="label-caps rounded-element bg-gold px-1.5 py-0.5 text-[#3c2f00]">
            命主日元
          </span>
        ) : null}
      </div>

      <div className="flex flex-col items-center gap-2 py-1">
        <CharacterRow
          char={pillar.gan}
          element={pillar.gan_element}
          shishen={pillar.shishen_gan}
          emphasize={isDay}
        />
        <CharacterRow char={pillar.zhi} element={pillar.zhi_element} shishen={pillar.shishen_zhi[0]} />
      </div>

      <div className="flex flex-col gap-1 rounded-element bg-[#0e111a] p-2.5">
        <span className="label-caps">地支藏干</span>
        {ledger.length > 0
          ? ledger.map((row) => (
              <div key={row.stem} className="flex items-center justify-between text-xs">
                <span className={wuxingText(elementOf(row.stem))}>
                  {row.stem} <span className="text-ink-muted">{row.role}</span>
                </span>
                <span className="numeric text-ink-muted">
                  {row.ten_god} · {row.weight.toFixed(2)}
                </span>
              </div>
            ))
          : pillar.hidden_stems.map((stem, index) => (
              <div key={`${stem}-${index}`} className="flex items-center justify-between text-xs">
                <span className={wuxingText(pillar.hidden_stem_elements[index] ?? '')}>{stem}</span>
                <span className="text-ink-muted">
                  {pillar.hidden_stem_elements[index]}
                  {pillar.shishen_zhi[index] ? ` · ${pillar.shishen_zhi[index]}` : ''}
                </span>
              </div>
            ))}
      </div>

      <dl className="flex flex-col gap-1 text-xs">
        <MetaRow label="纳音" value={pillar.nayin} accent={isDay} />
        <MetaRow label="地势" value={pillar.di_shi} />
        <MetaRow label="旬" value={pillar.xun} />
        <MetaRow label="空亡" value={pillar.xun_kong} />
      </dl>
    </div>
  );
}

/** A single large ganzhi character with its ten-god tag and five-element dot. */
function CharacterRow({
  char,
  element,
  shishen,
  emphasize,
}: {
  char: string;
  element: string;
  shishen?: string;
  emphasize?: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      {shishen ? (
        <span className="label-caps rounded-element bg-surface px-1.5 py-0.5 text-ink-muted">
          {shishen}
        </span>
      ) : null}
      <span
        className={`font-display text-4xl font-bold leading-none ${
          emphasize ? 'text-gold-bright text-glow-gold' : 'text-ink'
        }`}
      >
        {char}
      </span>
      <span className={`h-2 w-2 rounded-full ${wuxingBg(element)}`} title={`五行：${element}`} />
    </div>
  );
}

/** A caption/value line in the pillar's property list. */
function MetaRow({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <dt className="text-ink-muted">{label}</dt>
      <dd className={accent ? 'text-gold-soft' : 'text-ink-variant'}>{value || '—'}</dd>
    </div>
  );
}
