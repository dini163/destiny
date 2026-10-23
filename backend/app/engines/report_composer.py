"""付费报告装配器：把既有引擎算好的盘面事实装配成报告（v2.1 §3A）。

职责边界（与 AGENTS.md 第 1/6/9 条对齐）：

1. **不重算历法/星历**：三份报告分别调用 `compute_hehun` / `compute_bazi_chart` /
   `compute_transit`，只消费它们返回的结构化事实（分数、柱、命中、白话）。
2. **不现编文案**：所有句子来自 `content/report_templates.py` 的受控模板 + 盘面事实填空；
   装配器只做「选哪句模板、填什么事实」，不写无来源断言。
3. **每条结论必须有依据**：每章关键结论配一张 `ReportEvidenceCard`（结论/盘面事实/出处/
   可推翻句三分离，PRD §3A.1 原则 3）。
4. **无状态订单**：`order_id`/`token`/`expires_at` 由 `app.core.report_orders` 派生，
   同一输入恒同，取报告时按同一输入重算（确定性可复现，AGENTS.md 第 9 条）。

报告版本号在 `content.report_templates.REPORT_VERSION`；修改模板句不影响版本（句子内容
变更才 bump）。阈值（逐月节奏分档）是本地的模型参数，见 `_month_tone` 的注释。
"""

from datetime import date, datetime

from app.content import report_templates as T
from app.core.chart_input import chart_longitude
from app.core.config import get_settings
from app.core.report_orders import derive_order_id, expires_at_for, sign_token
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_hehun import compute_hehun
from app.engines.bazi_transit import compute_transit
from app.schemas.bazi import BaziChart, BaziNatalRequest
from app.schemas.bazi_hehun import BaziHehunRequest, BaziHehunResult
from app.schemas.bazi_transit import BaziTransitRequest, BaziTransitResult
from app.schemas.report import (
    ReportDocument,
    ReportEvidenceCard,
    ReportPreview,
    ReportProduct,
    ReportSection,
)

#: 逐月节奏分档阈值（本地模型参数，与岁运分数 0–100 同尺）：≥65 推进、50–64 谈判、
#: 35–49 收尾、<35 休整。句子在 `T.R3_MONTH_TONES`，阈值在此 —— 文案与数值分开维护。
_MONTH_TONE_THRESHOLDS = (65.0, 50.0, 35.0)


def compose_report(
    product: ReportProduct, request, reference_date: date | None = None
) -> ReportDocument:
    """装配一份完整报告（含签名链接三要素）。`request` 按产品分派到对应既有入参。"""
    if product == "r1":
        return _compose_r1(request, reference_date)
    if product == "r2":
        return _compose_r2(request, reference_date)
    if product == "r3":
        return _compose_r3(request, reference_date)
    raise ValueError(f"unknown report product: {product}")


def compose_preview(
    product: ReportProduct, request, reference_date: date | None = None
) -> ReportPreview:
    """免费预览：完整装配后只取一页摘要的条目作关键结论（PRD §3A.2–3A.4）。"""
    doc = compose_report(product, request, reference_date)
    summary = next(s for s in doc.sections if s.kind == "summary")
    return ReportPreview(
        product=product,
        title=doc.title,
        tagline=doc.tagline,
        version=doc.version,
        generated_date=doc.generated_date,
        input_summary=doc.input_summary,
        summary=summary.bullets,
        key_points=summary.bullets[:4],
        section_count=len(doc.sections),
        notice=T.PREVIEW_NOTICE,
    )


# ---------------------------------------------------------------------------
# R1 双人关系说明书：装配 compute_hehun 的结果
# ---------------------------------------------------------------------------


