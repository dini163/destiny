import { formatDegreeInSign, planetColor } from '../../lib/astro';
import { useI18n } from '../../i18n/context';
import type { NodeInfo, PlanetPlacement } from '../../types/western';

interface PlanetTableProps {
  planets: PlanetPlacement[];
  nodes: NodeInfo;
}

/** A unified ephemeris row: the ten bodies plus the two lunar nodes. */
interface EphemerisRow {
  key: string;
  glyph: string;
  color: string;
  nameZh: string;
  signZh: string;
  sign: string;
  degree: string;
  house: number;
  /** Motion / node status shown in the last column. */
  status: 'direct' | 'retrograde' | 'node';
}

/**
 * Ephemeris table (十大主星与交点).
 *
 * Lists every body's real sign, exact degree, house and retrograde motion, plus
 * the mean lunar nodes. Dignities (庙旺/落陷) are intentionally not shown — the
 * engine does not compute them and inventing them would breach the no-mock rule.
 */
export function PlanetTable({ planets, nodes }: PlanetTableProps) {
  const { t } = useI18n();
  const rows: EphemerisRow[] = [
    ...planets.map((planet) => ({
      key: planet.name,
      glyph: planet.glyph,
      color: planetColor(planet.name),
      nameZh: planet.name_zh,
      signZh: planet.sign_zh,
      sign: planet.sign,
      degree: planet.degree_text,
      house: planet.house,
      status: planet.retrograde ? ('retrograde' as const) : ('direct' as const),
    })),
    {
      key: 'north-node',
      glyph: '☊',
      color: '#e1c46e',
      nameZh: '北交点',
      signZh: nodes.north_node_sign_zh,
      sign: nodes.north_node_sign,
      degree: formatDegreeInSign(nodes.north_node_longitude),
      house: nodes.north_node_house,
      status: 'node',
    },
    {
      key: 'south-node',
      glyph: '☋',
      color: '#99907c',
      nameZh: '南交点',
      signZh: nodes.south_node_sign_zh,
      sign: nodes.south_node_sign,
      degree: formatDegreeInSign(nodes.south_node_longitude),
      house: nodes.south_node_house,
      status: 'node',
    },
  ];

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="label-caps border-b border-rim text-ink-muted">
            <th className="pb-2 font-medium">{t('星体')}</th>
            <th className="pb-2 font-medium">{t('星座落位')}</th>
            <th className="pb-2 font-medium">{t('度数')}</th>
            <th className="pb-2 font-medium">{t('分宫')}</th>
            <th className="pb-2 text-right font-medium">{t('状态')}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-rim-soft">
          {rows.map((row) => (
            <tr key={row.key} className="transition hover:bg-surface-raised/40">
              <td className="py-2">
                <span className="flex items-center gap-1.5 font-medium text-ink">
                  <span className="text-base" style={{ color: row.color }}>
                    {row.glyph}
                  </span>
                  {row.nameZh}
                </span>
              </td>
              <td className="py-2 text-ink">
                {row.signZh}
                <span className="ml-1 text-xs text-ink-muted">{row.sign}</span>
              </td>
              <td className="numeric py-2 text-gold-soft">{row.degree}</td>
              <td className="numeric py-2 text-ink-variant">{t('第 {{house}} 宫', { house: row.house })}</td>
              <td className="py-2 text-right">
                <StatusTag status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Retrograde / direct / node indicator for the status column. */
function StatusTag({ status }: { status: EphemerisRow['status'] }) {
  const { t } = useI18n();
  if (status === 'retrograde') {
    return <span className="text-xs text-wuxing-fire">℞ {t('逆行')}</span>;
  }
  if (status === 'node') {
    return <span className="text-xs text-ink-muted">{t('平交点')}</span>;
  }
  return <span className="text-xs text-ink-muted">{t('顺行')}</span>;
}
