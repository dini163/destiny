import { describe, expect, it } from 'vitest';

import {
  GENDER_LABEL,
  GENDER_SHORT,
  annotateGenderTerms,
  annotatePlainSections,
} from '../../src/lib/gender';

describe('造向标注', () => {
  it('全称与短称都把男女放在术语旁边', () => {
    expect(GENDER_LABEL.male).toBe('乾造（男）');
    expect(GENDER_LABEL.female).toBe('坤造（女）');
    expect(GENDER_SHORT.male).toBe('乾（男）');
    expect(GENDER_SHORT.female).toBe('坤（女）');
  });

  it('合盘响应里的造向词在渲染时补上男女', () => {
    expect(annotateGenderTerms('乾造 / 坤造')).toBe('乾造（男） / 坤造（女）');
    expect(annotateGenderTerms('乾视坤 / 坤视乾')).toBe(
      '乾（男）视坤（女） / 坤（女）视乾（男）',
    );
    expect(annotateGenderTerms('乾独宜 / 坤独忌')).toBe('乾（男）独宜 / 坤（女）独忌');
    expect(annotateGenderTerms('两造干合（乾年×坤时）')).toBe(
      '两造干合（乾（男）年×坤（女）时）',
    );
    expect(annotateGenderTerms('乾年命大林木、坤年命路旁土')).toBe(
      '乾（男）年命大林木、坤（女）年命路旁土',
    );
    expect(annotateGenderTerms('乾·第 4 运 戊午／坤·第 5 运 丁丑')).toBe(
      '乾（男）·第 4 运 戊午／坤（女）·第 5 运 丁丑',
    );
  });

  it('不动乾坤、乾为天这类非造向用法', () => {
    expect(annotateGenderTerms('乾坤')).toBe('乾坤');
    expect(annotateGenderTerms('乾为天，坤为地')).toBe('乾为天，坤为地');
  });

  it('重复渲染也不会叠出第二层括号', () => {
    const once = annotateGenderTerms('乾造 / 乾视坤 / 乾年');
    expect(annotateGenderTerms(once)).toBe(once);
  });

  it('白话小节只改正文，标题原样保留', () => {
    const sections = annotatePlainSections([
      { title: '五行互给', text: '从乾这一侧看过去，坤递过来的那组五行是金。' },
    ]);
    expect(sections).toEqual([
      { title: '五行互给', text: '从乾（男）这一侧看过去，坤（女）递过来的那组五行是金。' },
    ]);
  });
});
