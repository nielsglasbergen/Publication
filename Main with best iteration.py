# -*- coding: utf-8 -*-
"""
Main script for analyzing current and modeled crop rotations,
incl. profitability, KPI performance, result-based subsidies, and Pareto exploration.
"""

# === Imports ===
from parameters import param
from Constraints import constraints
from Epsilon import epsilon
from Pareto_front import generate_pareto_front, check_profit
from Pareto_KPI_obj import optimize_each_kpi_as_objective
from Calc_percentage import calculate_crop_shares
from Calc_subsidy import (
    subsidy_amount,
    percentage_to_crop_plan,
    calculate_profit_per_ha,
    calc_kpi_scores
)
from KPI_formulas import profit_expr_func
import copy
from copy import deepcopy
from Constraints import evaluate_current_plan_kpi
from best_iterative_response import run_iterative_subsidy_loop_best_response, scale_pareto_with_noise, run_iterative_subsidy_top_down

# === Step 1: Initialize model and set constraints ===
model = param()
model = constraints(model)
model_base = deepcopy(model)
model_profit = deepcopy(model)

# === Step 2: Evaluate current crop plan and compute total profit ===
print("\n%%% Evaluate current crop plan %%%")
current_model = percentage_to_crop_plan(model_base)
current_model_profit = calculate_profit_per_ha(model_base, current_model)
print("Current profit per ha:", current_model_profit)

total_profit = 0
tot_profit = 0
for (c, y, f), area in current_model.items():
    soil = model.f_soil[f]
    if area > 0.001:
        margin = model.gross_margin[(soil, c)]
    else:
        margin = 0
    tot_profit += area * margin

for f in model.F:
    area = model.f_A[f]
    sub = area * 85 * 4
    total_profit += sub
total_profit += tot_profit
print("Total current plan profit:", tot_profit)
print("Total current plan profit with sub:", total_profit)

# === Step 3: Solve profit-maximizing model ===
print("\n%%% Profit-maximizing model %%%")
model_profit_value = check_profit(model_profit)
print("Model total profit:", model_profit_value)

# === Step 4: Compare KPI scores between current and model plan ===
print("\n%%% KPI score comparison %%%")
goals_current = calc_kpi_scores(model_base, current_model)
print("KPI scores of current:", goals_current)

profit_crop_plan = {
    (c, y, f): model_profit.x[c, y, f].value
    for c in model.C for y in model.Y for f in model.F
}
goals_profit = calc_kpi_scores(model_base, profit_crop_plan)
print("KPI scores of profit-maximizing model:", goals_profit)

# === Step 5: Epsilon bounds for KPI space ===
# print("\n%%% Compute KPI bounds with epsilon method %%%")
# bounds = epsilon(model_profit)
# print("Bounds are done")

# # === Step 6: Generate Pareto front ===
print("\n%%% Generate Pareto front %%%")
pareto_results = generate_pareto_front(model, steps=25)
print("Pareto results:", pareto_results)

# === Step 7: Subsidy calibration based on current KPI targets ===
# print("\n%%% Subsidy calibration (target-based) %%%")
baseline_crop_plan = profit_crop_plan
# subsidy_amount(
#     deepcopy(model_base),
#     goals_current,
#     baseline_crop_plan,
#     growth_factor=100,
#     budget=500000,
#     max_iterations=200,
#     amount_of_kpi_met=2
# )

# # === Step 8: Optimize each KPI as objective ===
print("\n%%% Optimize individual KPIs %%%")
results, max_kpi_objectives = optimize_each_kpi_as_objective(model, pareto_results)
print("KPI optimization results complete")

# === Step 9: Run iterative subsidy scaling loop ===
print("\n%%% Iterative subsidy scaling %%%")

'''I usually go for the shift 1 technique to # one of the methods'''

"Best intermediate result METHOD"
print("\n%%% Best intermediate result %%%")


goals_scaled = scale_pareto_with_noise(max_kpi_objectives, 0.5, noise= 0.3)

max_it = 1
best_of_the_best = {}
all_scores = {}
scale_best = {}

