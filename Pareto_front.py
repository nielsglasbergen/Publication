# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 13:54:39 2025

@author: Niels
"""

import pyomo.environ as pe
import pyomo.opt as po
from KPI_formulas import div_expr_func, cover_expr_func, cr_expr_func, n_expr_func, eos_expr_func, \
     profit_with_kpi_subsidy, profit_expr_func

"""Make a base solution for kpi's to ensure all are on a reasonable level.
Not yet a optimal level"""


## Bounds are saved in a csv so read the csv
def load_epsilon_bounds(filename):
    bounds = {}
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().split()
            indicator, soil_type, _, min_val, _, max_val = parts
            if indicator not in bounds:
                bounds[indicator] = {}
            bounds[indicator][soil_type] = {'min': float(min_val), 'max': float(max_val)}
    return bounds


### Pareto Front Generation###

def generate_pareto_front(model, steps, min_profit=None):
    # Initialize and 'unpack' bounds
    current_min = {}
    current_max = {}
    bounds = load_epsilon_bounds("epsilon_bounds.txt")
    for indicator, soils in bounds.items():
        current_min[indicator] = {}
        current_max[indicator] = {}
        for soil, vals in soils.items():
            current_min[indicator][soil] = vals['min']
            current_max[indicator][soil] = vals['max']

    ##Start bisection search
    best_feasible_epsilons = None
    
    for iteration in range(steps):
        epsilons = {}
        for indicator in bounds:
            epsilons[indicator] = {}
            for soil in bounds[indicator]:
                
                # All need to be maximized, but these two
                if indicator in ['n']:
                    epsilons[indicator][soil] = (current_max[indicator][soil] + current_min[indicator][soil]) / 2
                else:
                    epsilons[indicator][soil] = (current_min[indicator][soil] + current_max[indicator][soil]) / 2


        # Remove old constraints
        if hasattr(model, 'epsilon_con'): 
            model.del_component(model.epsilon_con)
        model.epsilon_con = pe.ConstraintList()

        if min_profit is not None:
            model.min_profit_constraint = pe.Constraint(
                expr=profit_expr_func(model) >= min_profit
            )


        # Add KPI functions as constraints with min or max value
        for indicator, expr_func in {'div': div_expr_func, 'cover': cover_expr_func, 'cr': cr_expr_func, 'n': n_expr_func, 'eos': eos_expr_func}.items():
            for f in model.F:
                soil_type = model.f_soil[f]
                epsilon_value = epsilons[indicator][soil_type]
                  
                for y in model.Y:
                        if indicator in ['n']:
                            model.epsilon_con.add(expr_func(model, f, y) <= epsilon_value)
                        else:
                            model.epsilon_con.add(expr_func(model, f, y) >= epsilon_value)

        # Set profit as objective
        if hasattr(model, 'obj'):
            model.del_component(model.obj)

        model.obj = pe.Objective(expr=profit_expr_func(model), sense=pe.maximize)

        solver = po.SolverFactory('gurobi')
        result = solver.solve(model, tee=False)

        #Save results if feasible
        if result.solver.termination_condition == po.TerminationCondition.optimal:             

            best_feasible_epsilons = epsilons.copy()
            
            # Update bounds to new values if feasible to decresae/increase new epsilon
            for indicator in bounds:
                for soil in bounds[indicator]:
                    if indicator in ['n']:
                        current_max[indicator][soil] = epsilons[indicator][soil]  # n moet naar beneden
                    else:
                        current_min[indicator][soil] = epsilons[indicator][soil]  # andere mogen omhoog
        else:
           
            #If infeasible, set current values as max and min (opposite of feasible)
            for indicator in bounds:
                for soil in bounds[indicator]:
                    if indicator in ['n']:
                        current_min[indicator][soil] = epsilons[indicator][soil]  # n moet omhoog
                    else:
                        current_max[indicator][soil] = epsilons[indicator][soil]  # andere mogen omlaag


    return best_feasible_epsilons

 

def check_profit (model):
    from pyomo.opt import SolverFactory
    solver = SolverFactory("gurobi")
    model.obj = pe.Objective(expr=profit_expr_func(model), sense=pe.maximize)
    results = solver.solve(model, tee=True)
    return pe.value(model.obj)
    
