// @vitest-environment node
/**
 * 轴 2 前端侧的机器不变式：页面不直连 HTTP、组件目录互不泄漏、契约层成对、
 * 页面必有路由、重复逻辑与体量只减不增、重发保果 hook adoption 不回落。
 *
 * 判据文字见仓库根 `AGENTS.md`（第 2 条的前端分工、第 8 条「数字必须带测法」）；本模块用
 * node:fs 直读 `src/**` 源码文本，不 import 被测代码，环境刻意是 node（要真文件系统）。
 * 棘轮而非硬门：已裁定保留的例外写进**身份清单**（附理由与 ledger 行号），断言只保证
 * 「不再变差」；现测为零的规则就是硬门。为什么是身份而不是计数（评审 Minor 5）：
 * `BASELINE = 1` 这种纯计数棘轮允许「修掉这条边、换一条同样非法的边」照样绿，
 * 身份子集判定则任何未登记的新违规（哪怕总数不变）都红。
 * 复测口径（2026-09-26 全绿，10 项）：
 * `cd frontend && npx vitest run tests/architecture/conventions.test.ts`
 */
import { readdirSync, readFileSync } from 'node:fs';
import { relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

/** 从本文件定位 `src/`，不用 process.cwd()：CI 的调用目录不可依赖（同 tests/lib/readFixture.ts）。 */
const SRC = fileURLToPath(new URL('../../src/', import.meta.url));

/**
 * 计数型例外的基线上限；表留空即每条规则都是硬门（`assertNoNewViolations` 缺省基线 0）。
 * 本表原本有两条计数棘轮（`跨系统组件 import` = 1、`formatDelta 重复定义` = 4），
 * 2026-09-26 评审轮把它们换成下面的身份清单：更强（同数量置换也红），且例外本身与
 * ledger 行号同处登记。将来确有「同一身份的违规数只能减」型例外时再回到这张表。
 */
const BASELINE: Record<string, number> = {};

/** 已裁定的跨系统组件 import 边（`components/<A>/ -> components/<B>/`，B≠ui）全仓唯一一处：
 * `components/meihua/HexagramTriad.tsx` 引 `../zhouyi/HexagramGlyph`——卦画字形是梅花与
 * 周易共用的视觉件，暂居 zhouyi 未提升为 ui/，裁定见 ledger F-A2-4。提升后清单清空即硬门。 */
const ADJUDICATED_CROSS_SYSTEM_EDGES = [
  'components/meihua/HexagramTriad.tsx -> ../zhouyi/HexagramGlyph',
];

/** `function formatDelta` 的四处已登记定义（ledger F-A2-5）：前两处逐字复制、后两处签名不同，
 * 合并进 ui/ScoreLedger 或 lib 共用件后逐条从清单划掉（每划掉一条离硬门近一格）。 */
const ADJUDICATED_FORMAT_DELTA_DEFINERS = [
  'components/bazi/hehun/HehunFiredList.tsx',
  'components/bazi/transit/TransitFiredList.tsx',
  'components/ui/ScoreLedger.tsx',
  'lib/meihua.ts',
];

/** 计数棘轮：offenders 数不得超过该 kind 的基线（缺省 0 = 硬门），并把全部违规报出来。 */
function assertNoNewViolations(kind: string, offenders: string[]): void {
  const limit = BASELINE[kind] ?? 0;
  expect(
    offenders.length,
    `${kind} 违规 ${offenders.length} 处，超出基线 ${limit}；清单: ${offenders.join(', ') || '无'}`,
  ).toBeLessThanOrEqual(limit);
}

/** 身份棘轮：offenders 必须全部落在已登记例外里；任何未登记身份（新增或置换）都红。 */
function assertOnlyAdjudicated(kind: string, offenders: string[], adjudicated: string[]): void {
  const unlisted = offenders.filter((o) => !adjudicated.includes(o));
  expect(
    unlisted,
    `${kind} 出现未登记例外 ${unlisted.join(', ') || '无'}；已裁定例外: ${adjudicated.join(', ') || '（无）'}`,
  ).toEqual([]);
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
  // 现测 0（2026-09-26，两条命令都从 `frontend/` 跑）：
  //   grep -rln "apiPost\|apiGet" src/pages  → 0 命中
  //   grep -rln "from '\.\./api"  src/pages  → 0 命中
  // `fetch(` 全仓唯一出现在 `api/client.ts`（fetch 包装器本身，不是漏网调用点）。
  // 不再要求名字紧跟 `(`（评审 Important 1）：本仓真调用一律带泛型参数
  // （`api/bazi.ts:9` 的 `apiPost<BaziChart>('/bazi/natal', request, signal)`），
  // 旧正则 `/\b(apiPost|apiGet|fetch)\s*\(/` 对 `apiPost<BaziChart>(` 零命中，
  // 于是"把 api/bazi.ts 那一行抄进页面"这条最自然的绕过路径是绿的。
  // 页面无条件不许 import `src/api/` 任何东西：接线的唯一去处是 `hooks/`
  // （不变式 7 的重发保果与错误约定都挂在那一层）。
  it('pages/** 不得出现 apiPost/apiGet/fetch(', () => {
    const offenders = listFiles(resolve(SRC, 'pages'), ['ts', 'tsx'])
      .filter((p) => /\b(apiPost|apiGet)\b|\bfetch\s*\(/.test(readFileSync(p, 'utf8')))
      .map(rel);
    assertNoNewViolations('页面直连 HTTP', offenders);
  });

  it('pages/** 不得 import src/api/ 的任何东西', () => {
    const apiDir = resolve(SRC, 'api');
    const offenders = listFiles(resolve(SRC, 'pages'), ['ts', 'tsx'])
      .filter((p) =>
        importSpecs(p).some((spec) => {
          if (!spec.startsWith('.')) return false;
          const target = resolve(p, '..', spec);
          return target === apiDir || target.startsWith(apiDir + sep);
        }),
      )
      .map(rel);
    assertNoNewViolations('页面直连 api 层', offenders);
  });
});

describe('不变式 2：components/<A>/ 不得 import components/<B>/（B≠ui）', () => {
  // 共享 UI 的唯一合法去处是 components/ui/。现测（2026-09-26）1 处：
  // meihua -> zhouyi/HexagramGlyph（ledger F-A2-4），登记为 ADJUDICATED_CROSS_SYSTEM_EDGES
  // 的边身份而非计数：换一条同样数量的边照样红。layout/portal 两个平台目录现测既不
  // 外流也不被引（复测命令按本目录口径 scoping：`cd frontend && grep -rln
  // "components/layout\|components/portal" src/components` = 0 命中；不带 src/components
  // 的仓内全量 grep 会有 3 个命中——router.tsx:3、pages/NotFoundPage.tsx:3、
  // pages/PortalPage.tsx:4-5，那三处不是本不变式的射程），故不为其开后门：哪天引了
  // 就是未登记身份，直接红。
  const topDir = (path: string): string => relative(resolve(SRC, 'components'), path).split(sep)[0];
  const componentsDir = resolve(SRC, 'components');

  it('跨系统组件 import 只能是被裁定的那条边', () => {
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
    assertOnlyAdjudicated('跨系统组件 import', offenders, ADJUDICATED_CROSS_SYSTEM_EDGES);
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

describe('不变式 4：每个 pages/<X>.tsx 必须被 router.tsx 引且渲染（防孤儿页）', () => {
  // 现测 0：21 个页面文件全部既被 import 又渲染（含走 `'*'` 兜底的 NotFoundPage），故硬门。
  // 复测：`cd frontend && grep -c "from './pages" src/router.tsx`（21）对 `ls src/pages | wc -l`（21）。
  // 判定用「import 指称 + 渲染元素」两道（评审 Important 2）：只看去后缀的文件名是否出现在
  // router.tsx 里，会被同名前缀遮蔽——`pages/TransitPage.tsx` 就靠 `BaziTransitPage`
  // （router.tsx:9,51）蒙了过去，删掉它自己的 import 与路由仍是绿的；注释里提一句名字
  // 同样能骗过名字匹配，元素匹配堵的就是这条。
  it('无孤儿页', () => {
    const router = readFileSync(resolve(SRC, 'router.tsx'), 'utf8');
    const offenders = listFiles(resolve(SRC, 'pages'), ['tsx'])
      .map(rel)
      .filter((p) => {
        const name = p.replace(/^pages\//, '').replace(/\.tsx$/, '');
        return (
          !router.includes(`from './pages/${name}'`) || !new RegExp(`<${name}[\\s/>]`).test(router)
        );
      })
      .map((p) => `${p} 未被 router.tsx import 并渲染`);
    assertNoNewViolations('孤儿页', offenders);
  });
});

describe('不变式 5：重复逻辑抽样 formatDelta', () => {
  // 四处已登记身份见 ADJUDICATED_FORMAT_DELTA_DEFINERS；合并进 ui/ScoreLedger 或 lib
  // 共用件后逐条从清单划掉（ledger F-A2-5），新增一处同名定义即未登记身份，直接红。
  it('function formatDelta 只能定义在已登记的四处', () => {
    const offenders = listFiles(SRC, ['ts', 'tsx'])
      .filter((p) => /function\s+formatDelta\b/.test(readFileSync(p, 'utf8')))
      .map(rel);
    assertOnlyAdjudicated('formatDelta 重复定义', offenders, ADJUDICATED_FORMAT_DELTA_DEFINERS);
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
  // 上一次成功结果留在屏上，载体就是这个 hook。
  //
  // 2026-09-26（Task 5 走查）把缺口补平了：原先 7 采用 / 12 个直调 `useMutation`
  // （ledger F-A2-6，紫微页同页重发抹空白即其表现，F-A1-2），12 个已逐个改为
  // `useLastSuccessMutation`，名单随之从 7 项扩到 19 项。一次性抽签三页（tarot /
  // lenormand / zhouyi）跟着采用，依的是 `useRunes` 已立的裁定：留住的是**上一次显示的
  // 结果**，不是重放上一次的抽牌——下一次仍是后端 `secrets` 的新洗牌。
  //
  // 机制两条，各挡一种退化：① 名单（下面）——已采用者偷偷改回去即红；② 裸
  // `useMutation` 禁令（最后一条 it）——新增 hook 绕过这个模式即红，基线 0 是硬门。
  const ADOPTED_BY = [
    'useBaziHehun',
    'useBaziLiuri',
    'useBaziLiushi',
    'useBaziNatal',
    'useBaziTransit',
    'useGematria',
    'useLenormand',
    'useMeihua',
    'useNameAnalysis',
    'useNumerology',
    'useQimen',
    'useRunes',
    'useSynastry',
    'useTarotSpread',
    'useTransit',
    'useVedic',
    'useWesternNatal',
    'useZhouyiCast',
    'useZiwei',
  ];
  const SELF = 'useLastSuccessMutation';

  it('既有采用者一个都不许丢（名单只准加长）', () => {
    const adopters = readdirSync(resolve(SRC, 'hooks'))
      .filter((f) => f.endsWith('.ts') && f !== `${SELF}.ts`)
      .filter((f) => readFileSync(resolve(SRC, 'hooks', f), 'utf8').includes(SELF))
      .map((f) => f.replace(/\.ts$/, ''));
    const dropped = ADOPTED_BY.filter((n) => !adopters.includes(n));
    expect(dropped, `丢掉重发保果模式的 hook: ${dropped.join(', ')}`).toEqual([]);
  });

  it('除包装器外没有 hook 再直调 useMutation', () => {
    // 注意判定形状：`useLastSuccessMutation` 字面上**包含** `useMutation`，所以按子串
    // grep 会全绿假阴；只有 import 语句本身能区分「直调」与「走包装」。
    const DIRECT = /import\s*\{[^}]*\buseMutation\b[^}]*\}\s*from\s*'@tanstack\/react-query'/;
    const offenders = readdirSync(resolve(SRC, 'hooks'))
      .filter((f) => f.endsWith('.ts') && f !== `${SELF}.ts`)
      .filter((f) => DIRECT.test(readFileSync(resolve(SRC, 'hooks', f), 'utf8')))
      .map((f) => f.replace(/\.ts$/, ''));
    expect(offenders, `绕过重发保果模式的 hook: ${offenders.join(', ')}`).toEqual([]);
  });
});