for it in range(max_it):
    
    subsidies, budget, scales, kpi_scores, best_soil, scale = kpi_subsidies = run_iterative_subsidy_loop_best_response(
        model_base,
        goals_scaled,
        baseline_crop_plan,
        initial_budget=500,
        max_iterations_it=50,
        max_iterations_sub=100,
        growth_factor=20,
        amount_of_kpi_met=0,
        min_scale=0.2,
        individual_budget = True
    )

    for soil in best_soil:
        score = best_soil[soil]["score"]
        all_scores.setdefault(soil, []).append(score)

        
        if soil not in best_of_the_best or score > best_of_the_best[soil]["score"]:
            best_of_the_best[soil] = best_soil[soil]
            scale_best[soil] = scale

for soil, data in best_of_the_best.items():
    print(f"Best result for {soil}:\n  Score: {data['score']}\n  Budget: €{data['budget']:.2f}")

print("\n=== Effective KPI targets in best iteration ===")
for soil, scale in scale_best.items():
    print(f"\nSoil: {soil} (scale: {scale:.3f})")
    for kpi, base_val in goals_scaled[soil].items():
        if kpi == 'n':
            target = base_val / scale
        else:
            target = base_val * scale
        print(f"  {kpi}: {target:.2f}")


print("\nAll scores per soil type:")
for soil, scores in all_scores.items():
    print(f"{soil}: {scores}")
    
        
print("\n=== Best Normalized KPI Scores per Soil Type ===")
for soil, info in best_soil.items():
    print(f"\nSoil: {soil}")
    print(f"  Iteration: {info['iteration']}")
    print(f"  Normalized score: {info['score']:.3f}")
    print(f"  Budget used: €{info['budget']:.2f}")
    print("  Subsidies:")
    if info['subsidy']:
        for kpi, amount in info['subsidy'].items():
            print(f"    {kpi}: €{amount:.2f}")
    print("  KPI Scores:")
    for kpi, score in info['scores'].items():
        print(f"    {kpi}: {score:.2f}")


# "TOP DOWN METHOD"
# print("\n%%% Top down method %%%")

# max_goal = {
#     'sand': {
#         'div': 0.73,
#         'cover': 0.63,
#         'cr': 0.86,
#         'n': 282.55,
#         'eos': 8633.16
#     },
#     'clay': {
#         'div': 0.71,
#         'cover': 0.62,
#         'cr': 1.05,
#         'n': 758.80,
#         'eos': 6592.01
#     }
# }



# goals_scaled = scale_pareto_with_noise(max_goal, 1.1, noise= 0.1)

# print("this is goals scaled:",goals_scaled)

# kpi_subsidies = run_iterative_subsidy_top_down(
#     model_base,
#     goals_scaled,
#     baseline_crop_plan,
#     max_iterations_sub=100,
#     initial_budget=85,
#     max_iterations=20,
#     growth_factor=20,
#     amount_of_kpi_met=0,
#     min_scale=0.2,
#     individual_budget = True
# )


# subsidies = kpi_subsidies['kpi_subsidy']
# scales = kpi_subsidies['scale']
# kpi_scores = kpi_subsidies['kpi_scores']



# print("\n=== Final Subsidy Outcomes per Soil Type ===")
# for soil, kpis in subsidies.items():
#     print(f"\nSoil: {soil}")
#     for kpi, value in kpis.items():
#         print(f"  {kpi}: €{value:.2f}")

# print("\n=== Scaling Factors per Soil Type ===")
# for soil, scale in scales.items():
#     print(f"  {soil}: {scale:.3f}")

# print("\n=== Final KPI Scores per Soil Type ===")
# for soil, kpis in kpi_scores.items():
#     print(f"\nSoil: {soil}")
#     for kpi, value in kpis.items():
        
#         print(f"  {kpi}: {value:.2f}")

# print("\n=== Effective KPI targets in final iteration ===")
# for soil, scale in scales.items():
#     print(f"\nSoil: {soil} (scale: {scale:.3f})")
#     for kpi, base_val in goals_scaled[soil].items():
#         if kpi == 'n':
#             target = base_val / scale
#         else:
#             target = base_val * scale
#         print(f"  {kpi}: {target:.2f}")


# print("Under the following stariting goals:", goals_scaled)