def _compose_r1(request: BaziHehunRequest, reference_date: date | None) -> ReportDocument:
    result = compute_hehun(
        male=request.male,
        female=request.female,
        reference_date=reference_date,
        axis_start_year=request.axis_start_year,
        axis_years=request.axis_years,
    )
    male, female = result.male, result.female
    tables = _table_names(result.provenance.tables)
    rules_src = _pick_table(tables, "hehun_rules") or _pick_table(tables, "plain") or tables[0]
    plain_src = _pick_table(tables, "plain") or rules_src
    ref_year = int(result.provenance.reference_date[:4])

    # 一页摘要 --------------------------------------------------------------
    complement_brief = _r1_complement_brief(result)
    risk = _r1_top_risk(result)
    advice_lines = [result.verdict.advice] if result.verdict.advice else []
    advice_lines.append(_action(T.R1_ACTION_FOCUS["scripts"], "act"))
    advice_lines.append(_action(T.R1_ACTION_FOCUS["conflict"], "observe"))
    summary = _section(
        "summary",
        T.REPORT_SECTION_NAMES["r1"]["summary"],
        "summary",
        bullets=[
            f"{T.R1_SUMMARY_LABELS['tone']}：{result.verdict.headline}",
            f"{T.R1_SUMMARY_LABELS['complement']}：{complement_brief}",
            f"{T.R1_SUMMARY_LABELS['risk']}：{risk}",
            f"{T.R1_SUMMARY_LABELS['advice']}：{'；'.join(advice_lines)}",
        ],
        cards=[
            _card(
                "r1-summary-01",
                result.verdict.headline,
                f"契合分 {result.score.value}（{result.verdict.grade}，{result.verdict.stars} 星）",
                rules_src,
                "high",
            )
        ],
    )

    # 双方核心需求与给予方式 ------------------------------------------------
    needs_items = []
    for who, p in (("乾造", male), ("坤造", female)):
        need = _need_for(p.favorable_elements, p.unfavorable_elements)
        needs_items.append(
            T.R1_NEEDS_ITEM.format(
                who=who,
                day_master=p.day_master,
                favorable="、".join(p.favorable_elements) or "—",
                unfavorable="、".join(p.unfavorable_elements) or "—",
                need=need["need"],
                blind=need["blind"],
            )
        )
    needs = _section(
        "needs",
        T.REPORT_SECTION_NAMES["r1"]["needs"],
        "chapter",
        body=[T.R1_NEEDS_OPENING, *needs_items, _action(T.R1_ACTION_FOCUS["needs"], "act")],
        cards=[
            _card(
                "r1-needs-01",
                "双方的核心需求由各自日主与喜忌决定",
                f"乾造日主 {male.day_master}（喜 {'/'.join(male.favorable_elements)}）；"
                f"坤造日主 {female.day_master}（喜 {'/'.join(female.favorable_elements)}）",
                plain_src,
                "medium",
            )
        ],
    )

    # 吸引力与互补 ----------------------------------------------------------
    comp_bullets = [
        f"{view.label} · {cell.name}：{'、'.join(e.element for e in cell.elements)}"
        for view in result.complement.views
        for cell in view.cells
        if cell.elements
    ]
    comp_body = [T.R1_COMPLEMENT_OPENING]
    if not comp_bullets:
        comp_body.append(T.R1_COMPLEMENT_NONE)
    comp_body.append(_action(T.R1_ACTION_FOCUS["complement"], "act"))
    complement = _section(
        "complement",
        T.REPORT_SECTION_NAMES["r1"]["complement"],
        "chapter",
        body=comp_body,
        bullets=comp_bullets,
        cards=[
            _card(
                "r1-complement-01",
                complement_brief,
                f"互补图 {len([c for v in result.complement.views for c in v.cells if c.elements])} 格有元素落点",
                plain_src,
                "medium",
            )
        ],
    )

    # 冲突升级链 ------------------------------------------------------------
    negatives = [f for f in result.fired if f.delta < 0]
    issues = "、".join(f"{f.label}（{f.reading}）" for f in negatives[:3]) or T.R1_RISK_NONE
    pattern = _r1_conflict_pattern(male.favorable_elements, female.favorable_elements)
    trigger_lines = [T.R1_CONFLICT_TRIGGERS[family] for family in _hit_families(result) if family in T.R1_CONFLICT_TRIGGERS]
    conflict = _section(
        "conflict",
        T.REPORT_SECTION_NAMES["r1"]["conflict"],
        "chapter",
        body=[
            T.R1_CONFLICT_OPENING.format(issues=issues),
            T.R1_CONFLICT_ESCALATION.format(pattern=pattern),
            *trigger_lines,
            _action(T.R1_ACTION_FOCUS["conflict"], "observe"),
        ],
        cards=[
            _card(
                "r1-conflict-01",
                issues if negatives else "盘面没有常规扣分项",
                f"账本负分 {len(negatives)} 条，最负一条 {min((f.delta for f in negatives), default=0)}",
                rules_src,
                "high",
            )
        ],
    )

    # 修复脚本 --------------------------------------------------------------
    own_need = _need_for(male.favorable_elements, male.unfavorable_elements)["need"]
    partner_need = _need_for(female.favorable_elements, female.unfavorable_elements)["need"]
    scripts = _section(
        "scripts",
        T.REPORT_SECTION_NAMES["r1"]["scripts"],
        "chapter",
        body=[
            T.R1_SCRIPT_STEPS["step1"],
            T.R1_SCRIPT_STEPS["step2"].format(own_need=own_need, partner_need=partner_need),
            T.R1_SCRIPT_STEPS["step3"].format(signal="一句你们共同认的暗号"),
            _action(T.R1_ACTION_FOCUS["scripts"], "act"),
        ],
    )

    # 时间窗口 --------------------------------------------------------------
    window_body = _r1_windows(result, ref_year)
    windows = _section(
        "windows",
        T.REPORT_SECTION_NAMES["r1"]["windows"],
        "chapter",
        body=window_body,
        cards=[
            _card(
                "r1-windows-01",
                "时间窗口由两造岁运分差的同步档位派生",
                f"同频演进轴 {result.axis.start_year}–{result.axis.end_year}，"
                f"{len(result.axis.rows)} 年（含 {len([r for r in result.axis.rows if r.sync == '背离'])} 年背离）",
                rules_src,
                "high",
            )
        ],
    )

    # 长期相处约定 ----------------------------------------------------------
    yiji = _yiji_brief(result)
    agreement = _section(
        "agreement",
        T.REPORT_SECTION_NAMES["r1"]["agreement"],
        "chapter",
        body=[
            T.R1_AGREEMENT_OPENING.format(agreement=T.R1_AGREEMENT_ITEMS["boundary"]),
            T.R1_AGREEMENT_ITEMS["rhythm"],
            T.R1_AGREEMENT_ITEMS["household"],
            T.R1_AGREEMENT_ITEMS["yiji"].format(yiji=yiji),
            _action(T.R1_ACTION_FOCUS["agreement"], "act"),
        ],
    )

    # 证据附录与边界声明 -----------------------------------------------------
    evidence = _section(
        "evidence",
        T.REPORT_SECTION_NAMES["r1"]["evidence"],
        "evidence",
        body=[T.EVIDENCE_SUMMARY_OPENING],
        bullets=_evidence_summary([summary, needs, complement, conflict, windows, agreement]),
    )
    boundary = _section(
        "boundary",
        T.REPORT_SECTION_NAMES["r1"]["boundary"],
        "boundary",
        body=[T.BOUNDARY_STATEMENTS["r1"]],
    )

    return _document("r1", request, [summary, needs, complement, conflict, scripts, windows, agreement, evidence, boundary],
                     input_summary=f"乾造 {male.four_pillars}（{male.zodiac}）· 坤造 {female.four_pillars}（{female.zodiac}）",
                     boundary_text=T.BOUNDARY_STATEMENTS["r1"])


