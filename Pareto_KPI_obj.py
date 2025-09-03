# -*- coding: utf-8 -*-
import pyomo.environ as pe
import pyomo.opt as po
import pandas as pd
from KPI_formulas import div_expr_func, cover_expr_func, cr_expr_func, n_expr_func, eos_expr_func, \
     profit_with_kpi_subsidy, profit_expr_func
from Constraints import evaluate_current_plan_kpi

"""Pareto optimize the rotation with the base solution for each of the KPI"""

def optimize_each_kpi_as_objective(model, baseline_epsilons):
    kpi_exprs = {
        'div': div_expr_func,
        'cover': cover_expr_func,
        'cr': cr_expr_func,
        'n': n_expr_func,
        'eos': eos_expr_func,
    }
    max_kpi_objectives = {soil: {} for soil in model.S}
    results = []
    
    ## Identify the selected KPI as the objective to find the pareto optimal solution
    for target_kpi, objective_expr in kpi_exprs.items():

        # Clean old constraints
        if hasattr(model, 'epsilon_con'):
            model.del_component(model.epsilon_con)
        model.epsilon_con = pe.ConstraintList()

        # Add all of the other KPI as base constraints
        for kpi, expr_func in kpi_exprs.items():
            if kpi == target_kpi:
                continue
            for f in model.F:
                soil = model.f_soil[f]
                bound = baseline_epsilons[kpi][soil]

                for y in model.Y:
                        if kpi in ['n']:
                            model.epsilon_con.add(expr_func(model, f, y) <= bound)
                        else:
                            model.epsilon_con.add(expr_func(model, f, y) >= bound)

        # Set new objective
        if hasattr(model, 'obj'):
            model.del_component(model.obj)

        # Only min if n
        sense = pe.minimize if target_kpi in ['n'] else pe.maximize
        model.obj = pe.Objective(expr=sum(objective_expr(model, f, y) for f in model.F for y in model.Y), sense=sense)
        solver = po.SolverFactory('gurobi')
        result = solver.solve(model, tee=False)
        objective_value = pe.value(model.obj)
        soil_objective_score = {soil: 0.0 for soil in model.S}
        for f in model.F:
            soil = model.f_soil[f]
            soil_objective_score[soil] = pe.value(objective_expr(model, f, y))

        for soil in model.S:
            max_kpi_objectives[soil][target_kpi] = soil_objective_score[soil]
        if result.solver.termination_condition != po.TerminationCondition.optimal:
            continue

        # Save crop plan, calculate KPI scores and profits
        crop_plan = []
        soil_profit = {soil: 0 for soil in model.S}
        soil_count = {soil: 0 for soil in model.S}
        kpi_scores = {kpi: {soil: 0 for soil in model.S} for kpi in kpi_exprs}
        kpi_count = {soil: 0 for soil in model.S}
        
        for f in model.F:
            soil = model.f_soil[f]
            for y in model.Y:
                for c in model.C:
                    val = model.x[c, y, f].value
                    obj_score = pe.value(model.obj)
                    # print(f"The objective score of {soil} for {target_kpi} is: {obj_score}")
                    if val and val > 1e-4:
                        crop_plan.append({
                            'KPI': target_kpi,
                            'Soil': soil,
                            'Farm': f,
                            'Year': y,
                            'Crop': c,
                            'Area_ha': val,
                            'obj_score': obj_score
                        })
                        if (soil, c) in model.gross_margin:
                            soil_profit[soil] += val * model.gross_margin[(soil, c)]
                soil_count[soil] += 1
                for kpi, expr_func in kpi_exprs.items():
                    kpi_scores[kpi][soil] += pe.value(expr_func(model, f, y))
                kpi_count[soil] += 1

        avg_profit = {soil: soil_profit[soil] / soil_count[soil] for soil in model.S if soil_count[soil] > 0}
        avg_kpis = {kpi: {soil: kpi_scores[kpi][soil] / kpi_count[soil] for soil in model.S if kpi_count[soil] > 0} for kpi in kpi_exprs}
        
        #quick evaluation of the scores for the graph
        if target_kpi == 'cr':
            print(f"target kpi: {target_kpi}")
            evaluate_current_plan_kpi(model)
        
        df = pd.DataFrame(crop_plan)
        filename = f"crop_plan_objective_{target_kpi}.csv"
        df.to_csv(filename, index=False)

        results.append({
            'target_kpi': target_kpi,
            'avg_soil_profit': avg_profit,
            'avg_kpi_scores': avg_kpis,
            'objective_score': soil_objective_score
        })

    return results, max_kpi_objectives