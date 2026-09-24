import { TransitErrorNote } from '../components/bazi/transit/TransitErrorNote';
import { CoreNumberCard } from '../components/numerology/CoreNumberCard';
import { CoreNumberHero } from '../components/numerology/CoreNumberHero';
import { LetterMapTable } from '../components/numerology/LetterMapTable';
import { LoshuGridPanel } from '../components/numerology/LoshuGridPanel';
import { NameGridPanel } from '../components/numerology/NameGridPanel';
import { NumerologyConsole } from '../components/numerology/NumerologyConsole';
import { PersonalCyclePanel } from '../components/numerology/PersonalCyclePanel';
import { PinnacleLadder } from '../components/numerology/PinnacleLadder';
import { Icon } from '../components/ui/Icon';
import { ProvenancePanel } from '../components/ui/ProvenancePanel';
import { ResultCard } from '../components/ui/ResultCard';
import { SourceNote } from '../components/ui/SourceNote';
import { useNumerology } from '../hooks/useNumerology';
import type { KarmicDebt, NumerologyChart } from '../types/numerology';

/**
 * 数字命理入参里唯一会变成 `context` 键的那一个。
 *
 * `numerology_no_latin_letters` 的 `context` 有两键：`field` 与 `chars`。`chars` 是数组，
 * `TransitErrorNote` 只摆数值与非空字符串（其余类型"留给文案自己说"，那条注释正是为这种
 * 形状写的），而这里也确实不必摆 —— 后端原句已经把整个名字印在引号里了
 * （「陆青玄」里没有可计算的拉丁字母…），再排一行同样的字符只是重复。
 */
const CONTEXT_LABEL: Record<string, string> = { field: '出错字段' };

/**
 * 毕达哥拉斯数字命理页（PRD §6.9，设计稿 数字命理全景矩阵，spec 2026-09-24）。
 *
 * 结果卡顺序照设计稿：核心数仪表盘 → 两张九宫 → 顶峰/挑战阶梯 → 个人周期 → 字母映射表
 * → 溯源。设计稿右上那四个按钮一个都不渲染（spec §4.2）：存档属 Stage 9、导出 PDF 与
 * 合参比对属 Stage 10，而"重新测算"就是重新提交上面那张表单 —— 放一个假按钮或一个
 * 「即将上线」的占位，都是在页面上写一句系统兑现不了的话。
 *
 * 两个页内局部组件（{@link ChartSummary} / {@link KarmicDebtStrip}）刻意不升成
 * `components/numerology/` 下的第十、第十一个文件：spec §8 点名的是九个组件，多出的文件
 * 会让那份清单与代码对不上；而这两块各只渲染一次、且都紧贴着自己所属的那张卡，
 * 先例是 `NamePage` 的 `NameSummary`。
 */
export function NumerologyPage() {
  const chart = useNumerology();

  return (
    <div className="mx-auto flex w-full max-w-[1536px] flex-col gap-6 px-gutter py-8">
      <NumerologyConsole
        pending={chart.isPending}
        hasChart={chart.data !== undefined}
        onSubmit={(request) => chart.mutate(request)}
      />

      {chart.error ? (
        <TransitErrorNote
          error={chart.error}
          captions={CONTEXT_LABEL}
          hint="把姓名换成拼音或英文名后重新推演；中文名可填在选填格里，仅作回显、不参与计算。"
        />
      ) : null}

      {chart.isPending && !chart.data ? (
        <p className="label-caps text-ink-muted">正在逐字取值、约简六个核心数并排布两张九宫…</p>
      ) : null}

      {chart.data ? <NumerologyResults chart={chart.data} /> : null}
    </div>
  );
}

/**
 * 一次提交换一整套可核对的推导。
 *
 * 六张核心数卡不按下标取：`core` 的顺序虽由后端保证（生命灵数在首位），但按 `key` 找
 * 才把"哪张是大卡"这件事写在页面上，而不是藏在一份数组顺序的约定里。
 */