# ---------------------------------------------------------------------------
# R2 本命使用说明书：装配 compute_bazi_chart 的结果
# ---------------------------------------------------------------------------


def _compose_r2(request: BaziNatalRequest, reference_date: date | None) -> ReportDocument:
    chart = compute_bazi_chart(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=chart_longitude(request.city, request.longitude, request.apply_true_solar_time),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        reference_date=reference_date,
        name=request.name,
    )
    tables = _table_names(chart.provenance.tables) if chart.provenance else []
    rules_src = _pick_table(tables, "rules") or (tables[0] if tables else "本命盘")
    analysis = chart.analysis
    favorable = analysis.favorable_elements or [chart.day_master_element]
    unfavorable = analysis.unfavorable_elements or _other_elements(chart.day_master_element)
    top = _top_wuxing(chart)
    low = _low_wuxing(chart)
    need = _need_for(favorable, unfavorable)

    driver_line = T.R2_DRIVER_OPENING.format(
        day_master=chart.day_master,
        element=chart.day_master_element,
        favorable="、".join(favorable),
        unfavorable="、".join(unfavorable),
    )
    level_line = {
        "strong": T.R2_DRIVER_STRONG,
        "weak": T.R2_DRIVER_WEAK,
        "balanced": T.R2_DRIVER_BALANCED,
    }.get(analysis.level, T.R2_DRIVER_BALANCED)
    stress_line = T.R2_STRESS_OPENING.format(
        map=f"{T.R2_STRESS_EXCESS[top['element']]} {T.R2_STRESS_MISSING[low['element']]}"
    )
    energy_line = (
        T.R2_ENERGY_FAVORABLE[favorable[0]] + T.R2_ENERGY_UNFAVORABLE[unfavorable[0]]
    )

    summary = _section(
        "summary",
        T.REPORT_SECTION_NAMES["r2"]["summary"],
        "summary",
        bullets=[
            f"{T.R2_SUMMARY_LABELS['driver']}：{driver_line} {level_line}",
            f"{T.R2_SUMMARY_LABELS['stress']}：{stress_line}",
            f"{T.R2_SUMMARY_LABELS['practice']}：{need['need']}",
        ],
        cards=[
            _card(
                "r2-summary-01",
                level_line,
                f"日主 {chart.day_master}，旺弱档位 {analysis.label}（{analysis.level}）",
                rules_src,
                "high",
            )
        ],
    )

    driver = _section(
        "driver",
        T.REPORT_SECTION_NAMES["r2"]["driver"],
        "chapter",
        body=[driver_line, level_line, _action(T.R2_ACTION_FOCUS["driver"], "act")],
        bullets=[f"{w.element}：{w.count} 字（加权 {w.score}）" for w in chart.wuxing],
        cards=[
            _card(
                "r2-driver-01",
                "核心驱动力由日主旺弱与喜忌决定",
                f"旺弱档位 {analysis.label}（{analysis.strength.value} 分，"
                f"临界 {'是' if analysis.borderline else '否'}）；喜 {favorable} / 忌 {unfavorable}",
                rules_src,
                "high",
            )
        ],
    )

    stress = _section(
        "stress",
        T.REPORT_SECTION_NAMES["r2"]["stress"],
        "chapter",
        body=[
            stress_line,
            _action(T.R2_ACTION_FOCUS["stress"], "observe"),
        ],
        cards=[
            _card(
                "r2-stress-01",
                f"压力反应与最旺五行（{top['element']}）和最缺五行（{low['element']}）相关",
                f"五行分布：{_wuxing_summary(chart)}",
                rules_src,
                "medium",
            )
        ],
    )

    energy = _section(
        "energy",
        T.REPORT_SECTION_NAMES["r2"]["energy"],
        "chapter",
        body=[
            T.R2_ENERGY_OPENING.format(advice=energy_line),
            T.R2_ENERGY_SIGNALS,
            _action(T.R2_ACTION_FOCUS["energy"], "act"),
        ],
        cards=[
            _card(
                "r2-energy-01",
                "工作节奏宜贴合喜用五行",
                f"喜用主行：{favorable[0]}；忌神主行：{unfavorable[0]}",
                rules_src,
                "medium",
            )
        ],
    )

    relationships = _section(
        "relationships",
        T.REPORT_SECTION_NAMES["r2"]["relationships"],
        "chapter",
        body=[
            T.R2_RELATIONSHIP_OPENING.format(
                needs=need["need"], blindspots=need["blind"]
            ),
            _action(T.R2_ACTION_FOCUS["relationships"], "act"),
        ],
        cards=[
            _card(
                "r2-relationships-01",
                f"关系里更需要{need['need']}",
                f"喜用 {favorable} / 忌 {unfavorable}",
                rules_src,
                "medium",
            )
        ],
    )

    #: R2 §6 的 {area} 填充值：喜用五行 → 建议关注的生活领域。模板用 `{area} 相关的活动`
    #: 与「做 {area} 里」两种句式，领域名按词填入即可自然成立（本地模型参数，PRD §3A.3）。
    experiments = _section(
        "experiments",
        T.REPORT_SECTION_NAMES["r2"]["experiments"],
        "chapter",
        body=[f"三个 30 天小实验都以你的喜用（{favorable[0]}）为关注点，可记录、可推翻："],
        bullets=[
            f"{e['title']}：{e['body'].replace('{area}', area)} {e['verify'].replace('{area}', area)} {e['falsify']}"
            for e in T.R2_EXPERIMENTS
            for area in [_r2_focus_area(favorable)]
        ],
    )

    evidence = _section(
        "evidence",
        T.REPORT_SECTION_NAMES["r2"]["evidence"],
        "evidence",
        body=[T.EVIDENCE_SUMMARY_OPENING],
        bullets=_evidence_summary([summary, driver, stress, energy, relationships]),
    )
    boundary = _section(
        "boundary",
        T.REPORT_SECTION_NAMES["r2"]["boundary"],
        "boundary",
        body=[T.BOUNDARY_STATEMENTS["r2"]],
    )

    return _document(
        "r2",
        request,
        [summary, driver, stress, energy, relationships, experiments, evidence, boundary],
        input_summary=f"{chart.four_pillars}（{chart.zodiac}）",
        boundary_text=T.BOUNDARY_STATEMENTS["r2"],
    )


