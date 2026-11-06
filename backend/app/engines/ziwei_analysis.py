"""Ziwei 13-Dimension Chart Analysis and Deep Interpretation Engine.

Derived from Ni Haixia Tianji / classical Dou Shu corpus (CC BY 4.0).
Provides deterministic, local chart interpretation across 13 life dimensions:
  mingGong, personality, xiongDi, fuQi, ziNv, caiBo, jiE,
  qianYi, jiaoYou, guanLu, tianZhai, fuDe, fuMu
"""

from typing import Any

from app.content.ziwei_db import (
    COMBO_DB,
    DUAL_STAR_SECTION_DB,
    KUIYUE_DESC_DB,
    NIANGAN_SIHUA_IMPACT_DB,
    QUANSHU_JUAN2_DB,
    SANFANG_AUX_DESC_DB,
    SANFANG_STAR_DESC_DB,
    SECOND_STAR_DESC_DB,
    SIHUA_STAR_DESC_DB,
    SPECIAL_PATTERNS_DB,
    STAR_AUX_DB,
    STAR_BRIGHTNESS_DB,
    STAR_DB,
    STAR_SECTIONS_DB,
    STAR_SIHUA_DB,
    TARGET_CHART_NOTES_DB,
    TOPIC_SUMMARY_DB,
    ZANGFU_DB,
)
from app.schemas.ziwei import Palace, StarPlacement, ZiweiChart

TOPIC_KEYS = (
    "mingGong",
    "personality",
    "xiongDi",
    "fuQi",
    "ziNv",
    "caiBo",
    "jiE",
    "qianYi",
    "jiaoYou",
    "guanLu",
    "tianZhai",
    "fuDe",
    "fuMu",
)

TOPIC_PALACE_MAP: dict[str, str] = {
    "mingGong": "命宫",
    "personality": "命宫",
    "xiongDi": "兄弟",
    "fuQi": "夫妻",
    "ziNv": "子女",
    "caiBo": "财帛",
    "jiE": "疾厄",
    "qianYi": "迁移",
    "jiaoYou": "仆役",
    "guanLu": "官禄",
    "tianZhai": "田宅",
    "fuDe": "福德",
    "fuMu": "父母",
}

TOPIC_LABELS: dict[str, str] = {
    "mingGong": "命格总览",
    "personality": "性格特质",
    "xiongDi": "兄弟姐妹",
    "fuQi": "感情婚姻",
    "ziNv": "子女缘分",
    "caiBo": "财富运势",
    "jiE": "健康状况",
    "qianYi": "外出迁移",
    "jiaoYou": "人际交友",
    "guanLu": "事业发展",
    "tianZhai": "田宅家运",
    "fuDe": "精神福德",
    "fuMu": "父母长辈",
}

TOPIC_SUMMARY_HEADERS: dict[str, str] = {
    "mingGong": "命格总览",
    "personality": "性格总览",
    "fuQi": "感情总览",
    "guanLu": "事业总览",
    "caiBo": "财运总览",
    "jiE": "健康总览",
    "xiongDi": "兄弟总览",
    "ziNv": "子女总览",
    "qianYi": "迁移总览",
    "jiaoYou": "人际总览",
    "tianZhai": "田宅总览",
    "fuDe": "福德总览",
    "fuMu": "父母总览",
}

CORE_12_AUX_STARS = {
    "左辅", "右弼", "文昌", "文曲", "天魁", "天钺",
    "擎羊", "陀罗", "火星", "铃星", "地空", "地劫",
}

SHA_STARS_SET = {"擎羊", "陀罗", "火星", "铃星", "地空", "地劫"}

SIHUA_ICON: dict[str, str] = {
    "化禄": "🟢",
    "化权": "🔵",
    "化科": "🟡",
    "化忌": "🔴",
    "禄": "🟢",
    "权": "🔵",
    "科": "🟡",
    "忌": "🔴",
}


def _short_palace_name(name: str, for_quanshu: bool = False) -> str:
    cleaned = name.replace("宫", "")
    if for_quanshu:
        if cleaned in ("仆役", "交友"):
            return "奴仆"
    if cleaned == "命":
        return "命宫"
    return cleaned


def _major_stars(palace: Palace) -> list[StarPlacement]:
    return [s for s in palace.stars if s.kind == "主星"]


def _aux_stars(palace: Palace) -> list[StarPlacement]:
    return [s for s in palace.stars if s.kind != "主星"]


