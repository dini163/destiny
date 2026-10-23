import { Icon } from '../../ui/Icon';
import { GENDER_LABEL } from '../../../lib/gender';
import type { ApiError } from '../../../api/client';

/** `context` 里那些"取值本身也是机器词"的键：合婚的 `partner` 是唯一的例子。 */
const VALUE_LABEL: Record<string, string> = { male: GENDER_LABEL.male, female: GENDER_LABEL.female };

/**
 * 域错误（岁运、流日、流时、合婚与数字命理共用的 `transit_*` / `liuri_*` / `liushi_*` /
 * `hehun_*` / `numerology_*` 十个码，外加带 `context.partner` 的 `invalid_birth_data`）的页顶回显。
 *
 * 文案照后端原句（"2028-06-01 不在 2028-01-06 ~ 2028-02-03 这一段里"），数字与日期另取
 * `context` 排成可扫读的一行，让读者知道该把表单改成什么 —— 两处同源，不可能互相打架。
 * 校验错误（`validation_error`，pydantic 那份信封）不在域之列：它没有 `context`，
 * 只剩后端 `detail` 拼出的那一句，也就只有那一句可给。
 */
export function TransitErrorNote({
  error,
  captions,
  hint,
}: {
  error: ApiError;
  /** 本页可能收到的 `context` 键 → 中文标签；未收入的键以机器键原样呈现。 */
  captions: Record<string, string>;
  /** 域错误时补的一句"那该怎么办"，各页按自己的控件写。 */
  hint?: string;
}) {
  const isDomain =
    error.code.startsWith('transit_') ||
    error.code.startsWith('liuri_') ||
    error.code.startsWith('liushi_') ||
    error.code.startsWith('hehun_') ||
    // 数字理只有一个域码（`numerology_no_latin_letters`）：纯中文名过得了 pydantic 的长度
    // 校验，坏的是「毕达哥拉斯映射只定义在 A–Z 上」这条只有引擎知道的前提。
    error.code.startsWith('numerology_') ||
    // 合婚独有：`invalid_birth_data` 不是前缀族，但 §9.2 往它的 `context` 里塞了
    // `partner`。那一格不列出来，页面就只说"这一造排不出来"而说不出是哪一造。
    error.context?.partner !== undefined;
  const facts = isDomain ? contextFacts(error.context, captions) : [];

  return (
    <div className="flex items-start gap-2 rounded-element border border-wuxing-fire/40 bg-wuxing-fire/10 px-4 py-3 text-sm text-ink">
      <Icon name="alert" size={18} className="mt-0.5 shrink-0 text-wuxing-fire" />
      <div className="flex flex-col gap-1.5">
        <span>{error.message}</span>
        {facts.length > 0 ? (
          <span className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-muted">
            {facts.map((fact) => (
              <span key={fact.label}>
                {fact.label}
                <span className="numeric ml-1 text-ink">{fact.value}</span>
              </span>
            ))}
          </span>
        ) : null}
        {isDomain && hint ? <span className="text-xs text-ink-muted">{hint}</span> : null}
      </div>
    </div>
  );
}

/**
 * `context` 里的数值与日期串 → 中文标签 + 原值。
 *
 * 岁运的六个键全是年份数字，流日的三个键全是 `YYYY-MM-DD`，两者都要摆出来才看得懂
 * 该改成什么；流时另有两个键，`supported` 是一整串十二支（`子丑寅卯辰巳午未申酉戌亥`），
 * 与 `requested` 并排即说明该往哪个方向改。其余类型（如姓名学的候选字列表）留给文案自己说。
 */
function contextFacts(
  context: Record<string, unknown> | undefined,
  captions: Record<string, string>,
): Array<{ label: string; value: string }> {
  const facts: Array<{ label: string; value: string }> = [];
  for (const [key, value] of Object.entries(context ?? {})) {
    if (typeof value === 'number') {
      facts.push({ label: captions[key] ?? key, value: String(value) });
    } else if (typeof value === 'string' && value !== '') {
      facts.push({ label: captions[key] ?? key, value: VALUE_LABEL[value] ?? value });
    }
  }
  return facts;
}