# ---------------------------------------------------------------------------
# R3 未来12个月时间地图：装配 compute_transit 的结果
# ---------------------------------------------------------------------------


def _compose_r3(request: BaziTransitRequest, reference_date: date | None) -> ReportDocument:
    ref_date = reference_date or date.today()
    start_year = request.start_year or ref_date.year
    end_year = request.end_year or start_year + 1
    focus_year = request.focus_year or start_year
    result = compute_transit(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=chart_longitude(request.city, request.longitude, request.apply_true_solar_time),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        start_year=start_year,
        end_year=end_year,
        focus_year=focus_year,
        reference_date=reference_date,
        name=request.name,
    )
    tables = _table_names(result.provenance.tables)
    rules_src = _pick_table(tables, "transit_rules") or _pick_table(tables, "plain") or tables[0]
    plain_src = _pick_table(tables, "plain") or rules_src

    best = max(result.years, key=lambda y: y.score.value)
    worst = min(result.years, key=lambda y: y.score.value)
    months = _month_tone_brief(result)

    summary = _section(
        "summary",
        T.REPORT_SECTION_NAMES["r3"]["summary"],
        "summary",
        bullets=[
            f"{T.R3_SUMMARY_LABELS['theme']}：{result.verdict.headline}",
            f"{T.R3_SUMMARY_LABELS['windows']}：{best.year}（{best.score.value:.0f} 分）",
            f"{T.R3_SUMMARY_LABELS['low']}：{worst.year}（{worst.score.value:.0f} 分）",
        ],
        cards=[
            _card(
                "r3-summary-01",
                result.verdict.headline,
                f"区间 {result.start_year}–{result.end_year} 逐年账本，档位 {result.verdict.grade}（{result.verdict.stars} 星）",
                rules_src,
                "high",
            )
        ],
    )

    months_body = [T.R3_MONTH_OPENING.format(tones="；".join(
        f"{k}（{'、'.join(v)}）" for k, v in months.items() if v
    ))]
    if result.focus_year is not None and result.years:
        focus = next((y for y in result.years if y.year == result.focus_year), None)
        if focus is not None and focus.months is not None:
            months_body.append(T.R3_MONTH_FOOTER)
        else:
            months_body.append(T.R3_FOCUS_NONE)
    else:
        months_body.append(T.R3_FOCUS_NONE)
    month_section = _section(
        "months",
        T.REPORT_SECTION_NAMES["r3"]["months"],
        "chapter",
        body=months_body,
        bullets=[f"{m['month_in_chinese']}月（{m['ganzhi']}）：{T.R3_MONTH_TONES[_month_tone(m['score']['value'])]}"
                 for m in _focus_months(result)],
        cards=[
            _card(
                "r3-months-01",
                "逐月节奏由流月账本分数分档",
                f"{focus_year} 年十二节气流月账本（{len(_focus_months(result))} 个月）",
                plain_src,
                "high",
            )
        ],
    )

    high = [m["month_in_chinese"] for m in _focus_months(result) if _month_tone(m["score"]["value"]) == "push"]
    low = [m["month_in_chinese"] for m in _focus_months(result) if _month_tone(m["score"]["value"]) in ("wrap", "rest")]
    windows = _section(
        "windows",
        T.REPORT_SECTION_NAMES["r3"]["windows"],
        "chapter",
        body=[
            T.R3_WINDOW_HIGH.format(months="、".join(high) or "—"),
            T.R3_WINDOW_LOW.format(months="、".join(low) or "—"),
            T.R3_WINDOW_FOOTER,
        ],
    )

    actions = _section(
        "actions",
        T.REPORT_SECTION_NAMES["r3"]["actions"],
        "action",
        bullets=[
            T.R3_ACTION_TEMPLATE.format(window=f"{m['month_in_chinese']}月", action=T.R3_ACTIONS[_month_tone(m["score"]["value"])])
            for m in _focus_months(result)
        ][:12],
    )

    review = _section(
        "review",
        T.REPORT_SECTION_NAMES["r3"]["review"],
        "chapter",
        body=[T.R3_REVIEW_OPENING],
        bullets=list(T.R3_REVIEW_ITEMS),
    )

    evidence = _section(
        "evidence",
        T.REPORT_SECTION_NAMES["r3"]["evidence"],
        "evidence",
        body=[T.EVIDENCE_SUMMARY_OPENING],
        bullets=_evidence_summary([summary, month_section, windows]),
    )
    boundary = _section(
        "boundary",
        T.REPORT_SECTION_NAMES["r3"]["boundary"],
        "boundary",
        body=[T.BOUNDARY_STATEMENTS["r3"]],
    )

    return _document(
        "r3",
        request,
        [summary, month_section, windows, actions, review, evidence, boundary],
        input_summary=f"{result.four_pillars} · 区间 {result.start_year}–{result.end_year}",
        boundary_text=T.BOUNDARY_STATEMENTS["r3"],
    )


