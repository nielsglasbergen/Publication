# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 14:58:24 2025

@author: Niels
"""
### All biodiversity formulas
def div_expr_func(model, f, y):
    return sum(
        - (model.x[ c, y, f]/model.f_A[f])**2 + (model.x[c,y,f]/model.f_A[f])
        for c in model.C
    )

def cover_expr_func(model, f, y):
    return sum(
        model.x[ c, y, f] * model.p_cym[c, y, m]
        for c in model.C
        for m in model.M
        if m in range(1 + y*12, 1 + (y+1)*12)
        if (c, y, m) in model.p_cym.index_set()
    ) / (model.f_A[f] * 12)

def cr_expr_func(model, f, y):
    return sum(model.x[ c, y, f] / model.f_A[f] for c in model.CR)

def n_expr_func(model, f, y):
    total = 0
    soil = model.f_soil[f]
    for c in model.C:
        key = (c, soil)
        fert = model.N_fertilizer[key] if (key in model.N_fertilizer) else 0
        content = model.N_content[key] if (key in model.N_content) else 0
        seedlings = model.Q_seedlings[key] if (key in model.Q_seedlings) else 0
        yield_kg = model.yield_kg_ha[key] if (key in model.yield_kg_ha) else 0

        total += model.x[ c, y, f] * (fert + (content * seedlings/100) - (content * yield_kg/100))
    return total


def eos_expr_func(model, f, y):
    total = 0
    soil = model.f_soil[f]

    for c in model.C:
        if (c, soil) not in model.N_fertilizer:
            continue
        # EOS from crop residues
        crop_eos = model.x[ c, y, f] * model.eos_crops[c]
        # EOS from fertilizer
        fert_val = model.N_fertilizer[c, soil]

        fert_eos = (fert_val / (model.percentage_N_in_manure[soil]/100)) * model.eos_pig_manure * model.x[ c, y, f]
  
        total += crop_eos + fert_eos

    return total / model.f_A[f]

def profit_with_kpi_subsidy(model):
    gross_profit = sum(
        model.x[c, y, f] * model.gross_margin[(model.f_soil[f], c)]
        for c in model.C for y in model.Y for f in model.F
        if (model.f_soil[f], c) in model.gross_margin
    )

    subsidy_total = sum(
        model.kpi_met[f, y, kpi] * model.subsidy[model.f_soil[f], kpi] * model.f_A[f]
        for f in model.F for y in model.Y for kpi in model.KPI
    )

    return gross_profit + subsidy_total

def profit_expr_func(model):
    return sum(
        model.x[ c, y, f] * model.gross_margin[(model.f_soil[f], c)]
        for c in model.C for y in model.Y for f in model.F
        if (model.f_soil[f], c) in model.gross_margin)

 