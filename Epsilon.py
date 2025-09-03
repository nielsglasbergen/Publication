
import pyomo.environ as pe
import pyomo.opt as po
from KPI_formulas import div_expr_func, cover_expr_func, cr_expr_func, n_expr_func, eos_expr_func, \
     profit_with_kpi_subsidy, profit_expr_func


"""This code is to calculate the epsilon values for each KPI in each region"""

def quick_eps(model, expr_func, sense_list=('maximize', 'minimize')):
    print("working on:", expr_func)
    ## Save results
    soil_results = {
        'sand': {'maximize': [], 'minimize': []},
        'clay': {'maximize': [], 'minimize': []},
    }

    ## Del previous objective and run new one, either min or max
    for f in model.F:
        soil_type = model.f_soil[f]
        for y in model.Y:
                expr = expr_func(model, f, y)
                for sense in sense_list:
                    if hasattr(model, 'obj'):
                        model.del_component(model.obj)
                    model.obj = pe.Objective(expr=expr, sense=getattr(pe, sense))
                    solver = po.SolverFactory('gurobi')
                    solver.options['TimeLimit'] = 30
                    result = solver.solve(model, tee=False)
                    if result.solver.termination_condition == po.TerminationCondition.optimal:
                        soil_results[soil_type][sense].append(pe.value(expr))
                    elif result.solver.termination_condition == po.TerminationCondition.feasible: 
                       soil_results[soil_type][sense].append(pe.value(expr))
    ## Only get the lowest max and the highest min to ensure feasiblity within each region
    bounds = {}
    for soil, data in soil_results.items():
        bounds[soil] = {
            'max': min(data['maximize']) if data['maximize'] else float('nan'),
            'min': max(data['minimize']) if data['minimize'] else float('nan')
        }
    return bounds

###Save for all KPI's in csv
def epsilon(model, min_profit=None):
    if hasattr(model, 'min_profit_constraint'):
        model.del_component(model.min_profit_constraint)
    if min_profit is not None:
        model.min_profit_constraint = pe.Constraint(
            expr=profit_expr_func(model) >= min_profit
        )
    
    objective_funcs = {
        'div': div_expr_func,
        'cover': cover_expr_func,
        'cr': cr_expr_func,
        'n': n_expr_func,
        'eos': eos_expr_func,
    }

    bounds = {}
    for name, func in objective_funcs.items():
        bounds[name] = quick_eps(model, func)
    

    # Save bounds to a txt file
    with open("epsilon_bounds.txt", "w") as f:
        for indicator, soils in bounds.items():
            for soil_type, vals in soils.items():
                line = f"{indicator} {soil_type} min {vals['min']} max {vals['max']}\n"
                f.write(line)
    print("Bounds saved to epsilon_bounds.txt")
    if hasattr(model, 'min_profit_constraint'):
        model.del_component(model.min_profit_constraint)
    return bounds
