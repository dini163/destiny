// @vitest-environment node
/**
 * 轴 2 前端侧的机器不变式：页面不直连 HTTP、组件目录互不泄漏、契约层成对、
 * 页面必有路由、重复逻辑与体量只减不增、重发保果 hook adoption 不回落。
 *
 * 判据文字见仓库根 `AGENTS.md`（第 2 条的前端分工、第 8 条「数字必须带测法」）；本模块用
 * node:fs 直读 `src/**` 源码文本，不 import 被测代码，环境刻意是 node（要真文件系统）。
 * 棘轮而非硬门：已裁定保留的例外写进 BASELINE / 例外清单（附理由与 ledger 行号），
 * 断言只保证「不再变差」；现测为零的规则就是硬门。
 * 复测口径（2026-09-26 全绿）：
 * `cd frontend && npx vitest run tests/architecture/conventions.test.ts`
 */
import { readdirSync, readFileSync } from 'node:fs';
import { relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/** 从本文件定位 `src/`，不用 process.cwd()：CI 的调用目录不可依赖（同 tests/lib/readFixture.ts）。 */
const SRC = fileURLToPath(new URL('../../src/', import.meta.url));

/** 现测（2026-09-26）仍存在的违规数；未登记的 kind 基线为 0（硬门）。 */
const BASELINE: Record<string, number> = {
  // components/<A>/ -> components/<B>/（B≠ui）：唯一一处是
  // `components/meihua/HexagramTriad.tsx` 引 `../zhouyi/HexagramGlyph`——卦画字形
  // 是两系统共用的视觉件，暂居 zhouyi 未提升为 ui/，裁定见 ledger F-A2-4。
  '跨系统组件 import': 1,
  // `function formatDelta` 的重复定义：components/bazi/hehun/HehunFiredList.tsx、
  // components/bazi/transit/TransitFiredList.tsx、components/ui/ScoreLedger.tsx、
  // lib/meihua.ts 各一处，合并留作后续收口点（ledger F-A2-5）。
  'formatDelta 重复定义': 4,
};

/** 棘轮断言：offenders 数不得超过该 kind 的基线，并把全部违规报出来。 */
function assertNoNewViolations(kind: string, offenders: string[]): void {
  const limit = BASELINE[kind] ?? 0;
  expect(
    offenders.length,
    `${kind} 违规 ${offenders.length} 处，超出基线 ${limit}；清单: ${offenders.join(', ') || '无'}`,
  ).toBeLessThanOrEqual(limit);
}

/** 递归列出目录下匹配扩展名的文件（绝对路径，排序保证报错确定性）。 */
function listFiles(dir: string, exts: string[]): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = resolve(dir, entry.name);
    if (entry.isDirectory()) out.push(...listFiles(p, exts));
    else if (exts.some((x) => entry.name.endsWith(`.${x}`))) out.push(p);
  }
  return out.sort();
}

/** 相对 `src/` 的 posix 风格路径，报错里可比对、可 grep。 */
function rel(path: string): string {
  return relative(SRC, path).split(sep).join('/');
}

/** 一个源文件里所有 `from '...'` 的模块指称（含 `import type`，耦合不看关键字）。 */
function importSpecs(path: string): string[] {
  const source = readFileSync(path, 'utf8');
  return [...source.matchAll(/from\s+['"]([^'"]+)['"]/g)].map((m) => m[1]);
}

