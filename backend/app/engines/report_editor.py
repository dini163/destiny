"""Organise model factors into conditional readings without inventing personal history."""

from app.content import report_guidance as G


def enrich_natal(sections, chart):
    by_id = {section.id: section for section in sections}
    condition = G.R2_CONDITIONS.get(chart.analysis.level, G.R2_CONDITIONS["balanced"])
    by_id["driver"].body.extend(condition[1:])
    by_id["summary"].bullets.insert(0, f"先看重点：{condition[0]}")
    by_id["stress"].body.extend(G.R2_STRESS_CONTEXT)
    by_id["energy"].body.extend(G.R2_ENERGY_CONTEXT)
    by_id["relationships"].body.extend(G.R2_RELATION_CONTEXT)
    dimensions = chart.interpretation.six_dimensions if chart.interpretation else []
    body = [by_id["dimensions"].body[0]]
    for dimension in dimensions:
        if dimension.strengths and dimension.cautions:
            interpretation = G.R2_DIMENSION_MIXED
        elif dimension.strengths:
            interpretation = G.R2_DIMENSION_POSITIVE
        else:
            interpretation = G.R2_DIMENSION_NEGATIVE
        body.append(f"【{dimension.dimension}】{interpretation}")
    body.append(G.R2_DIMENSION_CHECK)
    by_id["dimensions"].body = body
    return sections
