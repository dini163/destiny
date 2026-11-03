import { useI18n } from '../../i18n/context';
import type { HouseCusp } from '../../types/western';

/** The four angular houses (1/4/7/10) — a fixed fact, given a gold accent. */
const ANGULAR_HOUSES = new Set([1, 4, 7, 10]);

interface HouseTableProps {
  houses: HouseCusp[];
}

/**
 * House-cusp table (十二宫头).
 *
 * Every cusp's real sign and degree from the selected house system, with the
 * four angular houses accented. House 1 always equals the Ascendant.
 */
export function HouseTable({ houses }: HouseTableProps) {
  const { t } = useI18n();
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
      {houses.map((cusp) => {
        const angular = ANGULAR_HOUSES.has(cusp.house);
        return (
          <div
            key={cusp.house}
            className={
              angular
                ? 'flex flex-col gap-0.5 rounded-element border border-gold/40 bg-gold/5 px-3 py-2'
                : 'flex flex-col gap-0.5 rounded-element border border-rim-soft bg-surface px-3 py-2'
            }
          >
            <span className={angular ? 'label-caps text-gold' : 'label-caps text-ink-muted'}>
              {t('第 {{house}} 宫', { house: cusp.house })}
            </span>
            <span className="text-sm text-ink">
              {cusp.sign_zh}
              <span className="ml-1 text-xs text-ink-muted">{cusp.sign}</span>
            </span>
            <span className="numeric text-xs text-gold-soft">{cusp.degree_text}</span>
          </div>
        );
      })}
    </div>
  );
}