describe('不变式 1：页面网络必须经 hooks/（AGENTS.md 分层惯例）', () => {
  // 现测 0：`grep -rl "apiPost\|apiGet" pages` 与 pages 内 `fetch(` 均零命中，故硬门。
  // `fetch(` 全仓唯一出现在 `api/client.ts`（fetch 包装器本身，不是漏网调用点）；
  // 页面直连 apiPost/apiGet 会绕开 hooks 层的重发保果与错误约定（不变式 7）。
  it('pages/** 不得直接 apiPost/apiGet/fetch(', () => {
    const offenders = listFiles(resolve(SRC, 'pages'), ['ts', 'tsx'])
      .filter((p) => /\b(apiPost|apiGet|fetch)\s*\(/.test(readFileSync(p, 'utf8')))
      .map(rel);
    assertNoNewViolations('页面直连 HTTP', offenders);
  });
});

describe('不变式 2：components/<A>/ 不得 import components/<B>/', () => {
  // 共享 UI 的唯一合法去处是 components/ui/。现测 1（棘轮，见 BASELINE）：
  // meihua -> zhouyi/HexagramGlyph（ledger F-A2-4）。layout/portal 两个平台目录
  // 现测既不外流也不被引（`grep -rln "components/layout\|components/portal"` 排除
  // 自身后零命中），故不为其开后门——哪天引了就是新增违规。
  const topDir = (path: string): string => relative(resolve(SRC, 'components'), path).split(sep)[0];
  const componentsDir = resolve(SRC, 'components');

  it('跨系统组件 import 不得超过基线', () => {
    const offenders: string[] = [];
    for (const file of listFiles(componentsDir, ['ts', 'tsx'])) {
      for (const spec of importSpecs(file)) {
        if (!spec.startsWith('.')) continue;
        const target = resolve(file, '..', spec);
        if (!target.startsWith(componentsDir + sep)) continue;
        const [from, to] = [topDir(file), topDir(target)];
        if (from !== to && to !== 'ui') offenders.push(`${rel(file)} -> ${spec}`);
      }
    }
    assertNoNewViolations('跨系统组件 import', offenders);
  });
});

describe('不变式 3：types/*.ts 与 api/*.ts 一一对应（契约层不缺件）', () => {
  // 刻意排除的共享件，不是漏网：types 侧 `common.ts`（CalendarType 等跨系统原语）、
  // `scoring.ts`（ScoreLedger 家族共享计分形状）；api 侧 `client.ts`（fetch 包装器）、
  // `meta.ts`（平台级路由 health/城市，AGENTS.md 第 2 条已裁定非测算系统）、
  // `queryClient.ts`（react-query 装配）。除这 5 个外，19 个系统词干现测双向齐全（硬门）。
  const SHARED_TYPE_FILES = ['common', 'scoring'];
  const SHARED_API_FILES = ['client', 'meta', 'queryClient'];
  const stems = (dir: string, shared: string[]): string[] =>
    readdirSync(resolve(SRC, dir))
      .filter((f) => f.endsWith('.ts') && !shared.includes(f.replace(/\.ts$/, '')))
      .map((f) => f.replace(/\.ts$/, ''));

  it('词干双向一一对应', () => {
    const typeStems = new Set(stems('types', SHARED_TYPE_FILES));
    const apiStems = new Set(stems('api', SHARED_API_FILES));
    const missingApi = [...typeStems].filter((s) => !apiStems.has(s)).map((s) => `types/${s}.ts 无 api/${s}.ts`);
    const missingType = [...apiStems].filter((s) => !typeStems.has(s)).map((s) => `api/${s}.ts 无 types/${s}.ts`);
    expect([...missingApi, ...missingType]).toEqual([]);
  });

  it('每个 api/<sys>.ts 必须 import 自己系统的 types/<sys>.ts', () => {
    const offenders = stems('api', SHARED_API_FILES)
      .filter((s) => !importSpecs(resolve(SRC, 'api', `${s}.ts`)).some((spec) => spec.endsWith(`types/${s}`)))
      .map((s) => `api/${s}.ts 未 import types/${s}.ts`);
    assertNoNewViolations('api 契约未引自家 types', offenders);
  });
});

describe('不变式 4：每个 pages/<X>.tsx 必须出现在 router.tsx（防孤儿页）', () => {
  // 现测 0：21 个页面文件全部被 router.tsx import（含走 '*' 兜底的 NotFoundPage），故硬门。
  // 复测：`cd frontend && grep -c "from './pages" src/router.tsx`（21）对 `ls src/pages | wc -l`（21）。
  it('无孤儿页', () => {
    const router = readFileSync(resolve(SRC, 'router.tsx'), 'utf8');
    const offenders = listFiles(resolve(SRC, 'pages'), ['tsx'])
      .map(rel)
      .filter((p) => !router.includes(p.replace(/^pages\//, '').replace(/\.tsx$/, '')))
      .map((p) => `${p} 未被 router.tsx 引用`);
    assertNoNewViolations('孤儿页', offenders);
  });
});

describe('不变式 5：重复逻辑抽样 formatDelta', () => {
  // 基线 4 的四处路径已列在 BASELINE 注释；此数为棘轮上限，合并进
  // ui/ScoreLedger 或 lib 共用件后应逐格调小（ledger F-A2-5）。
  it('function formatDelta 定义处不超过基线', () => {
    const offenders = listFiles(SRC, ['ts', 'tsx'])
      .filter((p) => /function\s+formatDelta\b/.test(readFileSync(p, 'utf8')))
      .map(rel);
    assertNoNewViolations('formatDelta 重复定义', offenders);
  });
});

describe('不变式 6：单文件体量棘轮（wc -l 口径）', () => {
  // 基线取现测最大值（2026-09-26）：pages 是 `src/pages/BaziNatalPage.tsx` 461 行
  // （`wc -l src/pages/BaziNatalPage.tsx`），components 是 `src/components/ui/DateTimeField.tsx`
  // 342 行。只准越用越小；新文件顶破上限时该拆，不该抬基线。
  const lineCount = (path: string): number => {
    const c = readFileSync(path, 'utf8');
    return (c.match(/\n/g) ?? []).length + (c.endsWith('\n') ? 0 : 1);
  };
  const MAX_PAGES_LINES = 461;
  const MAX_COMPONENTS_LINES = 342;

  it('pages/**.tsx 不超 pages 上限', () => {
    const offenders = listFiles(resolve(SRC, 'pages'), ['tsx'])
      .filter((p) => lineCount(p) > MAX_PAGES_LINES)
      .map((p) => `${rel(p)} (${lineCount(p)} 行)`);
    assertNoNewViolations('pages 体量超限', offenders);
  });

  it('components/**.tsx 不超 components 上限', () => {
    const offenders = listFiles(resolve(SRC, 'components'), ['tsx'])
      .filter((p) => lineCount(p) > MAX_COMPONENTS_LINES)
      .map((p) => `${rel(p)} (${lineCount(p)} 行)`);
    assertNoNewViolations('components 体量超限', offenders);
  });
});

describe('不变式 7：重发保果 —— hooks/useLastSuccessMutation adoption 不回落', () => {
  // 项目红线（memory `feedback-retained-result-on-refetch`）：可重发的推演页必须让
  // 上一次成功结果留在屏上，载体就是这个 hook。现测（2026-09-26）：25 个 hook 文件里
  // 7 个采用（`grep -rl useLastSuccessMutation hooks | grep -v useLastSuccessMutation.ts | wc -l`），
  // 另外 12 个直调 useMutation 的 hook 未采用（其页面同样可重发）——缺口记在
  // ledger F-A2-6，本测试钉住「已采用的 7 个不许掉、总数不许跌」，只准增不准减。
  const ADOPTED_BY = [
    'useBaziHehun',
    'useBaziLiuri',
    'useBaziLiushi',
    'useBaziTransit',
    'useNumerology',
    'useRunes',
    'useSynastry',
  ];
  const SELF = 'useLastSuccessMutation';

  it('既有采用者不得丢失，adoption 数不低于 7', () => {
    const adopters = readdirSync(resolve(SRC, 'hooks'))
      .filter((f) => f.endsWith('.ts') && f !== `${SELF}.ts`)
      .filter((f) => readFileSync(resolve(SRC, 'hooks', f), 'utf8').includes(SELF))
      .map((f) => f.replace(/\.ts$/, ''));
    const dropped = ADOPTED_BY.filter((n) => !adopters.includes(n));
    expect(dropped, `丢掉重发保果模式的 hook: ${dropped.join(', ')}`).toEqual([]);
    expect(adopters.length).toBeGreaterThanOrEqual(ADOPTED_BY.length);
  });
});