def _format_star(star: StarPlacement) -> str:
    sh = f"{star.sihua}" if star.sihua else ""
    return f"{star.name}{sh}"


def _find_combo(stars: list[StarPlacement]) -> dict[str, Any] | None:
    if len(stars) < 2:
        return None
    names = {s.name for s in stars}
    for combo in COMBO_DB.values():
        c_stars = combo.get("stars", [])
        if len(c_stars) == 2 and c_stars[0] in names and c_stars[1] in names:
            return combo
    return None


def _build_shengong_text(chart: ZiweiChart) -> str:
    body_palace_name = chart.shen_gong_name
    body_palace = next((p for p in chart.palaces if p.name == body_palace_name), None)
    if not body_palace:
        return ""
    ps = _short_palace_name(body_palace.name)
    if ps == "命宫":
        return (
            "你的身宫和命宫同宫。身宫代表后天作为与主观追求，"
            "身命同宫代表言行归一、身心同行，先天秉性与后天作为高度重合。"
        )
    majors = _major_stars(body_palace)
    star_label = "、".join(_format_star(s) for s in majors) if majors else "空宫"
    role_map: dict[str, str] = {
        "夫妻": f"你的身宫落**夫妻**（{star_label}）——婚姻与亲密关系对你后天的影响比较大，家庭情感往往是人生重要转折点。",
        "财帛": f"你的身宫落**财帛**（{star_label}）——后天重心偏向财运与经济积累，后天受钱财经营与物质基础影响最深。",
        "迁移": f"你的身宫落**迁移**（{star_label}）——后天发展宜往外走，在外地、跨地域或变动环境中更能打开局面。",
        "官禄": f"你的身宫落**官禄**（{star_label}）——后天重心在事业与职位成就上，个人发展受工作平台与职责使命驱动最大。",
        "福德": f"你的身宫落**福德**（{star_label}）——后天重精神世界、兴趣追求与内心安稳，身心清闲对你而言尤为关键。",
    }
    return role_map.get(
        ps,
        f"你的身宫落**{ps}**（{star_label}）。身宫代表后天作为与追求，是后天努力重心所在。"
    )


