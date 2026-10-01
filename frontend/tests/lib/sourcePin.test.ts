/**
 * `pinLiteralOrder` 自身的反向自测（终审 I-1 的机器侧凭据）。
 *
 * 为什么这份测必须存在：`pinLiteralOrder` 收留的是「只钉次序不先钉存在性，锚点被整行删掉
 * 照样绿」这个坑（`String.indexOf` 缺席返回 -1，而 -1 小于任何正数）。一个专治空钉的件如果
 * 自己没被反向验过，它就和它替代掉的那两行裸 `indexOf` 比较一样未经证明。所以第二条刻意
 * 构造「锚点缺席」的输入并要求**必须抛**——这一条挂了，说明公共件退化成空钉。
 * 复测：cd frontend && npx vitest run tests/lib/sourcePin.test.ts
 */
import { describe, expect, it } from 'vitest';

import { pinLiteralOrder } from './sourcePin';

const SRC = '<Board /><Plain /><Provenance />';

describe('pinLiteralOrder', () => {
  it('锚点齐备且升序：不抛（对照组）', () => {
    expect(() => pinLiteralOrder(SRC, ['<Board />', '<Plain />', '<Provenance />'])).not.toThrow();
  });

  it('首锚点缺席：必须抛——这就是「本件不是空钉」的证明', () => {
    // 缺席的锚点必须挑**第一个**，这条才有鉴别力。挖掉存在性循环的 helper 只剩
    // `indexOf` 递增比较：中间或末尾的锚点缺席时它的 `indexOf` 是 -1，正好处在序列
    // 半路、比较照样失败，所以「删中间那段」在真件与空壳上都红——它钉不到存在性那一半。
    // 只有首锚点缺席是分水岭：空壳会算出 `-1 < 0`（永真）而绿，真件必须红。
    const mutated = '<Plain /><Provenance />';
    expect(() => pinLiteralOrder(mutated, ['<Board />', '<Plain />', '<Provenance />'])).toThrow();
  });

  it('锚点齐备但次序反了：必须抛', () => {
    const swapped = '<Provenance /><Plain /><Board />';
    expect(() => pinLiteralOrder(swapped, ['<Board />', '<Plain />', '<Provenance />'])).toThrow();
  });
});
