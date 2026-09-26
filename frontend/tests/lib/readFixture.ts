import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/**
 * 读一份录制自真实 `:8000` 后端的响应夹具（`frontend/tests/fixtures/<name>.json`）。
 *
 * 夹具的唯一生产者是本仓库根部的 `scripts/record_frontend_fixtures.py`；
 * 手写夹具 = 伪造后端输出，一律禁止。返回值刻意是 `unknown`：JSON 的形状
 * 只有调用点的断言（或显式收窄）能证明，这里替它标成任何具体类型都是说谎。
 *
 * 定位方式必须是「相对本文件」而不是 `process.cwd()`（同 `tests/architecture/conventions.test.ts:21`）。
 * 陷阱（Task 8B 实录）：**走客户端资源改写的模块**里 `new URL(字面量, import.meta.url)` 会被
 * Vite 的 import-analysis 插件在转译期改写成静态资源引用，base 换成 dev server 的 origin，
 * 于是读文件变成 `ENOENT: E:\tests\fixtures\…`。把路径先拼成变量再交给 `new URL`，参数节点
 * 不再是字面量，插件放过，运行时用 Node 原生 `URL` 解析出真正的 `file:` 地址。
 *
 * 判据是「该模块是否走客户端资源改写」，**不是**「参数是不是字面量」——组件测默认在 jsdom
 * 环境（`vitest.config.ts` 的 `environment: 'jsdom'`），字面量形式在这里必被改写成 `http:`
 * 资源 URL，所以本函数必须先拼变量；而带 `// @vitest-environment node` 的文件（如
 * `tests/architecture/*.test.ts`）不走这条改写，同样的字面量形式今天安全（`conventions.test.ts:21`
 * 与 `utc_offset_rendering.test.ts` 的 `const SRC = …` 行就是这么写的，复测：
 * `grep -n "new URL(" tests/architecture/*.test.ts`）。这是**现状不是许可**：若哪天架构测改用
 * jsdom，那两处字面量就会红，修法照搬本函数。
 * 复测（控制器 2026-09-27 以临时探针实测，探针已删、不落仓库）：默认 jsdom 下字面量的
 * `href` 以 `http:` 开头，带 node 环境注解的文件下为
 * `file:///E:/workspace/destiny/frontend/tests/fixtures/transit.json`；对照
 * `grep -n "new URL" tests/architecture/conventions.test.ts` → 命中 **:21**（:20 是它上面的注释行）。
 */
export function readFixture(name: string): unknown {
  const specifier = `../fixtures/${name}.json`;
  const url = new URL(specifier, import.meta.url);
  return JSON.parse(readFileSync(fileURLToPath(url), 'utf8')) as unknown;
}
