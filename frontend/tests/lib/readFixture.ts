import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

/**
 * 读一份录制自真实 `:8000` 后端的响应夹具（`frontend/tests/fixtures/<name>.json`）。
 *
 * 夹具的唯一生产者是本仓库根部的 `scripts/record_frontend_fixtures.py`；
 * 手写夹具 = 伪造后端输出，一律禁止。返回值刻意是 `unknown`：JSON 的形状
 * 只有调用点的断言（或显式收窄）能证明，这里替它标成任何具体类型都是说谎。
 */
export function readFixture(name: string): unknown {
  const url = new URL(`../fixtures/${name}.json`, import.meta.url);
  return JSON.parse(readFileSync(fileURLToPath(url), 'utf8')) as unknown;
}
