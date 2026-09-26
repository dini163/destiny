// @vitest-environment node
/**
 * F-A1-11 的现状钉：引擎回传的 `natal.utc_offset_hours` / `utc_offset_source` 只被本命页
 * **渲染**，行运页、吠陀页与合盘输入台只在**发请求时构造**这两个字段、不回读响应。
 *
 * 事实出处（后端确实换算并回传，不是前端猜的）：`backend/app/engines/western.py:179-184`、
 * `backend/app/schemas/western.py:105-106`。**数据在手、页面不印**——夹具里就带着这两个字段：
 * `tests/fixtures/transit.json` 的 `natal.utc_offset_hours = 0` / `natal.utc_offset_source =
 * "explicit"`，`tests/fixtures/synastry.json` 的 `person_a` 与 `person_b` 各带一份同值（文件内
 * 共 4 处命中）。复测：`cd frontend && node -e "const s=require('./tests/fixtures/synastry.json');console.log(s.person_a.utc_offset_hours, s.person_a.utc_offset_source)"`。
 * 结论：行运/合盘页要加偏移回显不需要任何新数据，响应里已经有了，缺的只是渲染。
 *
 * 前端现状复测（2026-09-27，于 `frontend/` 跑）：
 *   grep -n "utc_offset_hours\|utc_offset_source" src/pages/WesternNatalPage.tsx
 *     → 60（请求构造）/ 188, 190, 247（响应渲染读取）
 *   grep -n "utc_offset_hours\|utc_offset_source" src/pages/TransitPage.tsx
 *     → 67（仅请求构造）
 *   grep -n "utc_offset_hours\|utc_offset_source" src/pages/VedicPage.tsx
 *     → 46（仅请求构造）
 *   grep -rn "utc_offset_hours\|utc_offset_source" src/components/synastry/
 *     → SynastryConsole.tsx:141（仅请求构造）
 *   grep -rn "utc_offset_hours\|utc_offset_source" src/components/transit/
 *     → 0 命中（扫描范围仍已纳入，见下）
 * findings 条目 = F-A1-11（`docs/superpowers/findings/2026-09-26-fullstack-test.md`）。
 *
 * 「读取 vs 构造」的判定口径（刻意不写「出现过就算」，那种断言明年会误报）：
 * - **读取**＝点号属性访问 `\.\s*utc_offset_…`，形如 `chart.utc_offset_hours`——
 *   从响应对象上取值再渲染，是本页把偏移回显给用户的唯一途径。
 * - **构造**＝字面量键形态 `utc_offset_hours:`（可带 `?`），值来自表单 state
 *   （如 `utcOffset === '' ? undefined : Number(utcOffset)`），出现在请求对象里。
 * - 两种形态都不匹配的命中（例如赋值式 `req.utc_offset_hours = …`）按未裁定形态报红，
 *   强制重新思考口径，而不是静默放过。
 * - **注释不参与分类**：判定口径只裁代码——注释既不是读取也不是构造，对它表态等于把
 *   措辞改动误报成行为回归（变异实测 2026-09-27：往 `TransitPage.tsx` 插一行
 *   `// TODO: echo data.natal.utc_offset_source here` 曾让现状钉变红，行为零变化）。
 *   整行 `//`、`/* … *\/` 起、`*` 头（JSDoc 续行）跳过；代码行内的块注释段与 `//`
 *   尾注先剥再判。复测两腿（改完 `classify` 必须都过，之后逐字节还原 `src/`）：
 *   ① 临时在 `src/pages/TransitPage.tsx` 末尾加一行含 `data.natal.utc_offset_source`
 *      的 `//` 注释 → 本测**仍绿**（注释不再是表态对象）；
 *   ② 再加一行真实读取 `const probe = (chart: { utc_offset_source?: string }) => chart?.utc_offset_source;`
 *      → 现状钉**必须红**（read 形态进了扫描面）；两腿后 `git checkout -- src/pages/TransitPage.tsx`。
 *
 * **将来行运页/合盘结果加了偏移回显，本测按新行为重写，不是把它删掉或放宽**——
 * 它是「回显目前缺席」这一现状的证据，现状变了证据就该换形状（AGENTS §8）。
 *
 * 复测口径：
 *   cd frontend && npx vitest run tests/architecture/utc_offset_rendering.test.ts
 */
