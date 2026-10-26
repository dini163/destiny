import type { RuneCastResponse } from '../types/runes';

/**
 * 符印命谱导出：把一次铸石响应装配成纯文本，并在浏览器本地落一份 `.txt`。
 *
 * 不引 PDF/打印依赖，也不走后端：命谱是本次响应的一次**本地快照复述**，字段全部取自
 * `RuneCastResponse`，前端不重算星级、配比或吉凶（与页面同一条「不另算」纪律）。朝向、名义、
 * 关键词、释义逐字照搬响应；空白符没有字形，命谱里照实写「无刻痕」。
 */

/** 朝向在命谱里的短标签，对齐页面 `orientationMeta` 的口径，不复制颜色。 */
function orientationLabel(upright: boolean): string {
  return upright ? '正位' : '逆位（merkstave）';
}

/** 把一次铸石装配成可读纯文本。纯函数，便于单独测试，不触碰 DOM。 */
export function buildRuneTranscript(cast: RuneCastResponse): string {
  const lines: string[] = [];

  lines.push('北欧卢恩神谕 · 符印命谱');
  lines.push('================================');
  lines.push(`牌阵：${cast.spread_name_zh}（${cast.spread_name}）`);
  lines.push(cast.question ? `所问：${cast.question}` : '所问：（未附）');
  lines.push(`导出时间：${new Date().toLocaleString('zh-CN')}`);
  lines.push('');

  lines.push('【石碑位次】');
  cast.stones.forEach((stone, index) => {
    lines.push('');
    lines.push(`${index + 1}. ${stone.position_label_zh}（${stone.position_label}） · ${orientationLabel(stone.orientation === 'upright')}`);
    if (stone.is_wyrd) {
      lines.push('   无刻痕（空白石 · 现代增补）');
    } else {
      lines.push(`   字形 ${stone.glyph} · ${stone.name} · ${stone.name_zh} · 音译 ${stone.transliteration || '无'}`);
    }
    lines.push(`   名义：${stone.name_meaning}`);
    if (stone.keywords.length > 0) {
      lines.push(`   关键词：${stone.keywords.join(' / ')}`);
    }
    lines.push(`   释义：${stone.meaning}`);
    lines.push(`   位次：${stone.position_meaning}`);
  });

  lines.push('');
  lines.push('【综合结论】');
  lines.push(`档位：${cast.verdict.grade}（${cast.verdict.stars} / 5 星）`);
  lines.push(`${cast.verdict.headline}`);
  if (cast.verdict.points.length > 0) {
    cast.verdict.points.forEach((point) => lines.push(`· ${point}`));
  }
  lines.push(`建议：${cast.verdict.advice}`);

  lines.push('');
  lines.push('【综合直读】');
  lines.push(cast.synthesis);

  lines.push('');
  lines.push('【Aettir 组别配比（计数，非评分）】');
  cast.aett_balance.forEach((row) => {
    lines.push(`${row.name_zh}（${row.name}）：${row.count} 枚`);
  });

  if (cast.shadow_counsel && cast.shadow_counsel.length > 0) {
    lines.push('');
    lines.push('【阴影参照（反面参照，非本次结果）】');
    cast.shadow_counsel.forEach((note) => {
      lines.push(`${note.name_zh}（${note.position_label_zh} · ${note.drawn_orientation === 'upright' ? '正位' : '逆位'}）`);
      lines.push(`  ${note.shadow_meaning}`);
    });
  }

  return lines.join('\n');
}

/** 本地下载命谱 `.txt`；文件名带牌阵与时间戳，不重复覆盖。 */
export function downloadRuneTranscript(cast: RuneCastResponse): void {
  const text = buildRuneTranscript(cast);
  const blob = new Blob(['﻿' + text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `rune-${cast.spread_id}-${stamp}.txt`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
