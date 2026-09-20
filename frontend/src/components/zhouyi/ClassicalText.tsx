import type { HexagramInfo, ZhouyiLine } from '../../types/zhouyi';

interface ClassicalTextProps {
  /** 本卦 — supplies the 卦辞 and 用九/用六. */
  ben: HexagramInfo;
  /** The six dressed lines; each carries its classical 爻辞 of the primary hexagram. */
  lines: ZhouyiLine[];
}

/**
 * The classical canon panel (卦爻辞): the received 《周易》 text for the primary
 * hexagram — its 卦辞, the 用九/用六 line when the hexagram is 乾 or 坤, and all
 * six 爻辞 in reading order (初 → 上), with the moving lines highlighted.
 *
 * Every string is the curated classical text returned by the engine's content
 * module; nothing is paraphrased or generated on the client.
 */
export function ClassicalText({ ben, lines }: ClassicalTextProps) {
  return (
    <div className="flex flex-col gap-5">
      <section className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <span className="label-caps">卦辞 · JUDGMENT</span>
          <span className="gold-rule flex-1" />
        </div>
        <p className="font-display text-lg leading-relaxed text-ink text-glow-gold">{ben.gua_ci}</p>
        {ben.yong_ci ? (
          <p className="font-display text-base leading-relaxed text-gold-soft">
            <span className="label-caps mr-2 align-middle text-ink-muted">
              {ben.number === 1 ? '用九' : '用六'}
            </span>
            {ben.yong_ci}
          </p>
        ) : null}
      </section>

      <section className="flex flex-col gap-2.5">
        <div className="flex items-center gap-2">
          <span className="label-caps">爻辞 · LINE STATEMENTS</span>
          <span className="gold-rule flex-1" />
          <span className="shrink-0 text-[11px] text-ink-muted">动爻高亮</span>
        </div>

        <div className="flex flex-col gap-2">
          {lines.map((line) => (
            <div
              key={line.position}
              className={`rounded-element border px-3 py-2 ${
                line.moving
                  ? 'border-gold/30 bg-gold/10'
                  : 'border-rim-soft bg-[#0e111a]/50'
              }`}
            >
              <div className="mb-1 flex items-center gap-2">
                <span
                  className={`font-display text-sm font-semibold ${line.moving ? 'text-gold-bright' : 'text-ink-variant'}`}
                >
                  {line.yao_name}
                </span>
                <span aria-hidden="true" className="text-xs text-ink-muted">
                  {line.symbol}
                </span>
                {line.moving ? (
                  <span className="rounded bg-wuxing-fire/20 px-1.5 py-0.5 text-[10px] font-bold text-wuxing-fire">
                    动爻
                  </span>
                ) : null}
              </div>
              <p className="font-display text-sm leading-relaxed text-ink-variant">{line.yao_ci}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