import { readFileSync, readdirSync } from 'node:fs';
import { resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/** 从本文件定位 `src/`，不用 process.cwd()（同 conventions.test.ts 的理由）。 */
const SRC = fileURLToPath(new URL('../../src/', import.meta.url));

const IDENTIFIERS = ['utc_offset_hours', 'utc_offset_source'];

type Occurrence = { line: number; text: string; kind: 'read' | 'construct' | 'unknown' };

/** 递归列出目录下 .tsx 文件的绝对路径（排序保证报错确定性，同 conventions 口径）。 */
function listTsx(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = resolve(dir, entry.name);
    if (entry.isDirectory()) out.push(...listTsx(p));
    else if (entry.name.endsWith('.tsx')) out.push(p);
  }
  return out.sort();
}

/** 按上面的口径把一个源文件里所有含目标标识符的行分类。 */
function classify(path: string): Occurrence[] {
  const lines = readFileSync(path, 'utf8').split('\n');
  const out: Occurrence[] = [];
  lines.forEach((raw, i) => {
    // 判据口径只裁**代码**：整行注释（//、块注释起首 /*、JSDoc 续行 * 头）先剥掉，
    // 代码行内的 /* … */ 段与 // 尾注也剥——否则一句措辞改动就被误报成回显上线。
    const trimmed = raw.trim();
    if (trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*')) return;
    const text = trimmed.replace(/\/\*.*?\*\//g, '').replace(/\/\/.*$/, '').trim();
    if (!IDENTIFIERS.some((id) => new RegExp(`\\b${id}\\b`).test(text))) return;
    const read = IDENTIFIERS.some((id) => new RegExp(`\\.\\s*\\b${id}\\b`).test(text));
    const construct = IDENTIFIERS.some((id) => new RegExp(`\\b${id}\\b\\s*\\??\\s*:`).test(text));
    out.push({ line: i + 1, text, kind: read ? 'read' : construct ? 'construct' : 'unknown' });
  });
  return out;
}

/** 报错里用相对 `src/` 的 posix 路径，可 grep（同 conventions 口径）。 */
function rel(path: string): string {
  return path.slice(SRC.length).split(sep).join('/');
}

const NATAL_PAGE = resolve(SRC, 'pages/WesternNatalPage.tsx');
/**
 * 判据 ⑥ 的完整扫描面：行运/合盘/吠陀三页 + `components/{synastry,transit}/`。
 * 8B 首版只扫了 `TransitPage.tsx` 与 `components/synastry/`，2026-09-27 修复轮按判据补全：
 * `VedicPage.tsx` 是同类构造形态（:46，`vedic.json` 里也带 2 处偏移字段），`components/transit/`
 * 今天 0 命中（复测见文件头的 grep），列进来是为了「谁将来加回显谁被钉」，不是为钉现状。
 * 两个目录都确实存在，故不写缺失防御——`listTsx` 对不存在的目录裸抛 ENOENT，那正是我们要的报错。
 */
const PIN_SCOPES = [
  resolve(SRC, 'pages/TransitPage.tsx'),
  resolve(SRC, 'pages/VedicPage.tsx'),
  ...listTsx(resolve(SRC, 'components/synastry')),
  ...listTsx(resolve(SRC, 'components/transit')),
];

describe('F-A1-11：utc 偏移回显的现状（本命页渲染，行运/吠陀/合盘只构造）', () => {
  it('正向：本命页对两个标识符都存在响应读取（点号访问），不只是请求构造', () => {
    const occurrences = classify(NATAL_PAGE);
    for (const id of IDENTIFIERS) {
      const reads = occurrences.filter((o) => o.kind === 'read' && o.text.includes(id));
      expect(
        reads.map((o) => `${rel(NATAL_PAGE)}:${o.line}`),
        `WesternNatalPage.tsx 缺少对 ${id} 的响应读取（点号访问形态）`,
      ).not.toHaveLength(0);
    }
  });

  it('现状钉：PIN_SCOPES（行运/吠陀页与 components/{synastry,transit}/**）里两个标识符只有请求构造形态，零渲染读取', () => {
    const offenders: string[] = [];
    for (const file of PIN_SCOPES) {
      for (const o of classify(file)) {
        // read＝回显已出现（现状变了，重写本测）；unknown＝口径外新形态，须先裁定。
        if (o.kind !== 'construct') offenders.push(`${rel(file)}:${o.line} [${o.kind}] ${o.text}`);
      }
    }
    expect(
      offenders,
      `这些行不是请求构造形态：read 说明偏移回显已上线（按新行为重写本测，勿删勿放宽），` +
        `unknown 说明出现了判定口径之外的形态。清单: ${offenders.join(' | ') || '无'}`,
    ).toEqual([]);
  });
});
