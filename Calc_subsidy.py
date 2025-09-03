# -*- coding: utf-8 -*-
"""
Created on Wed May 14 13:25:31 2025

@author: Niels
"""

import pyomo.environ as pe
from collections import defaultdict
from KPI_formulas import div_expr_func, cover_expr_func, cr_expr_func, n_expr_func, eos_expr_func, \
     profit_with_kpi_subsidy, profit_expr_func
from Constraints import evaluate_current_plan_kpi
import random
"""Calculations to determine the needed subsidy to meet certain kpi's"""


"""Set the KPI targets"""
def kpi_met_constraint_rule(model, f, y, kpi):

    M = 100000 ## Could be a big-M depending on each of the KPI's, but this works as well
    soil = model.f_soil[f]
    baseline = model.kpi_baseline[soil, kpi]

    score = {
        "div": div_expr_func,
        "cover": cover_expr_func,
        "cr": cr_expr_func,
        "eos": eos_expr_func,
        "n": n_expr_func,

    }[kpi](model, f, y)

    ## Update the constraint
    if kpi in ['n']:
        return score - baseline <= (1 - model.kpi_met[f, y, kpi]) * M
    else:
        return baseline - score <= (1 - model.kpi_met[f, y, kpi]) * M


"""Calculate the current scores"""
def calc_kpi_scores(model, crop_planning):

    kpi_funcs = {
        "div": div_expr_func,
        "cover": cover_expr_func,
        "cr": cr_expr_func,
        "n": n_expr_func,
        "eos": eos_expr_func,
    }

    # Save model.x temporarely 
    old_x = {}
    for c in model.C:
        for y in model.Y:
            for f in model.F:       
                    old_x[c, y, f] = model.x[c, y, f].value
                    model.x[c, y, f].value = crop_planning[c, y, f]

    # Get the scores
    scores = {soil: {kpi: [] for kpi in kpi_funcs} for soil in model.S}

    for f in model.F:
        soil = model.f_soil[f]
        for y in model.Y:
            for kpi, func in kpi_funcs.items():
                
                    score = pe.value(func(model, f, y))
                    scores[soil][kpi].append(score)


    # Get the orgiginal values back
    for key, val in old_x.items():
        model.x[key].value = val

    # Calc average scores
    avg_scores = {
        soil: {
            kpi: sum(vals) / len(vals) if vals else None
            for kpi, vals in kpi_dict.items()
        }
        for soil, kpi_dict in scores.items()
    }

    return avg_scores


"""Check whether subsidy is achieved"""
def subsidy_check(model, goal, crop_plan, amount_of_kpi_met):
    #calculate which KPI scores need the subsidy increased
    
    subsidy_needed = {}
    goal_reached = {}


    for soil in model.S:
        subsidy_needed[soil] = {}
        goal_reached[soil] = {}

        for kpi in model.KPI:
            unmet = 0
            met_count = 0

            for f in model.F:
                ## Change from farm to soil
                if model.f_soil[f] != soil:
                    continue
                for y in model.Y:

                    var = model.kpi_met[f, y, kpi]
                    
                    if var.value is not None:
                        val = pe.value(var)
                        is_met = int(val >= 0.5)
                        unmet += (1 - is_met)
                        met_count += is_met
                    else:
                        unmet += 1


            subsidy_needed[soil][kpi] = 0 if met_count > amount_of_kpi_met else 1
            goal_reached[soil][kpi] = 1 - subsidy_needed[soil][kpi]

    return subsidy_needed, goal_reached

"""Core of the calculation, all the functions come together in one 
iteratively checking function"""