# ---------------------------------------------------------------------------
# 装配辅助
# ---------------------------------------------------------------------------


def _document(
    product: ReportProduct,
    request,
    sections: list[ReportSection],
    input_summary: str,
    boundary_text: str,
) -> ReportDocument:
    settings = get_settings()
    now = datetime.now()
    order_id = derive_order_id(product, request)
    return ReportDocument(
        order_id=order_id,
        product=product,
        title=T.REPORT_PRODUCTS[product]["title"],
        tagline=T.REPORT_PRODUCTS[product]["tagline"],
        version=T.REPORT_VERSION,
        generated_date=now.date().isoformat(),
        input_summary=input_summary,
        sections=sections,
        boundary=boundary_text,
        token=sign_token(settings.report_secret, product, order_id, now),
        expires_at=expires_at_for(now, settings.report_link_ttl_hours),
    )


def _section(section_id: str, title: str, kind: str, body=None, bullets=None, cards=None) -> ReportSection:
    return ReportSection(
        id=section_id,
        title=title,
        kind=kind,
        body=body or [],
        bullets=bullets or [],
        evidence_cards=cards or [],
    )


def _card(claim_id: str, claim: str, chart_fact: str, source: str, confidence: str) -> ReportEvidenceCard:
    return ReportEvidenceCard(
        claim_id=claim_id,
        claim=claim,
        chart_fact=chart_fact,
        source=source,
        confidence=confidence,
        falsifier=T.EVIDENCE_FALSIFIER.format(claim=claim, basis=chart_fact),
    )


