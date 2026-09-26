import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/**
 * 读一份录制自真实 `:8000` 后端的响应夹具（`frontend/tests/fixtures/<name>.json`）。
 *
 * 夹具的唯一生产者是本仓库根部的 `scripts/record_frontend_fixtures.py`；
 * 手写夹具 = 伪造后端输出，一律禁止。返回值刻意是 `unknown`：JSON 的形状
 * 只有调用点的断言（或显式收窄）能证明，这里替它标成任何具体类型都是说谎。
 *
 * 定位方式必须是「相对本文件」而不是 `process.cwd()`（同 `tests/architecture/conventions.test.ts:20`）。
 * 陷阱（Task 8B 实录）：`new URL(字面量, import.meta.url)` 会被 Vite 的 import-analysis
 * 插件在转译期改写成静态资源引用，base 换成 dev server 的 origin，于是读文件变成
 * `ENOENT: E:\tests\fixtures\…`。把路径先拼成变量再交给 `new URL`，参数节点不再是
 * 字面量，插件放过，运行时用 Node 原生 `URL` 解析出真正的 `file:` 地址。
 */
export function readFixture(name: string): unknown {
  const specifier = `../fixtures/${name}.json`;
  const url = new URL(specifier, import.meta.url);
  return JSON.parse(readFileSync(fileURLToPath(url), 'utf8')) as unknown;
}