def subsidy_amount(model, goal, baseline_crop_plan, growth_factor, budget = 85, max_iterations=100, amount_of_kpi_met= 1, individual_budget=False):


    # Initialize iteration counter and structures
    it = 0
    kpi_goal = goal  # Desired KPI target values per soil, from previous functions (like pareto front)
    kpi_subsidy = {}        # current subsidy levels for each soil-KPI
    kpi_subsidy_start = {}  # base subsidy increment amounts for each soil-KPI (initial calculated subsidy)
    tot_needs = defaultdict(lambda: defaultdict(int))  # track how many iterations each KPI needed subsidy
    total_budget = {soil: 0 for soil in model.S}
    # Calculate the current and baseline crop plan and profit per hectare
    current_plan = percentage_to_crop_plan(model)
    profit_current = calculate_profit_per_ha(model, current_plan)
    profit_baseline = calculate_profit_per_ha(model, baseline_crop_plan)
    kpi_met_matrix ={}
    # Compute profit difference per hectare for each soil, averaged over years
    profit_diff = {
        soil: (profit_current[soil] - profit_baseline[soil]) / len(model.Y)
        for soil in model.S
    }

    # Initial subsidy need check: determine which KPI goals are unmet under the current plan
    subsidy_needs, goal_reached = subsidy_check(model, kpi_goal, current_plan, amount_of_kpi_met)
    
    # Initialize subsidy amounts for each KPI–soil based on profit difference and initial need
    for soil in model.S:


        kpi_subsidy_start[soil] = {}
        kpi_subsidy[soil] = {}
        total_needs = sum(subsidy_needs[soil].values())  # number of KPI goals unmet for this soil

        for kpi in kpi_goal[soil]:
            # Base subsidy amount per KPI for this soil: distribute profit loss equally among unmet KPIs
            base_amount = (max(100, profit_diff[soil]) / total_needs) * 0.01 if total_needs > 0 else 0
            
            kpi_subsidy_start[soil][kpi] = base_amount


            # Create the first subsidy iteration by adding a subsidy to the unmet KPI's
            kpi_subsidy[soil][kpi] = base_amount * subsidy_needs[soil][kpi]

    # Track the previous iteration's plan and which KPI–soil goals were met
    prev_plan = current_plan.copy()

    # Copy goal_reached to avoid referencing the same dict in iterations
    prev_goal_reached = {soil: goal_reached[soil].copy() for soil in goal_reached}
    
    # Start the iterative subsidy adjustment process

    while it<max_iterations:
        
        # Initialize a new constraint that ensures all is within the budget
        model.subsidy_budget = budget 
        
        ## Choose between individual and combined budget
        if individual_budget == True:
            if hasattr(model, 'SubBudget'):
                    model.del_component(model.SubBudget)
            model.SubBudget = pe.Constraint(model.F, rule=total_subsidy_budget_constraint_farm_specific)
        else:
            if hasattr(model, 'SubBudget'):
                    model.del_component(model.SubBudget)
            model.SubBudget = pe.Constraint(rule = total_subsidy_budget_constraint)
        # Apply the current subsidies and KPI targets to the model
        for soil in model.S:
            for kpi in kpi_goal[soil]:
                if (soil, kpi) in model.subsidy:
                    model.subsidy[soil, kpi] = kpi_subsidy.get(soil, {}).get(kpi, 0)
                    
                    model.kpi_baseline[soil, kpi] = kpi_goal[soil][kpi]

        # Rebuild the KPI constraint and objective with updated subsidies
        if hasattr(model, 'kpi_met_constraint'):
            model.del_component(model.kpi_met_constraint)
        model.kpi_met_constraint = pe.Constraint(model.F, model.Y, model.KPI, rule=kpi_met_constraint_rule)

        if hasattr(model, 'obj'):
            model.del_component(model.obj)
        model.obj = pe.Objective(rule=profit_with_kpi_subsidy, sense=pe.maximize)

        # Solve the model with the new subsidy settings
        solver = pe.SolverFactory("gurobi")
        result = solver.solve(model, tee=False)
        if result.solver.termination_condition != pe.TerminationCondition.optimal:
            print(f"Solver terminated with condition: {result.solver.termination_condition}")
            break  # If no optimal solution, break out

        # Retrieve the new optimal crop plan after applying subsidies
        new_plan = {
            (c, y, f): model.x[c, y, f].value
            for c in model.C for y in model.Y for f in model.F
        }
        
        # Check if the crop plan changed from the previous iteration
        # Directly checking KPI values resulted in noisy differences, so this helps prevent that
        plan_changed = False
        tolerance = 0.001
        for key, prev_val in prev_plan.items():
            new_val = new_plan.get(key, 0)
            if abs(new_val - prev_val) > tolerance:
                plan_changed = True
                break

        # Determine which KPI goals are met or unmet with the new plan
        subsidy_needs, goal_reached = subsidy_check(model, kpi_goal, new_plan, amount_of_kpi_met)
        # Update the count of iterations each KPI–soil has needed subsidy (for diagnostics)
        for soil in subsidy_needs:
            for kpi, need in subsidy_needs[soil].items():
                tot_needs[soil][kpi] += need

        # print(f"Iteration {it} - subsidy still needed: {subsidy_needs}")

        # Check if all KPI goals are now met (no subsidies needed)
        all_done = all(
            all(need == 0 for need in subsidy_needs[soil].values())
            for soil in model.S
        )
        if all_done:

            kpi_met_matrix = {
                (f, y, k): int(pe.value(model.kpi_met[f, y, k]) >= 0.5)
                for f in model.F for y in model.Y for k in model.KPI
            }
            print(f"DEBUG: kpi_met_matrix contains {len(kpi_met_matrix)} entries")
            assert len(kpi_met_matrix) > 0, "kpi_met_matrix is unexpectedly empty"


            print("\n=== KPI Met Matrix – Final Iteration ===")
            entries = kpi_met_matrix
            farms = sorted(set(f for (f, _, _) in entries))
            years = sorted(set(y for (_, y, _) in entries))
            kpis = sorted(set(k for (_, _, k) in entries))
            
            # Header
            print(f"{'Farm':<6} {'Year':<6} " + " ".join(f"{k:<8}" for k in kpis))
            print("-" * (13 + 9 * len(kpis)))
            
            # Rijen
            for f in farms:
                for y in years:
                    row = f"{f:<6} {y:<6} "
                    row += " ".join(str(entries.get((f, y, k), "-")).ljust(8) for k in kpis)
                    print(row)


            print("All KPI goals achieved. Final subsidy scheme:")
            
            # print(f"\nSubsidy usage per farm and year at iteration {it}:")
            for f in model.F:
                soil = model.f_soil[f]
                total_budget[soil] = 0
                for y in model.Y:
                    total_subsidy = 0
                    # print(f"  Farm {f}, Year {y}:")
                    for k in model.KPI:
                        met = pe.value(model.kpi_met[f, y, k])
                        if met is None:
                            met = 0
                        subsidy = pe.value(model.subsidy[soil, k])
                        amount = met * subsidy 
    
                        total_subsidy += amount
                    #     print(f"    KPI {k}: {'x' if met else ''} → €{amount:.2f}")
                    # print(f"    Total subsidy: €{total_subsidy:.2f}")
                    total_budget[soil] += total_subsidy
            kpi_raw = evaluate_current_plan_kpi(model)
            kpi_scores = {soil: {kpi: kpi_raw[kpi][soil] for kpi in kpi_raw} for soil in model.S}
            
            
            
            return {"partial_success": False,
                    "kpi_subsidy": kpi_subsidy,
                    "total_budget": total_budget,
                    "kpi_scores": kpi_scores,
                    "kpi_met_matrix": kpi_met_matrix}

        ## Last check if one of the farms has succesfully reached the subsidies
        if it == max_iterations -1:
            farm_success = {
                f: all(subsidy_needs[model.f_soil[f]][k] == 0 for k in model.KPI)
                for f in model.F
            }
            if any(farm_success.values()):
                kpi_met_matrix = {
                    (f, y, k): int(pe.value(model.kpi_met[f, y, k]) >= 0.5)
                    for f in model.F for y in model.Y for k in model.KPI
                }
                print(f"DEBUG: kpi_met_matrix contains {len(kpi_met_matrix)} entries")
                
                print("\n=== KPI Met Matrix – Final Iteration ===")
                entries = kpi_met_matrix
                farms = sorted(set(f for (f, _, _) in entries))
                years = sorted(set(y for (_, y, _) in entries))
                kpis = sorted(set(k for (_, _, k) in entries))
            
                print(f"{'Farm':<6} {'Year':<6} " + " ".join(f"{k:<8}" for k in kpis))
                print("-" * (13 + 9 * len(kpis)))
                for f in farms:
                    for y in years:
                        row = f"{f:<6} {y:<6} "
                        row += " ".join(str(entries.get((f, y, k), "-")).ljust(8) for k in kpis)
                        print(row)
                for f in model.F:
                    soil = model.f_soil[f]
                    total_budget[soil] = 0
                    for y in model.Y:
                        total_subsidy = 0
                        # print(f"  Farm {f}, Year {y}:")
                        for k in model.KPI:
                            met = pe.value(model.kpi_met[f, y, k])
                            if met is None:
                                met = 0
                            subsidy = pe.value(model.subsidy[soil, k])
                            amount = met * subsidy 
                            total_subsidy += amount
                        
                        total_budget[soil] += total_subsidy


              


                evaluate_current_plan_kpi(model)
                kpi_raw = evaluate_current_plan_kpi(model)
                kpi_scores = {soil: {kpi: kpi_raw[kpi][soil] for kpi in kpi_raw} for soil in model.S}
                return {
                    "partial_success": True,
                    "farm_success": farm_success,
                    "kpi_subsidy": kpi_subsidy,
                    "total_budget": total_budget,
                    "kpi_scores": kpi_scores
                }

        # Increase subsidies for remaining unmet KPI–soil pairs, with conditions to prevent false triggers
        for soil in model.S:
            for kpi in kpi_goal[soil]:
                if subsidy_needs[soil][kpi] == 1:  # KPI is still unmet for this soil
                    if (not plan_changed) and (prev_goal_reached.get(soil, {}).get(kpi) == 1):
                        # If plan didn't change and this KPI was met in the previous iteration, skip subsidy increase
                        # This avoids raising subsidy due to floating-point score fluctuations
                        continue
                    # Otherwise, plan changed or KPI was previously unmet – increase subsidy to push towards goal
                    kpi_subsidy[soil][kpi] += growth_factor * kpi_subsidy_start[soil][kpi] * random.uniform(0.2, 1.8)

        
        # Prepare for next iteration: update previous plan and achieved-goals record
        prev_plan = new_plan
        prev_goal_reached = {soil: goal_reached[soil].copy() for soil in goal_reached}
        it += 1  # move to the next iteration
        
        
    # print(f"\nSubsidy usage per farm and year at iteration {it}:")
    for f in model.F:
        soil = model.f_soil[f]
        for y in model.Y:
            total_subsidy = 0
            # print(f"  Farm {f}, Year {y}:")
            for k in model.KPI:
                met = pe.value(model.kpi_met[f, y, k])
                if met is None:
                    met = 0
                subsidy = pe.value(model.subsidy[soil, k])
                amount = met * subsidy 
                total_subsidy += amount
                # print(f"    KPI {k}: {'x' if met else ''} → €{amount:.2f}")
            # print(f"    Total subsidy: €{total_subsidy:.2f}")
            

    
    # If loop finishes without all goals met, output the cumulative needs for analysis and return current subsidies
    print(f"Reached iteration limit. Cumulative unmet counts: {tot_needs}")
    print("No achievable solution within the iteration limit. Final subsidy scheme:", kpi_subsidy)
    
    return None

