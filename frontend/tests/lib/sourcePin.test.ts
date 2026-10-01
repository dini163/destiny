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

  it('中间锚点缺席：必须抛——这就是「本件不是空钉」的证明', () => {
    // 把中间那段整块删掉：只钉次序的话 `<Board />`(-1 之前) 与 `<Provenance />` 的
    // indexOf 比较照样升序，空钉会绿；存在性钉必须先红。
    const mutated = '<Board /><Provenance />';
    expect(() => pinLiteralOrder(mutated, ['<Board />', '<Plain />', '<Provenance />'])).toThrow();
  });

  it('锚点齐备但次序反了：必须抛', () => {
    const swapped = '<Provenance /><Plain /><Board />';
    expect(() => pinLiteralOrder(swapped, ['<Board />', '<Plain />', '<Provenance />'])).toThrow();
  });
});
