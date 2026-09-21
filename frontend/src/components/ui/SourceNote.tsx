/**
 * One provenance marker, rendered two ways.
 *
 * The no-mock contract needs a *visual* difference between a figure a classic
 * states and a figure our own weighting produced, otherwise a modelled number
 * borrows a book's authority. The test is deliberately structural (does the
 * string name a book at all?) rather than a whitelist of constants: some sources
 * are mixed, e.g. 《渊海子平》…（档位取值见 bazi_strength 模型参数）, and a mixed
 * source must not be downgraded to "本系统".
 */
export function citesBook(source: string): boolean {
  return source.includes('《');
}

export function SourceNote({ source }: { source: string }) {
  if (citesBook(source)) {
    return (
      <span className="text-xs text-ink-muted" title={source}>
        {source}
      </span>
    );
  }
  // 角标只印声明的前半句（如"模型参数""本系统季节纲要"），全文留在 title 里。
  return (
    <span
      className="label-caps rounded-element border border-gold/40 bg-gold/10 px-1.5 py-0.5 text-gold-soft"
      title={source}
    >
      {source.split('（')[0]}
    </span>
  );
}