def _action(focus: str, mode: str) -> str:
    """一章的行动句：模板（act/observe/avoid）+ 该章关注点。"""
    return T.ACTION_TEMPLATES[mode].format(action=focus, signal=focus, avoid=focus)


def _table_names(tables) -> list[str]:
    return [t.name for t in tables] if tables else []


def _pick_table(names: list[str], fragment: str) -> str | None:
    return next((n for n in names if fragment in n), None)


def _r1_complement_brief(result: BaziHehunResult) -> str:
    """摘要里的「最大互补」：优先补格，其次阙格；都没有就落在整体差异上。"""
    parts = []
    for view in result.complement.views:
        for cell in view.cells:
            if cell.name in ("补", "阙") and cell.elements:
                parts.append(
                    f"{view.label}：{'、'.join(e.element for e in cell.elements)}"
                )
                break
    return "；".join(parts) or T.R1_COMPLEMENT_NONE


def _r1_top_risk(result: BaziHehunResult) -> str:
    negatives = [f for f in result.fired if f.delta < 0]
    if not negatives:
        return T.R1_RISK_NONE
    worst = min(negatives, key=lambda f: f.delta)
    return f"{worst.label}（{worst.reading}）"


def _hit_families(result: BaziHehunResult) -> set[str]:
    return {f.family for f in result.fired}


def _r1_conflict_pattern(male_fav: list[str], female_fav: list[str]) -> str:
    """谁先退、谁先追：按两造喜用重叠度映射（喜忌互补越少，立场越容易顶住）。"""
    overlap = len(set(male_fav) & set(female_fav))
    if overlap == 0:
        return T.R1_CONFLICT_PATTERN_HIGH
    if overlap >= 2:
        return T.R1_CONFLICT_PATTERN_LOW
    return T.R1_CONFLICT_PATTERN_MID


