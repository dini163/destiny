import { SourceNote } from '../ui/SourceNote';
import { currentPinnacle, masterPair, pinnacleAgeLabel } from '../../lib/numerology';
import type { Challenge, Pinnacle } from '../../types/numerology';

interface PinnacleLadderProps {
  pinnacles: readonly Pinnacle[];
  challenges: readonly Challenge[];
}

/**
 * 四顶峰阶梯（含当前段高亮）+ 四挑战并排（spec §6.3、§6.4、§8）。
 *
 * 顶峰与挑战按 `index` 配对，**不按下标**：下标序是契约里的约定，一旦后端换了枚举序，
 * 按下标配会画出一张错位而完整的阶梯 —— 那比空一段难查得多（同 `HehunPairMatrix` 取格的
 * 理由）。配不上的那一段就只印顶峰、挑战位留「无对应挑战」，不静默错位。
 *
 * 当前段的高亮只读后端的 `is_current`（`currentPinnacle` 只是 `find`）：基准日落在哪一段
 * 是后端按 `reference_date` 判的，前端没有"今天"的权威口径。一段都落不到（基准日早于
 * 出生）就不高亮任何一段，并如实说明，而不是硬挑第一段充数。
 *
 * 挑战数**不印 `steps`**，因为后端就没给（决策 3 的例外：挑战链是全系统唯一把主数约简掉的
 * 地方，整条链压进 `expression` 一个字符串）。例外写在算式上，读者不必先记住规则。
 * 挑战值 0 是值域的真实成员而不是缺失，故照样给释义，不印成"无"。
 */
export function PinnacleLadder({ pinnacles, challenges }: PinnacleLadderProps) {
  const current = currentPinnacle(pinnacles);
  const challengeOf = (index: number): Challenge | undefined =>
    challenges.find((item) => item.index === index);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-xs text-ink-muted">
        {current ? (
          <>
            <span className="label-caps text-gold">当前处于 </span>
            {current.label}（{pinnacleAgeLabel(current)}）
          </>
        ) : (
          <>
            <span className="label-caps text-wuxing-fire">无当前段 </span>
            基准日早于出生日，四段阶梯都不含这一天，故不高亮任何一段。
          </>
        )}
      </p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {pinnacles.map((pinnacle) => {
          const challenge = challengeOf(pinnacle.index);
          const pair = masterPair(pinnacle.value, pinnacle.root, pinnacle.is_master);
          return (
            <article
              key={pinnacle.key}
              className={`flex flex-col gap-3 rounded-card border p-3.5 ${
                pinnacle.is_current
                  ? 'border-gold/60 bg-surface-raised shadow-astral-halo'
                  : 'border-rim bg-surface'
              }`}
            >
              <header className="flex items-start justify-between gap-2">
                <div className="flex flex-col gap-0.5">
                  <span
                    className={`label-caps ${pinnacle.is_current ? 'text-gold' : 'text-ink-muted'}`}
                  >
                    {pinnacle.label}
                  </span>
                  <span
                    className={`numeric text-xs ${
                      pinnacle.is_current ? 'font-semibold text-gold-bright' : 'text-ink-variant'
                    }`}
                  >
                    {pinnacleAgeLabel(pinnacle)}
                  </span>
                </div>
                {pinnacle.is_current ? (
                  <span className="label-caps shrink-0 rounded-element bg-gold px-1.5 py-0.5 font-semibold text-[#3c2f00]">
                    当前激活
                  </span>
                ) : null}
              </header>

              <div className="flex flex-col gap-1">
                <div className="flex items-baseline gap-2">
                  <span
                    className={`numeric text-3xl font-semibold leading-none ${
                      pinnacle.is_current ? 'text-gold-bright' : 'text-ink'
                    }`}
                  >
                    {pair?.primary ?? '—'}
                  </span>
                  {pair?.rootSuffix ? (
                    <span className="numeric text-base text-gold">{pair.rootSuffix}</span>
                  ) : null}
                  <span className="label-caps text-ink-muted">
                    {pinnacle.is_master ? '主数顶峰' : '顶峰数'}
                  </span>
                </div>
                <span className="numeric text-[11px] text-ink-muted">{pinnacle.expression}</span>
              </div>

              <p className="text-xs leading-relaxed text-ink-variant">{pinnacle.meaning}</p>

              <div className="mt-auto flex flex-col gap-1 border-t border-rim pt-2">
                {challenge ? (
                  <>
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="label-caps text-ink-muted">{challenge.label}</span>
                      <span className="numeric text-lg font-semibold text-wuxing-fire">
                        {challenge.value}
                      </span>
                    </div>
                    <span className="numeric text-[11px] text-ink-muted">
                      {challenge.expression}
                    </span>
                    <span className="label-caps text-ink-muted">{challenge.duration}</span>
                    <p className="text-[11px] leading-relaxed text-ink-variant">
                      {challenge.meaning}
                    </p>
                    <SourceNote source={challenge.source} />
                  </>
                ) : (
                  <span className="label-caps text-wuxing-fire">无对应挑战（index 配不上）</span>
                )}
              </div>

              <SourceNote source={pinnacle.source} />
            </article>
          );
        })}
      </div>
    </div>
  );
}
