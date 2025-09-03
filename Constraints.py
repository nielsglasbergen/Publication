# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 13:04:36 2025

@author: Niels
"""
import pyomo.environ as pe
from KPI_formulas import div_expr_func, cover_expr_func, cr_expr_func, n_expr_func, eos_expr_func, \
     profit_with_kpi_subsidy, profit_expr_func

def constraints(model):
    
    ## Constraint for the max area
    model.ConA = pe.ConstraintList()
    for m in model.M:
        for f in model.F:
            for y in model.Y:
                expr = sum(model.x[c, y, f] * model.p_cym[c, y, m] for c in model.C) <= model.f_A[f]
                model.ConA.add(expr)
                
    model.ConA_Y1Y4 = pe.ConstraintList()
    for m_local in range(1, 13):  # month 1 t/m 12
        m_y1 = m_local            # year 1 → months 1–12
        m_y4 = m_local + 48       # year 4 → months 37–48
        for f in model.F:
            expr = sum(model.x[c, model.Y.first(), f] * model.p_cym[c, model.Y.first(), m_y1] for c in model.C) + \
                   sum(model.x[c, model.Y.last(), f] * model.p_cym[c, model.Y.last(), m_y4] for c in model.C) \
                   <= model.f_A[f]
            model.ConA_Y1Y4.add(expr)

         
    ## Constraint for z
    model.ConMinA_upper = pe.ConstraintList()
    for c in model.C:
        for y in model.Y:
            for f in model.F:
                    expr= model.f_A[f]*model.z[c,y,f] >= model.x[c, y, f]
                    model.ConMinA_upper.add(expr)

    ## Constraint for min area               
    model.ConMinA_lower = pe.ConstraintList()
    for c in model.C:
        for y in model.Y:
            for f in model.F:
                 
                    expr = model.x[c, y, f] >= model.min_A*model.z[c,y,f]
                    model.ConMinA_lower.add(expr)
                
    ## Rotation constraint (min 1:3 GEAC)
    model.ConRot = pe.ConstraintList()
    for c in model.C:
        for y in model.Y:
            for f in model.F:
                        expr = model.x[c, y, f] <= model.rotm * model.f_A[f]
                        model.ConRot.add(expr)
                    

    ## First this was different due to different restriction, however, 
    ## according to manual for agriculture they all obey 1:5
    model.ConPotatoRotation_NonSand = pe.ConstraintList()
    for f in [2]:
        for y in model.Y:  
             
                expr = sum(
                    model.x[c, y, f]
                    for c in {"seed potatoes", "starch potatoes", "consumer potatoes"}
                  
                )
                model.ConPotatoRotation_NonSand.add(expr <= ((1/3)*model.f_A[f]))

    model.ConPotatoRotation_Sand = pe.ConstraintList()

    for f in [1]:  
        for y in model.Y: 
                expr = sum(
                    model.x[c, y, f]
                    for c in {"seed potatoes"}
                )
                model.ConPotatoRotation_Sand.add(expr <= ((1/4)*model.f_A[f]))

    ## According to manual, farmers should 1:5 sugar beets
    model.ConBeets = pe.ConstraintList()
    for f in model.F:
        for y in model.Y:
            expr = sum(
                model.x[c, y, f]
                for c in {"sugar beets"}
                )
            model.ConBeets.add(expr <= ((1/4)*model.f_A[f]))
    
    ## Agriculture rule that restricts at least 1:4 should be rest crop
    model.ConCR = pe.ConstraintList()
    for f in [1]:
        for y in model.Y:
             
                expr = sum(model.x[c, y, f] for c in model.CR)
                model.ConCR.add (expr>=model.f_A[f]*(1/4))
                    
    # Nitrogen restriction rule
    model.ConN = pe.ConstraintList()
    for f in [1]:
        soil = model.f_soil[f]
        for y in model.Y:
            expr = sum(model.x[c,y,f]*model.N_fertilizer[c, soil] \
                       for c in model.C if (c, soil) in model.N_fertilizer)/model.f_A[f] <= 110
            model.ConN.add(expr)
    
    model.ConN2 = pe.ConstraintList()
    for f in [2]:
        soil = model.f_soil[f]
        for y in model.Y:
            expr = sum(model.x[c,y,f]*model.N_fertilizer[c, soil] \
                       for c in model.C if (c, soil) in model.N_fertilizer)/model.f_A[f] <= 110
            model.ConN2.add(expr)
    
            
   
    model.ConMaize = pe.ConstraintList()
    for f in [1]:
        soil = model.f_soil[f]
        for y in model.Y:
            expr = model.x['silage maize',y,f] >= (3/10)*model.f_A[f]
            model.ConMaize.add(expr)
               
    model.ConSeedPot = pe.ConstraintList()
    for f in model.F:
        soil = model.f_soil[f]
        for y in model.Y:
            expr = model.x['seed potatoes',y,f] <= (1/10)*model.f_A[f]
            model.ConSeedPot.add(expr)
    
    model.ConWinterWheat = pe.ConstraintList()
    for f in [2]:
        soil= model.f_soil[f]
        for y in model.Y:
            expr = model.x['winter wheat', y,f] >= (2/10)*model.f_A[f]
            model.ConWinterWheat.add(expr)
    
    model.ConOnion = pe.ConstraintList()
    for f in [1]:
        soil = model.f_soil[f]
        for y in model.Y:
            expr = model.x['seed onions',y,f] <= (1/25)*model.f_A[f]
            model.ConOnion.add(expr)
    
    model.ConOnion2 = pe.ConstraintList()
    for f in [2]:
        soil = model.f_soil[f]
        for y in model.Y:
            expr = model.x['seed onions',y,f] <= (1/20)*model.f_A[f]
            model.ConOnion2.add(expr)
    
    
    ## Validation to ensure no impossible (without score) crop soil combinations
    model.ConValidCropSoil = pe.ConstraintList()
    for f in model.F:
        soil = model.f_soil[f]
        for y in model.Y:
            for c in model.C:
                valid = (
                    (soil, c) in model.gross_margin and
                    (c, soil) in model.N_fertilizer and
                    (c, soil) in model.N_content and
                    (c, soil) in model.yield_kg_ha
                )
                if not valid:
                    model.ConValidCropSoil.add(model.z[c, y, f] == 0)
    return model


"""Fix the current crop plan, to eventually add other crops to make a full 100%"""
def fix_total_crop_area_constraints(model):
    model.ConTotalCropArea = pe.ConstraintList()

    for f in model.F:
        soil = model.f_soil[f]
        area_farm = model.f_A[f]

        for (s, c), perc in model.current_plan.items():
            if s == soil and perc > 0.001:
                totaal_ha = (perc / 100) * area_farm * len(model.Y)
                print(f"Tot area of soil: {soil} is :{totaal_ha} for crop: {c}")
                expr = sum(model.x[c, y, f] for y in model.Y)
                model.ConTotalCropArea.add(pe.inequality(totaal_ha * 0.8, expr, totaal_ha * 1.3))


    return model


def evaluate_current_plan_kpi(model):

    ## Creat dict for each KPI
    kpi_funcs = {
        "div": div_expr_func,
        "cover": cover_expr_func,
        "cr": cr_expr_func,
        "n": n_expr_func,
        "eos": eos_expr_func,
    }

    # Make a results dict
    kpi_results = {kpi: {soil: [] for soil in model.S} for kpi in list(kpi_funcs)}

    for f in model.F:
        soil = model.f_soil[f]
        for y in model.Y:
            for kpi, func in kpi_funcs.items():
                    val = pe.value(func(model, f, y))
                    kpi_results[kpi][soil].append(val)


    # Average scores over all years
    avg_results = {
        kpi: {
            soil: sum(vals) / len(vals) if vals else None
            for soil, vals in soil_dict.items()
        }
        for kpi, soil_dict in kpi_results.items()
    }
    
    if avg_results[kpi][soil] is not None:
        print(f"  {kpi}: {avg_results[kpi][soil]:.2f}")
    else:
        print(f"  {kpi}: n.v.t.")

    
    # Print
    for soil in model.S:
        print(f"\nSoil type: {soil}")
        for kpi in kpi_funcs:
            score = avg_results[kpi][soil]
            print(f"  {kpi}: {score:.2f}" if score is not None else f"  {kpi}: n.v.t.")
    
    return avg_results



    