def _r1_windows(result: BaziHehunResult, ref_year: int) -> list[str]:
    """未来 12 个月（参考年起两年）的低同步与高同步年份。"""
    window = [r for r in result.axis.rows if ref_year <= r.year <= ref_year + 1]
    if not window:
        return [T.R1_WINDOW_NONE]
    low = [r for r in window if r.sync == "背离"]
    good = [r for r in window if r.sync == "同频" and r.male.value >= 50 and r.female.value >= 50]
    lines = []
    lines.append(
        T.R1_WINDOW_OPENING.format(
            years="、".join(f"{r.year}（{r.sync}）" for r in low) or T.R1_WINDOW_NONE
        )
    )
    lines.append(
        T.R1_WINDOW_GOOD.format(
            years="、".join(f"{r.year}" for r in good) or "—"
        )
    )
    lines.append(T.R1_WINDOW_FOOTER)
    return lines


def _yiji_brief(result: BaziHehunResult) -> str:
    """同宜组的五行，作为「能量互补活动」的填充。"""
    for group in result.yi_ji.groups:
        if group.kind == "同宜" and group.items:
            return "、".join(i.element for i in group.items)
    return "木、火、土、金、水"


def _need_for(favorable: list[str], unfavorable: list[str]) -> dict[str, str]:
    """按喜用主行取「需要什么 / 容易误读什么」的短句（模板在 R2 命名空间，跨产品复用）。"""
    fav = favorable[0] if favorable else "木"
    unf = unfavorable[0] if unfavorable else "金"
    return {
        "need": T.R2_RELATIONSHIP_NEEDS.get(fav, "被理解与尊重"),
        "blind": T.R2_RELATIONSHIP_BLIND.get(unf, "容易按自己的节奏理解对方"),
    }


def _top_wuxing(chart: BaziChart) -> dict[str, object]:
    return {"element": max(chart.wuxing, key=lambda w: w.score).element}


def _low_wuxing(chart: BaziChart) -> dict[str, object]:
    return {"element": min(chart.wuxing, key=lambda w: w.score).element}


def _wuxing_summary(chart: BaziChart) -> str:
    return " ".join(f"{w.element}{w.score}" for w in chart.wuxing)


def _other_elements(day_master_element: str) -> list[str]:
    return [e for e in ("木", "火", "土", "金", "水") if e != day_master_element]


def _month_tone(value: float) -> str:
    """流月分档：阈值见 `_MONTH_TONE_THRESHOLDS`（65 推进 / 50 谈判 / 35 收尾 / 余休整）。"""
    if value >= _MONTH_TONE_THRESHOLDS[0]:
        return "push"
    if value >= _MONTH_TONE_THRESHOLDS[1]:
        return "negotiate"
    if value >= _MONTH_TONE_THRESHOLDS[2]:
        return "wrap"
    return "rest"


def _r2_focus_area(favorable: list[str]) -> str:
    """R2 §6 实验的关注领域：喜用主行 → 生活领域名，供模板 `{area}` 填空。"""
    return {
        "木": "成长与学习",
        "火": "表达与社交",
        "土": "稳定推进的工作",
        "金": "秩序与执行",
        "水": "沟通与流动",
    }.get(favorable[0] if favorable else "", "日常生活")


def _focus_months(result: BaziTransitResult) -> list[dict]:
    """聚焦年（focus_year）的十二节气流月；未展开时返回空。"""
    if result.focus_year is None:
        return []
    for year in result.years:
        if year.year == result.focus_year and year.months is not None:
            return [m.model_dump() for m in year.months]
    return []


def _month_tone_brief(result: BaziTransitResult) -> dict[str, list[str]]:
    """逐月节奏按分档归组（推进/谈判/收尾/休整），供摘要与 months 章共用。"""
    grouped: dict[str, list[str]] = {"push": [], "negotiate": [], "wrap": [], "rest": []}
    for m in _focus_months(result):
        grouped[_month_tone(m["score"]["value"])].append(m["month_in_chinese"])
    return grouped


def _evidence_summary(sections: list[ReportSection]) -> list[str]:
    """证据附录的汇总条目：每章首卡一行（结论 → 依据 → 出处）。"""
    lines = []
    for section in sections:
        for card in section.evidence_cards[:1]:
            lines.append(f"{section.title}：{card.claim}（依据：{card.chart_fact}；{card.source}）")
    return lines