"""Calculating the profits"""
def calculate_profit_per_ha(model, crop_plan=None):
    
    
    profit_per_soil = {soil: 0 for soil in model.S}
    area_per_soil = {soil: 0 for soil in model.S}

    for f in model.F:
        soil = model.f_soil[f]
        for y in model.Y:
            for c in model.C: 
                key = (c, y, f)
                if (soil, c) not in model.gross_margin:
                   
                    continue
                 
                   
                area = crop_plan[key] if crop_plan and key in crop_plan else model.x[c, y, f].value
                if area and area > 1e-4:
                        profit = area * model.gross_margin[(soil, c)]
                        profit_per_soil[soil] += profit
                        area_per_soil[soil] += area

    profit_per_ha = {
        soil: (profit_per_soil[soil] / area_per_soil[soil]) if area_per_soil[soil] > 0 else 0
        for soil in model.S
    }

    return profit_per_ha


"""The current model percentages to 4 year crop plan"""
def percentage_to_crop_plan(model):
    crop_plan = {}

    for f in model.F:
        soil = model.f_soil[f]
        area_farm = model.f_A[f]

        for c in model.C:
            perc = model.current_plan[soil, c]/ 100
            for y in model.Y:
                crop_plan[(c, y, f)] = perc * area_farm 

    return crop_plan

"""The new constraint that adds a maximum budget to ensure no overbudgeting"""
def total_subsidy_budget_constraint_farm_specific(model, f):
    return sum(
        model.kpi_met[f, y, kpi] * model.subsidy[model.f_soil[f], kpi]
        for y in model.Y for kpi in model.KPI
    ) <= model.subsidy_budget * len(model.Y)

def total_subsidy_budget_constraint(model):
    return sum(
        model.kpi_met[f, y, kpi] * model.subsidy[model.f_soil[f], kpi]
        for y in model.Y for kpi in model.KPI for f in model.F
    ) <= model.subsidy_budget * len(model.Y) * len(model.F)


     




