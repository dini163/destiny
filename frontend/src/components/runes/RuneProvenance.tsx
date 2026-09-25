import { ProvenancePanel } from '../ui/ProvenancePanel';
import type { ProvenanceMeta } from '../ui/ProvenancePanel';
import { ResultCard } from '../ui/ResultCard';
import type { RuneProvenance as RuneProvenanceInfo } from '../../types/runes';

interface RuneProvenanceProps {
  provenance: RuneProvenanceInfo;
}

/**
 * 出处卡（spec §8、plan T7 Step 7）。
 *
 * 卡上每一条都出自响应，前端不补一句自己的话 —— 这张卡的全部用处就是让读者能拿去核对，
 * 一句无从核对的话混进来，整张卡就白印了。
 *
 * **spec §8 点名要印的「Codex Regius GKS 2365 4to」印在 `manuscript_note` 里**，连同 Kylver
 * 石碑、以及设计稿那两条假声明（「EPIGRAPHICAL CALIBRATION VERIFIED」与那串 HASH）为何不印
 * 的取舍一起下发（spec §2.2、§11 偏差 L）。这一条是先补了后端才成立的：语料原先一处都没提到
 * 这部写本，而前端自己造一个出处字符串印上去，正是决策 24 与 `SourceNote` 那套角标纪律要拦的
 * 事 —— 卡上一句无从追溯的话，会把整张卡的信用一起拖下去。故修法是在语料里加
 * `MANUSCRIPT_NOTE`、由 `provenance` 下发，前端一个字也不写。
 *
 * 同一节里的「Unicode 码位锚点」与「`name_meaning` 的构拟标注」也不在这张卡上，而是落在真正
 * 用得到的地方：码位与官方名逐枚印在全典抽屉选中那一枚的宽表里（读者核字形时手边就有），
 * 构拟与否逐枚由 `name_meaning_uncertain` 的角标标出。这张卡只印表级出处，而
 * `tables` 里 `rune_futhark` 那条已经把「字形据 Unicode 标准字符名、符文名词义为原始日耳曼语
 * 构拟」写在限定语里 —— 走 `SourceNote` 的非书名号分支，角标只留前半句自证身份，全文在
 * `title` 里，与全站其它端点同一套行为。
 *
 * `rng_note` 与 `engine_note` 挂在对应 meta 行的 `title` 上而不进 `notes`：`method` 那一段已经
 * 把「Python secrets（OS 熵源 CSPRNG）的 sample() 不放回抽取」与「释义全部取自策展语料、引擎
 * 只做选取与串接、无任何评分与百分比」明写在页面上了，再列两条近逐字重复的短句只是噪音。
 * 决策 19 要的是熵源如实署名，那个署名（`secrets`）是可见的，不藏在悬停里。
 */
export function RuneProvenance({ provenance }: RuneProvenanceProps) {
  const meta: ProvenanceMeta[] = [
    { label: '熵源', value: provenance.rng, title: provenance.rng_note },
    { label: '释义引擎', value: provenance.engine, title: provenance.engine_note },
    { label: '牌组规模', value: `${provenance.deck_size} 枚` },
    { label: '方法标识', value: provenance.badge },
  ];

  return (
    <ResultCard title="出处与口径" eyebrow="PROVENANCE" icon="history">
      <ProvenancePanel
        tables={provenance.tables}
        meta={meta}
        notes={[
          provenance.method,
          provenance.manuscript_note,
          provenance.naming_note,
          provenance.wyrd_note,
        ]}
      />
    </ResultCard>
  );
}
