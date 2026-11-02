"""付费报告装配器：把既有引擎算好的盘面事实装配成报告（v2.1 §3A）。

职责边界（与 AGENTS.md 第 1/6/9 条对齐）：

1. **不重算历法/星历**：三份报告分别调用 `compute_hehun` / `compute_bazi_chart` /
   `compute_transit`，只消费它们返回的结构化事实（分数、柱、命中、白话）。
2. **不现编文案**：所有句子来自 `content/report_templates.py` 的受控模板 + 盘面事实填空；
   装配器只做「选哪句模板、填什么事实」，不写无来源断言。
3. **每条结论必须有依据**：每章关键结论配一张 `ReportEvidenceCard`（结论/盘面事实/出处/
   可推翻句三分离，PRD §3A.1 原则 3）。
4. **计算与交付分开**：本模块只装配内容与内测凭据；人工交付在 core/report_store.py
   保存固定快照与独立随机标识，后续读取不再依赖当前模板。

报告版本与受控框架在 content/report_templates.py；生活观察材料在 content/report_guidance.py。
改动解释内容时递增报告版本，已交付快照不重算。
"""

from datetime import date, datetime, timezone

from app.content import report_guidance as G
from app.content import report_templates as T
from app.core.chart_input import chart_longitude
from app.core.config import get_settings
from app.core.report_orders import derive_order_id, expires_at_for, sign_token
from app.engines.bazi import compute_bazi_chart
from app.engines.bazi_hehun import compute_hehun
from app.engines.bazi_transit import compute_transit
from app.engines.report_calendar import rolling_months
from app.engines.report_editor import enrich_natal
from app.schemas.bazi import BaziChart, BaziNatalRequest
from app.schemas.bazi_hehun import BaziHehunRequest, BaziHehunResult
from app.schemas.bazi_transit import BaziTransitRequest
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
        can_generate=get_settings().app_environment != "production",
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
        body=[
            T.R1_NEEDS_OPENING,
            *needs_items,
            *(
                [G.R1_STAGE_CONTEXT[request.relationship_stage]]
                if getattr(request, "relationship_stage", "unspecified") in G.R1_STAGE_CONTEXT
                else []
            ),
            _action(T.R1_ACTION_FOCUS["needs"], "act"),
        ],
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
        f"{view.label} · {cell.name}（{'、'.join(e.element for e in cell.elements)}）：{G.R1_COMPLEMENT_EXPLANATION[cell.name]}"
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
    issues = (
        "、".join(f.label for f in sorted(negatives, key=lambda row: row.delta)[:3])
        or T.R1_RISK_NONE
    )
    pattern = G.R1_PATTERN_BOUNDARY
    trigger_lines = [
        T.R1_CONFLICT_TRIGGERS[family]
        for family in sorted({row.family for row in negatives})
        if family in T.R1_CONFLICT_TRIGGERS
    ]
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
            *(
                line.format(own_need=own_need, partner_need=partner_need)
                for line in G.R1_REPAIR_SCENARIOS
            ),
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

    return _document(
        "r1",
        request,
        [summary, needs, complement, conflict, scripts, windows, agreement, evidence, boundary],
        input_summary=f"乾造 {male.four_pillars}（{male.zodiac}）· 坤造 {female.four_pillars}（{female.zodiac}）",
        boundary_text=T.BOUNDARY_STATEMENTS["r1"],
    )


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
    interp = chart.interpretation
    verdict = interp.verdict if interp else None
    dims = interp.six_dimensions if interp else []

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
        map=(
            _strip_end(T.R2_STRESS_EXCESS[top["element"]])
            + "，"
            + _strip_end(T.R2_STRESS_MISSING[low["element"]])
        )
    )
    energy_line = (
        _strip_end(T.R2_ENERGY_FAVORABLE[favorable[0]])
        + "；"
        + _strip_end(T.R2_ENERGY_UNFAVORABLE[unfavorable[0]])
    )

    summary_bullets = []
    if verdict is not None:
        summary_bullets.append(
            f"{T.R2_SUMMARY_LABELS['overall']}：{verdict.grade}（{verdict.stars} 星）{verdict.headline}"
        )
    summary_bullets.append(f"{T.R2_SUMMARY_LABELS['driver']}：{driver_line} {level_line}")
    dim_brief = _r2_dimension_brief(dims)
    if dim_brief:
        summary_bullets.append(f"{T.R2_SUMMARY_LABELS['dimensions']}：{dim_brief}")
    summary_bullets.append(f"{T.R2_SUMMARY_LABELS['stress']}：{stress_line}")
    summary_bullets.append(f"{T.R2_SUMMARY_LABELS['practice']}：{need['need']}")

    summary_cards = [
        _card(
            "r2-summary-01",
            level_line,
            f"日主 {chart.day_master}，旺弱档位 {analysis.label}（{analysis.level}）",
            rules_src,
            "high",
        )
    ]
    if verdict is not None:
        summary_cards.append(
            _card(
                "r2-summary-verdict",
                verdict.headline,
                f"整体 {verdict.grade}（{verdict.stars} 星），由六维账本均值派生",
                rules_src,
                "high",
            )
        )
    summary = _section(
        "summary",
        T.REPORT_SECTION_NAMES["r2"]["summary"],
        "summary",
        bullets=summary_bullets,
        cards=summary_cards,
    )

    profile = _r2_profile_section(chart, favorable, unfavorable, rules_src)
    dimensions = _r2_dimensions_section(dims, rules_src)

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
                f"五行相对高项 {top['element']}、相对低项 {low['element']} 的压力观察假设",
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

    dayun = _r2_dayun_section(chart, rules_src)

    relationships = _section(
        "relationships",
        T.REPORT_SECTION_NAMES["r2"]["relationships"],
        "chapter",
        body=[
            T.R2_RELATIONSHIP_OPENING.format(
                needs=_strip_end(need["need"]), blindspots=_strip_end(need["blind"])
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
        bullets=_evidence_summary(
            [summary, profile, dimensions, driver, stress, energy, dayun, relationships]
        ),
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
        enrich_natal(
            [
                summary,
                profile,
                dimensions,
                driver,
                stress,
                energy,
                dayun,
                relationships,
                experiments,
                evidence,
                boundary,
            ],
            chart,
        ),
        input_summary=f"{chart.four_pillars}（{chart.zodiac}）",
        boundary_text=T.BOUNDARY_STATEMENTS["r2"],
    )


# ---------------------------------------------------------------------------
# R3 未来12个月时间地图：装配 compute_transit 的结果
# ---------------------------------------------------------------------------


def _compose_r3(request: BaziTransitRequest, reference_date: date | None) -> ReportDocument:
    # Keep the original interval validation; report dates do not silently excuse invalid chart input.
    ref = reference_date or date.today()
    compute_transit(
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        calendar=request.calendar,
        longitude=chart_longitude(request.city, request.longitude, request.apply_true_solar_time),
        gender=request.gender,
        apply_true_solar_time=request.apply_true_solar_time,
        start_year=request.start_year,
        end_year=request.end_year,
        focus_year=request.focus_year,
        reference_date=ref,
        name=request.name,
    )
    start, end, periods = rolling_months(request, reference_date)
    month_lines, actions, evidence_cards, high, low = [], [], [], [], []
    for index, (left, right, pieces) in enumerate(periods):
        descriptions = []
        for a, b, term in pieces:
            tone = _month_tone(term.score.value)
            monthly = [row for row in term.fired if row.key.startswith("yue.")]
            selected = sorted(monthly, key=lambda row: abs(row.delta), reverse=True)[:2]
            reasons = "；".join(f"{row.label}（账本增量 {row.delta:+g}）" for row in selected)
            if not reasons:
                reasons = "本段未命中额外流月因子，保留年度账本基准，不另编变化"
            descriptions.append(
                f"{a}—{b} · {term.ganzhi}节气月 · {G.R3_TONE_LABELS[tone]}：{reasons}"
            )
            evidence_cards.append(
                _card(
                    f"r3-month-{index}-{term.index}",
                    f"{a}—{b} 的传统模型分档为{G.R3_TONE_LABELS[tone]}",
                    f"{term.ganzhi}，原始交节区间 {term.start_solar}—{term.end_solar}，账本 {term.score.value:g} 分；{reasons}",
                    "bazi_transit_rules · report_guidance",
                    "medium",
                )
            )
        dominant = max(pieces, key=lambda piece: (piece[1] - piece[0]).days)[2]
        tone = _month_tone(dominant.score.value)
        if tone == "push":
            high.append(f"{left}—{right}")
        elif tone in ("wrap", "rest"):
            low.append(f"{left}—{right}")
        month_lines.append(f"第{index + 1}个月｜{left}—{right}：" + "。".join(descriptions))
        monthly = [row for row in dominant.fired if row.key.startswith("yue.")]
        factor = max(monthly, key=lambda row: abs(row.delta), default=None)
        focus = G.R3_FACTOR_CONTEXT.get(
            factor.family if factor else "default", G.R3_FACTOR_CONTEXT["default"]
        )
        actions.append(
            f"{left}—{right}：{T.R3_ACTIONS[tone]} {focus} {G.R3_OBSERVATIONS[index % len(G.R3_OBSERVATIONS)]}"
        )
    summary = _section(
        "summary",
        T.REPORT_SECTION_NAMES["r3"]["summary"],
        "summary",
        bullets=[
            f"报告范围：{start}—{end}，从起始日起连续十二个月，按公历月段阅读",
            "阅读方式：每个公历月段可能跨交节；分段列出实际节气边界和命中因素，不把整个月当成相同的盘面",
            f"节奏分布：{len(high)}个月段以推进为主，{len(low)}个月段以收尾或休整为主；分档不是事件概率",
        ],
    )
    month_section = _section(
        "months",
        T.REPORT_SECTION_NAMES["r3"]["months"],
        "chapter",
        body=[
            "以下按真实交节区间组合每个公历月段。分数仅用于传统模型分档；同档月份仍可能命中不同因素，不能直接推断事件。"
        ],
        bullets=month_lines,
        cards=evidence_cards,
    )
    windows = _section(
        "windows",
        T.REPORT_SECTION_NAMES["r3"]["windows"],
        "chapter",
        body=[
            "推进为主的月段："
            + ("；".join(high) or "本周期没有达到该模型分界的月段，不强造利好窗口"),
            "收尾或休整为主的月段：" + ("；".join(low) or "本周期没有落在该模型分界的月段"),
            T.R3_WINDOW_FOOTER,
        ],
    )
    action_section = _section(
        "actions", T.REPORT_SECTION_NAMES["r3"]["actions"], "action", bullets=actions
    )
    review = _section(
        "review",
        T.REPORT_SECTION_NAMES["r3"]["review"],
        "chapter",
        body=[T.R3_REVIEW_OPENING],
        bullets=T.R3_REVIEW_ITEMS,
    )
    evidence = _section(
        "evidence",
        T.REPORT_SECTION_NAMES["r3"]["evidence"],
        "evidence",
        body=[T.EVIDENCE_SUMMARY_OPENING],
        bullets=_evidence_summary([month_section]),
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
        [summary, month_section, windows, action_section, review, evidence, boundary],
        input_summary=f"滚动时段 {start}—{end}",
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
    now = datetime.now(timezone.utc)
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


def _section(
    section_id: str, title: str, kind: str, body=None, bullets=None, cards=None
) -> ReportSection:
    return ReportSection(
        id=section_id,
        title=title,
        kind=kind,
        body=[_clean_sentence(line) for line in (body or [])],
        bullets=[_clean_sentence(line) for line in (bullets or [])],
        evidence_cards=cards or [],
    )


def _card(
    claim_id: str, claim: str, chart_fact: str, source: str, confidence: str
) -> ReportEvidenceCard:
    return ReportEvidenceCard(
        claim_id=claim_id,
        claim=_clean_sentence(claim),
        chart_fact=_clean_sentence(chart_fact),
        source=source,
        confidence="medium" if confidence == "high" else confidence,
        falsifier="请先核对盘面与引用规则。若相应的生活描述不符合经历，不必认领；规则一致不等于现实预测已被验证。",
    )


def _action(focus: str, mode: str) -> str:
    """一章的行动句：模板（act/observe/avoid）+ 该章关注点。"""
    return T.ACTION_TEMPLATES[mode].format(action=focus, signal=focus, avoid=focus)


def _table_names(tables) -> list[str]:
    return [t.name for t in tables] if tables else []


def _strip_end(text: str) -> str:
    """去掉语料片段自带的句末标点，统一由框架句收尾，避免拼接出双句号。"""
    return text.rstrip("。；！？!?； ")


def _pick_table(names: list[str], fragment: str) -> str | None:
    return next((n for n in names if fragment in n), None)


def _r1_complement_brief(result: BaziHehunResult) -> str:
    """摘要里的「最大互补」：优先补格，其次阙格；都没有就落在整体差异上。"""
    parts = []
    for view in result.complement.views:
        for cell in view.cells:
            if cell.name in ("补", "阙") and cell.elements:
                parts.append(f"{view.label}：{'、'.join(e.element for e in cell.elements)}")
                break
    return "；".join(parts) or T.R1_COMPLEMENT_NONE


def _r1_top_risk(result: BaziHehunResult) -> str:
    negatives = [f for f in result.fired if f.delta < 0]
    if not negatives:
        return T.R1_RISK_NONE
    worst = min(negatives, key=lambda f: f.delta)
    return f"{worst.label}（{worst.reading}）"


def _r1_windows(result: BaziHehunResult, ref_year: int) -> list[str]:
    """Annual rows can support yearly context only, never monthly timing claims."""
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
    lines.append(T.R1_WINDOW_GOOD.format(years="、".join(f"{r.year}" for r in good) or "—"))
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


def _r2_profile_section(
    chart: BaziChart, favorable: list[str], unfavorable: list[str], rules_src: str
) -> ReportSection:
    """命格总览：四柱、月令格局（geju）、用神三法（yongshen）；只填引擎已算好的事实。"""
    body = [
        T.R2_PROFILE_OPENING.format(
            pillars=chart.four_pillars,
            day_master=chart.day_master,
            element=chart.day_master_element,
        )
    ]
    cards: list[ReportEvidenceCard] = []
    geju = chart.geju
    if geju is not None:
        notes = "；".join(geju.notes)
        if geju.is_success:
            body.append(T.R2_GEJU_SUCCESS.format(geju=geju.name, notes=notes or geju.ten_god))
        else:
            body.append(T.R2_GEJU_FAIL.format(geju=geju.name, notes=notes or "无成格判语"))
        cards.append(
            _card(
                "r2-profile-geju",
                f"月令格局 {geju.name}（{'成格' if geju.is_success else '未全成格'}）",
                notes or f"定格十神 {geju.ten_god}",
                geju.source,
                "high",
            )
        )
    else:
        body.append(T.R2_GEJU_NONE)

    ys = chart.yongshen
    if ys is not None:
        body.append(
            T.R2_YONGSHEN_OPENING.format(
                favorable="、".join(ys.favorable_elements) or "—",
                unfavorable="、".join(ys.unfavorable_elements) or "—",
            )
        )
        method_lines = []
        for m in ys.methods:
            if m.chosen_elements:
                method_lines.append(
                    T.R2_YONGSHEN_METHOD.format(
                        method=m.method, chosen="、".join(m.chosen_elements)
                    )
                )
            else:
                method_lines.append(T.R2_YONGSHEN_METHOD_NONE.format(method=m.method))
        body.append("".join(method_lines))
    body.append(T.R2_YONGSHEN_FOOTER)
    cards.append(
        _card(
            "r2-profile-yongshen",
            "喜用由扶抑/通关/调候三法合并派生",
            f"喜 {favorable} / 忌 {unfavorable}",
            rules_src,
            "medium",
        )
    )
    body.append(_action(T.R2_ACTION_FOCUS["profile"], "act"))
    return _section(
        "profile",
        T.REPORT_SECTION_NAMES["r2"]["profile"],
        "chapter",
        body=body,
        cards=cards,
    )


def _r2_dimensions_section(dims, rules_src: str) -> ReportSection:
    """六维画像：bullets 放档位/分、优势、提醒清单，body 放引擎白话整段。"""
    body = [T.R2_DIMENSIONS_OPENING]
    bullets: list[str] = []
    for d in dims:
        bullets.append(
            T.R2_DIMENSION_HEAD.format(
                dimension=d.dimension, tier=d.score.tier, score=f"{d.score.value:.0f}"
            )
        )
        if d.strengths:
            bullets.append(T.R2_DIMENSION_STRENGTHS.format(items="、".join(d.strengths)))
        if d.cautions:
            bullets.append(T.R2_DIMENSION_CAUTIONS.format(items="、".join(d.cautions)))
        if not d.strengths and not d.cautions:
            bullets.append(T.R2_DIMENSION_EMPTY_FACTOR)
    cards = []
    if dims:
        cards.append(
            _card(
                "r2-dimensions-ledger",
                "六维分数由各自账本累加，档位顺/平/滞沿用 65/45 分界",
                f"{len(dims)} 个维度；最高 {max(d.score.value for d in dims):.0f} / "
                f"最低 {min(d.score.value for d in dims):.0f}",
                rules_src,
                "high",
            )
        )
    body.append(_action(T.R2_ACTION_FOCUS["dimensions"], "act"))
    return _section(
        "dimensions",
        T.REPORT_SECTION_NAMES["r2"]["dimensions"],
        "chapter",
        body=body,
        bullets=bullets,
        cards=cards,
    )


def _r2_dayun_section(chart: BaziChart, rules_src: str) -> ReportSection:
    """当前大运：干支/年龄段/伏吟反吟关系；无有效大运时给诚实兜底句。"""
    du = chart.dayun_current
    if du is None:
        return _section(
            "dayun",
            T.REPORT_SECTION_NAMES["r2"]["dayun"],
            "chapter",
            body=[T.R2_DAYUN_NONE],
        )
    body = [T.R2_DAYUN_OPENING.format(ganzhi=du.ganzhi, start_age=du.start_age, end_age=du.end_age)]
    for r in du.relations:
        body.append(T.R2_DAYUN_RELATION.format(relation=r.kind, reading=r.reading))
    body.append(T.R2_DAYUN_FOOTER)
    body.append(_action(T.R2_ACTION_FOCUS["dayun"], "act"))
    return _section(
        "dayun",
        T.REPORT_SECTION_NAMES["r2"]["dayun"],
        "chapter",
        body=body,
        cards=[
            _card(
                "r2-dayun-current",
                f"当前大运 {du.ganzhi}（{du.start_age}–{du.end_age}岁）",
                f"与命局伏吟/反吟关系 {len(du.relations)} 条",
                rules_src,
                "high",
            )
        ],
    )


def _r2_dimension_brief(dims) -> str:
    """摘要里的六维速览：顺/平/滞计数 + 最顺/最留意维度；无六维时返回空串。"""
    if not dims:
        return ""
    counts: dict[str, int] = {}
    for d in dims:
        counts[d.score.tier] = counts.get(d.score.tier, 0) + 1
    best = max(dims, key=lambda d: d.score.value)
    weak = min(dims, key=lambda d: d.score.value)
    parts = [
        f"顺{counts.get('顺', 0)}·平{counts.get('平', 0)}·滞{counts.get('滞', 0)}",
        f"最顺 {best.dimension}（{best.score.value:.0f}）",
    ]
    if weak.score.value < best.score.value:
        parts.append(f"最留意 {weak.dimension}（{weak.score.value:.0f}）")
    return "；".join(parts)


def _r2_focus_area(favorable: list[str]) -> str:
    """R2 §6 实验的关注领域：喜用主行 → 生活领域名，供模板 `{area}` 填空。"""
    return {
        "木": "成长与学习",
        "火": "表达与社交",
        "土": "稳定推进的工作",
        "金": "秩序与执行",
        "水": "沟通与流动",
    }.get(favorable[0] if favorable else "", "日常生活")


def _evidence_summary(sections: list[ReportSection]) -> list[str]:
    """证据附录的汇总条目：每章首卡一行（结论 → 依据 → 出处）。"""
    lines = []
    for section in sections:
        for card in section.evidence_cards[:1]:
            lines.append(f"{section.title}：{card.claim}（依据：{card.chart_fact}；{card.source}）")
    return lines


def _clean_sentence(text: str) -> str:
    while "。。" in text:
        text = text.replace("。。", "。")
    return text
