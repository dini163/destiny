/**
 * `src/lib/numerology.ts` 的被跳过字符写法：`skippedCharLabel`（单个字符）与
 * `skippedCharsLabel`（一整串，顿号分隔）。
 *
 * 为什么值得钉：`ab00175`（`fix(frontend): name the skipped characters that render as
 * blank`）修的正是这一处，而那两个函数今天零覆盖 —— 修过的 bug 没有任何东西挡回归。
 * 本条加入前 `tests/lib/` 只有 astro / transit / smoke 三个 `*.test.ts`（复测：
 * `git ls-tree --name-only HEAD~1 frontend/tests/lib/`，另有一个 `readFixture.ts` 助手）。
 * 回归的形状很具体：`LetterMapTable.tsx:70` 把去重后的被跳过字符拼进
 * `· 跳过 N 个非字母字符（…）`，而括号里的东西经常**正是**看不见的那几个：后端如实报的
 * 是分隔符与控制符（`backend/tests/test_numerology.py:238` 那组参数里 `LU QINGXUAN`
 * 跳过的就是中间一个空格）。直接印原字符，页面上就是一对空括号，看着像渲染坏了 ——
 * 而这一格恰恰是「为何字母数比字符数少」的唯一凭据，印成空白等于把凭据收了回去。
 *
 * 分隔符也不能是空格：`['-', ' '].join(' ')` 分不清谁是谁，故 `skippedCharsLabel` 用顿号。
 *
 * `skippedCharLabel` 里 `code === undefined` 那一支不写用例：走到那里的前提是
 * `NO_GLYPH.test(char)` 为真，而它要求恰好一个码点，`codePointAt(0)` 对这样的串永不返回
 * `undefined` —— 为不可达分支造一个断言只能靠 mock 或改码，两者都不做。
 *
 * 入参说明：`' '`、`'\n'` 这些是函数自己的字符入参，不是伪造的后端响应（AGENTS §9 的
 * 先例是 `tests/lib/smoke.test.ts` 直接写 `HehunSides` 字面量）；最后一条另取真实夹具
 * `tests/fixtures/numerology.json` 的 `input.skipped_chars`，把口径钉在录下来的那份响应上。
 *
 * 复测口径（2026-09-27 全绿，5 项）：
 *   cd frontend && npx vitest run tests/lib/numerology.test.ts
 * 夹具那三个值（改一次就要重跑一次）：
 *   cd frontend && node -e "const j=require('./tests/fixtures/numerology.json');console.log(JSON.stringify(j.input.full_name),j.input.skipped_count,JSON.stringify(j.input.skipped_chars))"
 */
import { describe, expect, it } from 'vitest';

import { skippedCharLabel, skippedCharsLabel } from '../../src/lib/numerology';
import type { NumerologyChart } from '../../src/types/numerology';
import { readFixture } from './readFixture';

describe('看不见的字符要改印码位（Task 10 判据 4 · ab00175 回归）', () => {
  it('四类不可见字符各印一个码位：分隔符 Zs、格式符 Cf、控制符 Cc', () => {
    // 半角空格就是主角名里被跳过的那一个；后三个是同名不同形的陷阱。
    expect(skippedCharLabel(' ')).toBe('空白 U+0020');
    expect(skippedCharLabel('\u00a0')).toBe('空白 U+00A0');
    expect(skippedCharLabel('\u200b')).toBe('空白 U+200B');
    expect(skippedCharLabel('\n')).toBe('空白 U+000A');
  });

  it('码位写成大写、至少四位：U+000A 既不塌成 U+0A 也不写成小写', () => {
    // `padStart(4, '0')` 与 `toUpperCase()` 各管一半，缺一半页面上就是另一种难看写法。
    expect(skippedCharLabel('\n')).toMatch(/^空白 U\+[0-9A-F]{4}$/);
    expect(skippedCharLabel('\u200b')).toMatch(/^空白 U\+[0-9A-F]{4}$/);
    expect(skippedCharLabel('\n')).not.toBe('空白 U+0A');
    expect(skippedCharLabel(' ')).not.toBe('空白 u+0020');
  });

  it('看得见的一律原样，一个码位都不加', () => {
    // 连字符是姓名里最常见的分隔符：给它加码位等于把括号写成读不懂的样子。
    expect(skippedCharLabel('-')).toBe('-');
    expect(skippedCharLabel("'")).toBe("'");
    // 空串没有码点可印，`NO_GLYPH` 也要求恰好一个字符，故原样返回。
    expect(skippedCharLabel('')).toBe('');
  });
});

describe('整串的被跳过字符', () => {
  it('顿号分隔，不是空格：混合「看得见 + 看不见」两项时仍分得清谁是谁', () => {
    // 空格 + 连字符不是臆造的形状：`backend/tests/test_numerology.py:239` 的
    // `Jean-Luc Picard` 去重后正好报回 `(" ", "-")`，:238 的 `LU QINGXUAN` 报回 `(" ",)`。
    expect(skippedCharsLabel([' ', '-'])).toBe('空白 U+0020、-');
    expect(skippedCharsLabel([])).toBe('');
  });

  it('真实夹具那一份（Liam Alexander Carter，跳过 2 个字符、去重后是一个空格）印出来不含空白括号', () => {
    const input = (readFixture('numerology') as NumerologyChart).input;
    expect(input.full_name).toBe('Liam Alexander Carter');
    expect(input.skipped_count).toBe(2);
    expect(input.skipped_chars).toEqual([' ']);
    const label = skippedCharsLabel(input.skipped_chars);
    expect(label).toBe('空白 U+0020');
    // 这一行才是 ab00175 的性质本身：括号里的文本自己不能是空白。
    expect(label.trim()).not.toBe('');
  });
});