def generate_topic_analysis(chart: ZiweiChart, topic: str) -> str:
    """Generate structured Markdown analysis for one of the 13 life topics."""
    target_palace_name = TOPIC_PALACE_MAP.get(topic, "命宫")
    palace = next((p for p in chart.palaces if p.name == target_palace_name), None)
    if not palace:
        return ""

    palace_idx = palace.index
    opp_palace = next(p for p in chart.palaces if p.index == (palace_idx + 6) % 12)
    tri1_palace = next(p for p in chart.palaces if p.index == (palace_idx + 4) % 12)
    tri2_palace = next(p for p in chart.palaces if p.index == (palace_idx + 8) % 12)

    self_majors = _major_stars(palace)
    opp_majors = _major_stars(opp_palace)
    is_empty = len(self_majors) == 0
    effective_stars = opp_majors if is_empty else self_majors
    first_star = effective_stars[0].name if effective_stars else "紫微"
    first_star_info = effective_stars[0] if effective_stars else None
    gender = chart.gender or "male"
    p_short = _short_palace_name(palace.name)

    sections: list[str] = []

    # 1. 主题总览
    sum_header = TOPIC_SUMMARY_HEADERS.get(topic, "总览")
    sum_key1 = f"{topic}|空宫:{first_star}|{gender}" if is_empty else f"{topic}|{first_star}|{gender}"
    sum_key2 = f"{topic}|{first_star}|{gender}"
    sum_text = TOPIC_SUMMARY_DB.get(sum_key1) or TOPIC_SUMMARY_DB.get(sum_key2)
    if sum_text:
        sections.append(f"**【{sum_header}】**\n\n{sum_text}")

    # 2. 一句话定调 & 核心论断
    combo = _find_combo(effective_stars) if not is_empty else None
    combo_topic_key = topic if topic in ("mingGong", "fuQi", "guanLu", "caiBo") else None
    combo_palace_data = combo.get("topics", {}).get(combo_topic_key) if combo and combo_topic_key else None
    base_star_data = STAR_SECTIONS_DB.get(first_star, {}).get(topic) or STAR_SECTIONS_DB.get("紫微", {}).get(topic, {})

    dingdiao = (combo_palace_data.get("dingdiao") if combo_palace_data else None) or base_star_data.get("dingdiao", "")
    sections.append(f"**【一句话定调】**\n\n{dingdiao}")

    lundian_parts: list[str] = [(combo_palace_data.get("lundian") if combo_palace_data else None) or base_star_data.get("lundian", "")]
    if first_star_info and first_star_info.sihua:
        sh_key = f"{topic}|{first_star}|{first_star_info.sihua}"
        sh_extra = STAR_SIHUA_DB.get(sh_key)
        if sh_extra and sh_extra[:16] not in lundian_parts[0]:
            lundian_parts.append(sh_extra)
    sections.append(f"**【核心论断】**\n\n" + "\n\n".join(p for p in lundian_parts if p))

    # 3. 身宫 · 后天追求 (仅命格总览)
    if topic == "mingGong":
        sg_text = _build_shengong_text(chart)
        if sg_text:
            sections.append(f"**【身宫 · 后天追求】**\n\n{sg_text}")

    # 4. 命盘推演
    tuiyan_lines: list[str] = []
    if is_empty:
        opp_names = "、".join(s.name for s in opp_majors) or "空宫"
        tuiyan_lines.append(f"本宫无主星（空宫），借对宫【{_short_palace_name(opp_palace.name)}：{opp_names}】论事")
    else:
        main_str = "、".join(_format_star(s) for s in self_majors)
        ju_str = f"，{chart.wuxing_ju}" if topic == "mingGong" and chart.wuxing_ju else ""
        tuiyan_lines.append(f"本宫主星：{main_str}{ju_str}")
        if len(self_majors) > 1:
            sec_star = self_majors[1]
            sec_desc = SECOND_STAR_DESC_DB.get(sec_star.name)
            if sec_desc:
                tuiyan_lines.append(f"\n同宫第二主星：**{sec_star.name}**——{sec_desc}")
    sections.append(f"**【命盘推演】**\n\n" + "\n".join(tuiyan_lines))

    # 5. 三方四正联动
    sf_blocks: list[str] = []

    def render_palace_block(hdr: str, p: Palace, is_self: bool) -> str:
        lines: list[str] = []
        ps = _short_palace_name(p.name)
        p_majors = _major_stars(p)
        p_star_str = "、".join(_format_star(s) for s in p_majors) if p_majors else f"{ps}空宫"
        lines.append(f"▍**{hdr} · {ps}**：{p_star_str}")
        if not is_self:
            if not p_majors:
                p_opp = next(x for x in chart.palaces if x.index == (p.index + 6) % 12)
                p_opp_names = "、".join(s.name for s in _major_stars(p_opp)) or "无"
                lines.append(f"  （空宫，借对宫{_short_palace_name(p_opp.name)}：{p_opp_names}入事）")
            else:
                for s in p_majors:
                    desc = SANFANG_STAR_DESC_DB.get(s.name, "")
                    sh_desc = SIHUA_STAR_DESC_DB.get(f"{s.name}|{s.sihua}", "") if s.sihua else ""
                    sh_sfx = f" ｜ {s.sihua}：{sh_desc}" if s.sihua and sh_desc else ""
                    if desc:
                        lines.append(f"  {_format_star(s)}：{desc}{sh_sfx}")
        for aux in _aux_stars(p):
            aux_desc = SANFANG_AUX_DESC_DB.get(f"{ps}|{aux.name}") or SANFANG_AUX_DESC_DB.get(f"交友|{aux.name}")
            if aux_desc:
                lines.append(f"✦ **{aux.name}**：{aux_desc}")
        return "\n".join(lines)

    t1_short = _short_palace_name(tri1_palace.name)
    t2_short = _short_palace_name(tri2_palace.name)
    opp_short = _short_palace_name(opp_palace.name)

    sf_blocks.append(render_palace_block("本宫", palace, True))
    sf_blocks.append(render_palace_block(f"{p_short}三合·{t1_short}", tri1_palace, False))
    sf_blocks.append(render_palace_block(f"{p_short}三合·{t2_short}", tri2_palace, False))
    sf_blocks.append(render_palace_block(f"{p_short}对宫·{opp_short}", opp_palace, False))

    self_body = "空宫·借对宫入事" if is_empty else "、".join(s.name for s in self_majors)
    opp_body = "、".join(s.name for s in opp_majors) if opp_majors else "空宫"
    tri_body = "、".join(s.name for s in _major_stars(tri1_palace) + _major_stars(tri2_palace)) or "无"
    sf_blocks.append(
        f"▸ **本盘合参**：{p_short}本宫【{self_body}】为体、对宫【{opp_body}】为用 ｜ 三合会【{tri_body}】——本命四化固定不动，吉凶看大限/流年引动。"
    )
    sections.append(f"**【三方四正联动】**\n\n" + "\n\n".join(sf_blocks))

    # 6. 四化路径分析
    sf_palaces = [
        (palace, f"你{TOPIC_LABELS.get(topic, '')}本宫"),
        (tri1_palace, f"你{p_short}的三合"),
        (tri2_palace, f"你{p_short}的三合"),
        (opp_palace, f"你{p_short}的对宫"),
    ]
    sihua_lines: list[str] = []
    for p, rel in sf_palaces:
        ps = _short_palace_name(p.name)
        for s in p.stars:
            if s.sihua:
                icon = SIHUA_ICON.get(s.sihua, "🔹")
                desc = SIHUA_STAR_DESC_DB.get(f"{s.name}|{s.sihua}", "")
                sihua_lines.append(f"{icon} **{s.name}{s.sihua}**（落{ps}·{rel}）\n   {desc}")
    if topic in ("mingGong", "personality"):
        kuiyue_lines: list[str] = []
        for p in chart.palaces:
            ps = _short_palace_name(p.name)
            for s in p.stars:
                if s.name in ("天魁", "天钺"):
                    kd = KUIYUE_DESC_DB.get(f"{s.name}|{ps}")
                    if kd:
                        kuiyue_lines.append(f"◇ **{s.name}在{ps}**：{kd}")
        if kuiyue_lines:
            sihua_lines.append("\n".join(kuiyue_lines))
    if sihua_lines:
        sections.append(f"**【四化路径分析 · 落到你这盘】**\n\n" + "\n".join(sihua_lines))

    # 7. 年干四化·关键宫位影响
    ng_impacts: list[str] = []
    for p in chart.palaces:
        ps = _short_palace_name(p.name)
        for s in p.stars:
            if s.sihua:
                imp = NIANGAN_SIHUA_IMPACT_DB.get(f"{topic}|{s.sihua}|{ps}")
                if imp:
                    icon = SIHUA_ICON.get(s.sihua, "🔴")
                    ng_impacts.append(f"{icon} **{s.name}{s.sihua}**（落{ps}）→ {imp}")
    if ng_impacts:
        sections.append(f"**【年干四化·关键宫位影响】**\n\n" + "\n".join(ng_impacts))

    # 8. 子午流注 · 宫位取象（仅疾厄宫）
    if topic == "jiE":
        max_sha_palace = palace
        max_shas: list[str] = []
        for p in chart.palaces:
            shas = [s.name for s in p.stars if s.name in SHA_STARS_SET]
            if len(shas) > len(max_shas):
                max_shas = shas
                max_sha_palace = p
        zf_worst = ZANGFU_DB.get(max_sha_palace.zhi)
        zf_jie = ZANGFU_DB.get(palace.zhi)
        if zf_worst and zf_jie:
            sha_lbl = "、".join(max_shas) if max_shas else "煞曜轻微"
            sections.append(
                f"**【子午流注 · 宫位脏腑取象（经方参考）】**\n\n"
                f"全盘煞星相对最集中在 **{max_sha_palace.zhi}宫**（{sha_lbl}）→ 对应脏腑 **{zf_worst.get('organ_full')}**\n\n"
                f"疾厄宫落于 **{palace.zhi}宫**，本位地支对应如下，只作参考；看疾厄当综合全盘，哪一宫煞星最集中亦当参看那一宫的地支配属：\n"
                f"▸ 脏腑取象：**{zf_jie.get('organ_short')}**\n"
                f"▸ 对应经络：{zf_jie.get('meridian')}\n"
                f"▸ 经络旺时：{zf_jie.get('hours')}\n"
                f"▸ 养生要点：{zf_jie.get('tip')}\n\n"
                f"> 这是传统术数与经方医学的文化取象，不是医学诊断，也不替代症状评估、体检或执业医师意见。"
            )

    # 9. 命盘依据
    yiju = (combo_palace_data.get("yiju") if combo_palace_data else None) or base_star_data.get("yiju", "")
    if yiju:
        sections.append(f"**【命盘依据】**\n\n{yiju}")

    # 10. 经典出处 + 《紫微斗数全书》卷二十二宫断语
    chuchu = (combo_palace_data.get("chuchu") if combo_palace_data else None) or base_star_data.get("chuchu", "")
    quanshu_lines: list[str] = []
    palace_all_stars = [s.name for s in effective_stars] + [s.name for s in _aux_stars(palace)]
    if any(s.sihua == "化忌" for s in effective_stars):
        palace_all_stars.append("化忌")
    q_palace_key = _short_palace_name(palace.name, True)
    for st_name in palace_all_stars:
        q_list = QUANSHU_JUAN2_DB.get(f"{p_short}|{st_name}") or QUANSHU_JUAN2_DB.get(f"{q_palace_key}|{st_name}")
        if q_list:
            for q in q_list:
                quanshu_lines.append(f"· 《紫微斗数全书·卷二·{p_short}》{st_name}条：「{q}」")
    if quanshu_lines:
        chuchu_block = f"{chuchu}\n\n▸ 《紫微斗数全书》卷二十二宫断语（明清刻本原文·传统流派参考）：\n" + "\n".join(quanshu_lines)
    else:
        chuchu_block = chuchu
    if chuchu_block:
        sections.append(f"**【经典出处】**\n\n{chuchu_block}")

    # 11. ⚠️ 风险提醒
    risk_lines: list[str] = []
    for s in palace.stars:
        if s.sihua == "化忌":
            risk_lines.append(f"◆ 本宫见【{s.name}化忌】：{TOPIC_LABELS.get(topic, '')}易有阻滞，凡事需多一分坚持与复盘。")
        elif s.name in SHA_STARS_SET:
            risk_lines.append(f"◆ 本宫见【{s.name}】，{TOPIC_LABELS.get(topic, '')}略有阻力，需识破情绪再做决策。")
    if is_empty:
        risk_lines.append(f"◆ 本宫空宫，能量需借对宫论事，{TOPIC_LABELS.get(topic, '')}走势比一般人更易受外缘/对宫牵动，宜提升自主定力。")
    if risk_lines:
        sections.append(
            f"**【⚠️ 风险提醒】**\n\n> 紫微斗数讲究阴阳互见，下方为基于本盘特征的中性提醒，知所警惕方能转危为安。\n\n" + "\n".join(risk_lines)
        )

    # 12. 双星同宫专题节
    if combo:
        title = combo.get("title", "")
        palaces_s = combo.get("palaces", "")
        brief = combo.get("brief", "")
        ds_markdown = DUAL_STAR_SECTION_DB.get(f"{topic}|{title}")
        if not ds_markdown and combo_palace_data:
            ds_markdown = f"## ✦ 双星同宫 · 「{title}」（{palaces_s}）\n\n*{brief}*\n\n{combo_palace_data.get('lundian')}"
        if ds_markdown:
            sections.append(f"---\n\n{ds_markdown}")

    # 13. ⚙ 主辅煞组合精细论断（168 矩阵）
    aux_names = [s.name for s in _aux_stars(palace)]
    aux_blocks: list[str] = []
    for ms in effective_stars:
        for aux_name in aux_names:
            if aux_name in CORE_12_AUX_STARS:
                entry = STAR_AUX_DB.get(f"{ms.name}+{aux_name}")
                if entry:
                    aux_blocks.append(f"### {entry.get('icon', '✦')} 「{ms.name}+{aux_name}」 — {entry.get('tag', '')}\n\n{entry.get('desc', '')}")
    if aux_blocks:
        main_names_str = "、".join(s.name for s in effective_stars)
        aux_names_str = "、".join(aux_names)
        sections.append(
            f"---\n\n## ⚙ 主辅煞组合精细论断（{p_short}宫实际辅煞）\n\n"
            f"*你的{p_short}宫除主星「{main_names_str}」外还同坐：{aux_names_str}。以下为各组合专属论断（基于主辅煞组合矩阵）：*\n\n" +
            "\n\n".join(aux_blocks)
        )

    return "\n\n".join(sections)


def generate_all_topics_analysis(chart: ZiweiChart) -> dict[str, str]:
    """Generate all 13 topics for a complete chart reading."""
    return {topic: generate_topic_analysis(chart, topic) for topic in TOPIC_KEYS}

