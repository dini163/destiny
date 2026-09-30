/**
 * 合盘相位行的白话第二行（多系统白话 spec §10 清单类版式，裁定 R8）。
 *
 * 三条腿：① 夹具里每一行都带非空 `plain`（旧夹具没这个字段，若哪次重录漏了，
 * 页面会安静地渲染出一排空行，所以这条按数据而不是按 DOM 断）；② 渲染出来的第二行
 * 逐字等于后端那句，不做任何截断与拼接；③ 甲方点义在前、乙方点义在后这个方向不许反——
 * 反了的话「你的情绪与安全感，与对方的待人接物的门面」会变成另一段意思，而 DOM 上
 * 看不出差别，所以这一条直接钉整句原文。
 *
 * 两处测法说明（都为了「字段为空时不许绿」）：长度钉一律取 40，而实测语料里最短的一句
 * 是 62 字（复测见下），所以 40 既能挡住 undefined/空串，又留了语料改短前的余量；
 * 整句定位用 `paragraphByExactIn`（全文相等、只在本行容器内找）而不是子串 `toContain`，
 * 因为这份语料里两行可以印出逐字相同的句子，子串查找会配到别处而静默变绿。
 *
 * 复测口径（2026-09-30 实算，同一对生辰；同日 fix 轮 1 文案改写后重取）：
 * 56 行 / 计入 8 行 / 首行 冥王星 六合 天王星 0.05°
 *   cd frontend && npx vitest run tests/components/synastry/SynastryAspectPlain.test.tsx
 * 语料整句长度：720 个全组合 60..80，本盘这 56 行 62..79（Moon△ASC 那句 67 字）。
 * 后两个数按行取，用上面那份重录后的夹具（仓库根，路径按根算）：
 *   PYTHONIOENCODING=utf-8 backend/.venv/Scripts/python.exe -c "import json;d=json.load(open('frontend/tests/fixtures/synastry.json',encoding='utf-8'));a=d['synastry_aspects'];c=[x for x in a if x['counted']];print(min(len(x['plain']) for x in a),max(len(x['plain']) for x in a),len(c[0]['plain']))"
 * 全组合那对数在 backend/ 下取：
 *   cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.synastry import _aspect_plain; from app.engines.plain_corpora import SYNASTRY; pts=[k.split('.')[-1] for k in SYNASTRY.entries if 'synastry.point' in k]; fr=[k.split('.')[-1] for k in SYNASTRY.entries if 'synastry.aspect' in k]; L=[len(_aspect_plain(a,b,f)) for a in pts for b in pts for f in fr]; print(min(L),max(L),len(_aspect_plain('Moon','ASC','trine')))"
 */
import { cleanup, fireEvent, render, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { SynastryAspectList } from '../../../src/components/synastry/SynastryAspectList';
import type { SynastryChart } from '../../../src/types/synastry';
import { paragraphByExactIn } from '../../lib/prose';
import { readFixture } from '../../lib/readFixture';

const synastry = readFixture('synastry') as SynastryChart;
const aspects = synastry.synastry_aspects;

afterEach(cleanup);

describe('SynastryAspectList 的白话第二行（多系统白话 Task 6）', () => {
  it('夹具的每一行都带非空 plain，总论段落数与命中轴数对得上', () => {
    expect(aspects).toHaveLength(56);
    aspects.forEach((aspect) => expect(aspect.plain.length).toBeGreaterThan(40));
    expect(synastry.plain_summary.split('\n')).toHaveLength(4);
  });

  it('计入的第一行：白话整句等于后端原文，甲方点义在前、乙方点义在后', () => {
    const counted = aspects.filter((aspect) => aspect.counted);
    const { container } = render(<SynastryAspectList aspects={counted} />);
    const first = within(container).getAllByRole('listitem')[0];

    // 夹具原文：计入行最紧的一条是 月亮 △ 上升 1.19°。
    expect(counted[0].point_a).toBe('Moon');
    expect(counted[0].point_b).toBe('ASC');
    expect(counted[0].orb).toBe(1.19);
    expect(counted[0].plain.length).toBeGreaterThan(40);
    expect(
      paragraphByExactIn(
        first,
        '你的情绪与安全感，与对方的待人接物的门面相隔一百二十度，气性本属一路，流过去不费力，' +
          '你在这一段上很少遇到阻力，和谐是这一格自己的口径。',
      ),
    ).toBeInTheDocument();
  });

  it('同一张相位表切到「全部」，56 行的白话一行不丢', () => {
    const { container } = render(<SynastryAspectList aspects={aspects} />);
    const items = within(container).getAllByRole('listitem');
    expect(items).toHaveLength(8);
    fireEvent.click(within(container).getByRole('radio', { name: '全部' }));
    const allItems = within(container).getAllByRole('listitem');
    expect(allItems).toHaveLength(56);
    allItems.forEach((item, index) => {
      expect(aspects[index].plain.length).toBeGreaterThan(40);
      expect(paragraphByExactIn(item, aspects[index].plain)).toBeInTheDocument();
    });
  });
});