function NumerologyResults({ chart }: { chart: NumerologyChart }) {
  const lifePath = chart.core.find((card) => card.key === 'life_path');
  const others = chart.core.filter((card) => card.key !== 'life_path');
  const planesComplete = chart.loshu_grid.planes.filter((plane) => plane.complete).length;

  return (
    <>
      <ChartSummary chart={chart} />

      <ResultCard
        eyebrow="ASTRAL CORE MATRIX"
        title="核心本命数仪表盘"
        icon="gauge"
        actions={
          <span className="label-caps text-ink-muted">
            六个核心数 · 各自带约简账本
          </span>
        }
        elevated
      >
        <div className="flex flex-col gap-6">
          {lifePath ? <CoreNumberHero card={lifePath} /> : null}
          <KarmicDebtStrip debts={chart.karmic_debts} />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {others.map((card) => (
              <CoreNumberCard key={card.key} card={card} />
            ))}
          </div>
        </div>
      </ResultCard>

      {/* 两张九宫并排而不合并：输入不同、传统不同、缺数释义也不同（决策 9）。
          窄屏自然叠成两行，各自仍是完整的两张表。 */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <ResultCard
          eyebrow="NAME GRID"
          title="姓名天赋九宫"
          icon="search"
          actions={
            <span className="label-caps text-ink-muted">
              来自姓名 · 业力课 {chart.name_grid.karmic_lessons.length} 个
            </span>
          }
        >
          <NameGridPanel grid={chart.name_grid} fullName={chart.input.full_name} />
        </ResultCard>

        <ResultCard
          eyebrow="LOSHU GRID"
          title="生辰洛书九宫"
          icon="compass"
          actions={
            <span className="label-caps text-ink-muted">
              来自生日 · 八平面贯通 {planesComplete} 条
            </span>
          }
        >
          <LoshuGridPanel grid={chart.loshu_grid} birthDate={chart.input.birth_date} />
        </ResultCard>
      </div>

      <ResultCard
        eyebrow="PINNACLES & CHALLENGES"
        title="顶峰与挑战阶梯"
        icon="timeline"
        actions={<span className="label-caps text-ink-muted">四程顶峰 · 四项挑战</span>}
      >
        <PinnacleLadder pinnacles={chart.pinnacles} challenges={chart.challenges} />
      </ResultCard>

      <ResultCard
        eyebrow="PERSONAL CYCLES"
        title="个人年月日周期"
        icon="calendar"
        actions={
          <span className="label-caps text-ink-muted">
            基准日 <span className="numeric">{chart.provenance.reference_date}</span>
          </span>
        }
      >
        <PersonalCyclePanel cycles={chart.personal_cycles} />
      </ResultCard>

      <ResultCard
        eyebrow="LETTER MAP"
        title="字母映射与逐字透视"
        icon="seal"
        actions={
          <span className="label-caps text-ink-muted">
            {chart.letter_map.length} 列映射 · 姓名 {chart.letters.length} 个字母
          </span>
        }
      >
        <LetterMapTable columns={chart.letter_map} letters={chart.letters} input={chart.input} />
      </ResultCard>

      <ResultCard eyebrow="PROVENANCE" title="数据溯源" icon="vault">
        <ProvenancePanel
          tables={chart.provenance.tables}
          meta={[
            {
              label: '档案号',
              value: chart.provenance.badge,
              title: '只印方法标识，不印流水号：一个每人不同又无推导依据的号只能靠编（决策 16）',
            },
            { label: '推演引擎', value: chart.provenance.engine },
            {
              label: '参考日',
              value: chart.provenance.reference_date,
              title: '请求未指定时取服务器当日（定当前顶峰与个人年月日）',
            },
            {
              label: '参与字母数',
              value: String(chart.input.letter_count),
              title: '只有 A–Z 计入；其余字符如实报出、不折算成 0（决策 8）',
            },
            {
              label: '跳过字符数',
              value: String(chart.input.skipped_count),
            },
            {
              label: 'Y 元音判定',
              value: chart.input.y_as_vowel ? '计入元音' : '计为辅音',
              title: '决策 7：Y 的元音性依名字而定，无权威统一口径，故交给用户并说明判据',
            },
          ]}
          notes={[
            chart.provenance.method,
            '本页不出综合评分，也不出均衡度百分比：毕达哥拉斯数理没有权威的吉凶总分传统，硬凑一个加权分等于声称有人替它赋过分（决策 13、14）。',
            '约简只在后端做，前端一个算术都不重算：每张卡印的账本就是它自己的推导过程，拿计算器可以逐行复核（决策 5）。',
            '主数 11/22/33 一律保留不约简，唯一例外是四挑战 —— 例外本身写在挑战的算式串上（决策 3）。',
            '顶峰与挑战的时段是来源给的定性文本，不是精确到年的断言（spec §5.3）。',
            '迦勒底映射本轮不做：其字母表不同且 9 不分配给任何字母，混进同一张表会污染单测（决策 15）。',
            '总和为 0 的核心数如实留空并印出原因，不填 0 充数（决策 17）。',
          ]}
        />
      </ResultCard>
    </>
  );
}

/**
 * 姓名 + 生日 + 基准日 + 三个总和：让"到底算了什么"在结果之前就能核对。
 *
 * 与 `NamePage` 的 `NameSummary` 同一个用意 —— 一套推导越是繁复，越要先把**输入**摆在
 * 最上面：读者能一眼看出参与计算的字母数、被跳过了什么、Y 判成了哪一类，后面六张卡才有
 * 可对账的起点。档案号取自 `provenance.badge` 而不是写死在页面里，它才会跟着后端一起变。
 */
function ChartSummary({ chart }: { chart: NumerologyChart }) {
  const { input, provenance } = chart;

  const facts: Array<{ label: string; value: string; title?: string }> = [
    { label: '公历生日', value: input.birth_date, title: '数字命理是西方体系，公历是其原生输入（spec §4.2）' },
    {
      label: '基准日周岁',
      value: input.age_at_reference === null ? '基准日早于生日' : String(input.age_at_reference),
      title: '基准日早于生日时如实留空，不填负数或 0',
    },
    { label: '参与字母', value: `${input.letter_count} 个` },
    { label: '跳过字符', value: `${input.skipped_count} 个` },
    { label: '字母值总和', value: String(input.letter_total), title: '恒等于元音和 + 辅音和' },
  ];

  return (
    <div className="panel-raised flex flex-col gap-4 p-5 sm:p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <span className="label-caps">推演对象 · SUBJECT</span>
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-display text-2xl font-semibold text-gold-bright text-glow-gold sm:text-3xl">
              {input.full_name}
            </span>
            {input.name_zh ? (
              <span className="font-display text-xl text-ink-variant sm:text-2xl">
                （{input.name_zh}）
              </span>
            ) : null}
            <span className="numeric rounded-element bg-gold/15 px-2 py-1 text-xs text-gold">
              {provenance.badge}
            </span>
          </div>
        </div>
        <span className="label-caps text-ink-muted">
          Y 元音判定 · {input.y_as_vowel ? '计入元音' : '计为辅音'}
        </span>
      </div>

      <div className="gold-rule" />

      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:grid-cols-3 xl:grid-cols-5">
        {facts.map((fact) => (
          <div key={fact.label} className="flex flex-col gap-0.5">
            <dt className="label-caps text-ink-muted">{fact.label}</dt>
            <dd className="numeric text-ink" title={fact.title}>
              {fact.value}
            </dd>
          </div>
        ))}
      </dl>

      <p className="numeric text-xs leading-relaxed text-ink-muted">
        元音和 {input.vowel_total} + 辅音和 {input.consonant_total} = 全字母和{' '}
        {input.letter_total}
        。这三个是约简前的总和，各自约简后才是灵魂冲动数、人格面具数与表达数，
        约简过程印在对应卡片的账本里。
      </p>

      {input.skipped_count > 0 ? (
        <p className="flex items-start gap-2 text-sm text-wuxing-fire">
          <Icon name="alert" size={16} className="mt-0.5 shrink-0" />
          <span>
            有 {input.skipped_count} 个字符不参与计算（去重后：
            <span className="numeric">{input.skipped_chars.join(' ')}</span>
            ）。毕达哥拉斯映射只定义在拉丁字母表上，其余字符如实报出、不折算成 0（决策 8）。
          </span>
        </p>
      ) : null}
    </div>
  );
}

/**
 * 业力债条。
 *
 * spec §6.8 要求账本那一行打标记**并给释义**：标记由 `ReductionLadder` 在生命灵数的账本里
 * 印出，而释义只存在于 `karmic_debts` 这一份数据里 —— 页面不印它，那半条要求就落不了地，
 * 后端也就白查了一遍语料。空列表同样是结论（"查过了、没有"），故显式印出「无业力债」
 * 并说明为什么只判相加行，而不是整块消失让人以为漏了什么。
 *
 * 以 `number` 作 key 是安全的：相加行的总和至多 9+9+9=27，而 13→4 / 14→5 / 16→7 /
 * 19→10→1 四条链的中间量没有一个还落在 {13,14,16,19} 里，故一份账本至多报出一个业力债。
 */
function KarmicDebtStrip({ debts }: { debts: readonly KarmicDebt[] }) {
  if (debts.length === 0) {
    return (
      <p className="text-sm leading-relaxed text-ink-muted">
        生命灵数的相加行未落在 13 / 14 / 16 / 19 上，故无业力债。只有相加行会判：
        年份逐位约简的途中也会路过 19，那里多报一个就是报出来源本人也没报的债（spec §6.8）。
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <span className="label-caps text-wuxing-fire">业力债 · KARMIC DEBT</span>
      {debts.map((debt) => (
        <div key={debt.number} className="panel flex flex-col gap-2 p-4">
          <div className="flex flex-wrap items-baseline gap-3">
            <span className="numeric text-2xl text-wuxing-fire">{debt.number}</span>
            <span className="text-sm text-ink">{debt.label}</span>
            <span className="numeric text-xs text-ink-muted">{debt.expression}</span>
          </div>
          <p className="text-sm leading-relaxed text-ink-variant">{debt.meaning}</p>
          <SourceNote source={debt.source} />
        </div>
      ))}
    </div>
  );
}
