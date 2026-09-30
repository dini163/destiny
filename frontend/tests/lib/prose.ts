/**
 * 白话区块测的段落定位件（从 `tests/components/bazi/DimensionGrid.test.tsx` 原样提出）。
 *
 * 提出来的理由是同一条判据要被多个消费者用：spec §10 把「白话在上、专业判语在下」定为
 * 全站阅读顺序，甲组的五格卡、三才条与后续系统的卡片测都同用这两件。两份定义必然漂，
 * 所以住一处。断言口径本身一字未改（`DimensionGrid.test.tsx` 三条断言原样跑绿即为凭据）。
 */

/** 文档序：a 在 b 之前为真。 */
export function precedes(a: Element, b: Element): boolean {
  return (
    a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING
  ) !== 0;
}

/**
 * 段落定位一律取全文相等，不留子串查找那条路：白话段与判语段各自就是一个 `<p>` 的
 * `textContent`，整段比一次就把「渲染的是全文而不是首行」一并钉死；子串版要靠
 * 「前 12 字在夹具里唯一」这条夹具事实才不错位，语料一改就可能配错 `<p>` 而静默变绿。
 * 总论那一条更是只能用全文：`PLAIN_SUMMARY_FRAME` 把 `summary` 原句嵌在白话总论里
 * （实测 `plain_summary.includes(summary)` → true），子串查找会先命中前者的 `<p>`，
 * 于是拿同一个元素和自己比 DOM 序，`compareDocumentPosition` 返回 0，断言必假红。
 * 复测：`cd frontend && node -e "const c=require('./tests/fixtures/bazi-natal.json'); console.log(c.interpretation.plain_summary.includes(c.interpretation.summary))"`
 */
export function paragraphByExact(text: string): Element {
  const el = [...document.querySelectorAll('p')].find((p) => p.textContent === text);
  if (!el) throw new Error(`找不到文本全等的 <p>：${text.slice(0, 20)}`);
  return el;
}

/**
 * 全文相等定位，但只在给定容器内找（同一页里并排多张卡片时用）。
 *
 * 存在的理由是一条实测事实，不是对上一条的放松：同一份响应里两格可以同数理，于是它们的
 * `verdict` 逐字相同——实测 `李/明` 的人格与总格都是数理 15，`verdict` 同为「福寿圆满，
 * 富贵荣誉，涵养雅量，德高望重」（复测：`cd frontend && node -e "const c=require('./tests/fixtures/name.json'); console.log(c.grids.map(g=>[g.key,g.number].join(':')).join(' '))"`）。
 * 全站范围的 `paragraphByExact` 这时会命中**前一张卡**那句，拿早出现的判语和后一张卡的白话
 * 比 DOM 序，`precedes` 必假红。判据没变（仍是全文相等，仍不许子串），变的只是搜索范围：
 * 「这一格的白话排在**这一格**的判语之前」本来就是说一张卡内部的事。
 */
export function paragraphByExactIn(root: Element, text: string): Element {
  const el = [...root.querySelectorAll('p')].find((p) => p.textContent === text);
  if (!el) throw new Error(`容器内找不到文本全等的 <p>：${text.slice(0, 20)}`);
  return el;
}
