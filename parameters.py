# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 13:01:27 2025

@author: Niels
"""
import pyomo.environ as pe
from pyomo.environ import Any
def param():
    model = pe.ConcreteModel()
    ###SETS###
    crops = {
        "seed potatoes",
        "winter wheat",
        "sugar beets",
        "seed onions",
        "consumer potatoes",
        "starch potatoes",
        "summer wheat",
        "winter barley",
        "summer barley",
        "english ryegrass",
        "perennial ryegrass",
        "silage maize",
        "brown beans", 
        "winter rapeseed",
        "corn cob",
        "grain maize",
        "empty",
        "green manure"
    }

    rest_crops = {
        # "lucerne",
        # "temporary grassland (with herb-rich grass/clover)",
        "winter wheat",
        "summer wheat",
        "winter barley",
        "summer barley",
        # "rye",
        # "oats",
        # "caraway seed",
        # "blue poppy seed",
        # "spelt",
        # "triticale",
        # "teff",
        # "miscanthus",
        # "rapeseed",
        # "linseed",
        # "red clover",
        # "hemp fiber",
        # "quinoa",
        # "root parsley",
        # "parsley",
        # "grass seed",
        "winter rapeseed",
        # "summer oilseed rape",
        # "other cereals",
        "english ryegrass",
        "empty",
        "green manure"
        # "italian ryegrass",
        # "sorghum",
        # "meadow fescue",
        # "white clover",
        # "fibre flax",
        # "reed fescue"
    }

    years = 4

    months = list(range(1, years * 12 + 13))

    soil = {"sand","clay"}




    Farms = 2

    f_soil = {1:"sand",
              2: "clay",
              }


    ## Area
    f_A = {1:12.2,
              2: 33.6,
              }

    ## Min ha. 
    min_A = 0.5
    
    ## rotation rule
    rotm = 2/3

    ## Profit
    gross_margin = {
        ("clay", "seed potatoes"): 7040, 
        ("clay", "winter wheat"): 1263, 
        ("clay", "sugar beets"): 2671,
        ("clay", "seed onions"): 3624,
        ("clay", "consumer potatoes"): 3115, 
        ("clay", "starch potatoes"): 1365,
        ("clay", "summer wheat"): 988, 
        ("clay", "winter barley"): 1121, 
        ("clay", "summer barley"): 969, 
        ("clay", "silage maize"): 1042, 
        ("clay", "brown beans"): 1145, 
        ("clay", "winter rapeseed"): 798, 
        ("clay", "english ryegrass"): 1789, 
        ("clay", "perennial ryegrass"): 1681, 
        ("clay", "empty"): 0,
        ("clay", "green manure"): -200,
        
        ("sand", "empty"): 0,
        ("sand", "green manure"): -200,
        ("sand", "consumer potatoes"): 3269, 
        ("sand", "starch potatoes"): 1403, 
        ("sand", "winter wheat"): 793, 
        ("sand", "sugar beets"): 1925, 
        ("sand", "seed onions"): 3245,
        ("sand", "summer wheat"): 1254, 
        ("sand", "winter barley"): 761, 
        ("sand", "summer barley"): 529, 
        ("sand", "corn cob"): 1308, 
        ("sand", "grain maize"): 598, 
        ("sand", "silage maize"): 741, 
        ("sand", "brown beans"): 1145, 
        
    
    }

    ### Plant month of crop
    s_c = {
        "seed potatoes" : 3,
        "winter wheat" :10,
        "sugar beets": 3,
        "seed onions" :4,
        "consumer potatoes" : 3,
        "starch potatoes" : 3,
        "summer wheat" : 4,
        "empty": 1,
        "green manure": 1,

        "winter barley" : 10,
        "summer barley" : 4,
        "english ryegrass" : 10,
        "perennial ryegrass" : 10,
        "silage maize": 4,
        "brown beans": 5, 
        "winter rapeseed": 8,
        "corn cob" : 4,
        "grain maize": 4,

    }

    ## Growing time of crop
    gt_c = {
        "seed potatoes" : 5,
        "winter wheat" :10,
        "sugar beets": 7,
        "seed onions" :5,
        "consumer potatoes" : 6,
        "starch potatoes" : 6,
        "summer wheat" : 4,
        "empty": 12,
        "green manure": 12,

        "winter barley" : 10,
        "summer barley" : 4,
        "english ryegrass" : 10,
        "perennial ryegrass" : 10,
        "silage maize": 6,      
        "brown beans": 4, 
        "winter rapeseed": 10,
        "corn cob": 6,
        "grain maize": 6,
    }
    
    ## Create a 0/1 matrix for each crop that will be covered in a 
    ## certain month of the year
    p_cym = {
        (c, y, m): 1 if m in range(s_c[c] + 12*y, s_c[c] + gt_c[c] + 12*y)
        else 0
        for c in crops
        for y in range(years)
        for m in months
    }
    
    #EOS values of pig
    EOS_Pig_manure = 40
    
    #Percentage of nitrogen in manure that stays in the ground, value for EOS
    Percentage_N_in_manure = {"sand": 60,
                              "clay": 80}
    
    ## Organic matter values
    eos_crops = {
        "winter wheat": 3100,   
        "summer wheat": 2750,   

        "seed potatoes": 550,
        "consumer potatoes": 450,
        "starch potatoes": 800,
        "sugar beets": 850,
        "seed onions": 300,
        "empty": 0,
        "green manure": 600,

        "winter barley" : 2650, 
        "summer barley" : 2000, 
        "english ryegrass" : 1900, # second year 2100
        "perennial ryegrass" : 1000,
        "silage maize": 800,      
        "brown beans": 650, 
        "winter rapeseed": 975,
        "corn cob": 800,
        "grain maize": 2400,
    }

    # N content for each crop and region
    N_content = {
        ("seed potatoes","clay"): 0.25,
        ("winter wheat","clay"): 1.62,
        ("sugar beets","clay"): 0.115,
        ("seed onions","clay"): 0.18,
        ("starch potatoes", "clay"): 0.4,
        ("consumer potatoes", "clay"): 0.33,
        ("summer wheat", "clay"): 1.66,
        ("winter barley", "clay"): 1.60,
        ("summer barley", "clay"): 1.23,
        ("silage maize", "clay"): 0.41,
        ("grain maize", "clay"): 1.15,
        ("english ryegrass", "clay"): 0.2, 
        ("perennial ryegrass", "clay"): 0.23, 

        ("winter rapeseed", "clay"): 1,
        ("brown beans", "clay"): 1,
        ("empty", "clay"): 0,
        ("green manure", "clay"): 0.5,
        
        ("consumer potatoes","sand"): 0.33,
        ("seed potatoes","sand"): 0.33,
        ("starch potatoes", "sand"): 0.37,
        ("winter wheat","sand"): 1.62,
        ("sugar beets","sand"): 0.115,
        ("empty", "sand"): 0,
        ("green manure", "sand"): 0.6,
       
        ("seed onions","sand"): 0.18,
        ("summer wheat", "sand"): 1.66,
        ("winter barley", "sand"): 1.60,
        ("summer barley", "sand"): 1.38,
        ("silage maize", "sand"): 0.41,
        ("grain maize", "sand"): 1.15,
      
    }
    
    ## Yield in kg per ha
    yield_kg_ha = {
        ("seed potatoes", "clay"): 38500,
        ("winter wheat", "clay"): 10000,
        ("summer wheat", "clay"): 7500, 
        ("sugar beets", "clay"): 97500,
        ("seed onions", "clay"): 54300,
        ("consumer potatoes", "clay"): 50500,
        ("starch potatoes", "clay"): 42000,
        ("winter barley", "clay"): 9000,
        ("summer barley", "clay"): 7000, 
        ("silage maize", "clay"): 14550,
        ("brown beans", "clay"): 2940,
        ("winter rapeseed", "clay"): 3750, 
        ("english ryegrass", "clay"): 1600,
        ("perennial ryegrass", "clay"): 1400, 
        ( "empty","sand"): 0,
        ( "empty","clay"): 0,
        
        ( "green manure","sand"): 0,
        ( "green manure","clay"): 0,
    

        ("consumer potatoes", "sand"): 48200,
        ("seed potatoes", "sand"): 30000,
        ("starch potatoes", "sand"): 42000,
        ("winter wheat", "sand"): 9300,
        ("winter barley", "sand"): 7900, 
        ("summer barley", "sand"): 6600,
        ("sugar beets", "sand"): 84000,
        ("summer wheat", "sand"): 6600,
       
        ("seed onions", "sand"): 50000,
        ("corn cob", "sand"): 10600,
        ("grain maize", "sand"): 10600,
        ("silage maize", "sand"): 12900,
        
    }

    ## Added nitrogen
    N_fertilizer = {

        ("seed potatoes", "clay"): 120,
        ("winter wheat", "clay"): 245, 
        ("summer wheat", "clay"): 150, 
        ("sugar beets", "clay"): 150,
        ("seed onions", "clay"): 130,
        ("consumer potatoes", "clay"): 250,
        ("starch potatoes", "clay"): 235,
        ("winter barley", "clay"): 140, 
        ("summer barley", "clay"): 80, 
        ("silage maize", "clay"): 160,
        ("brown beans", "clay"): 90,
        ("winter rapeseed", "clay"): 250, 
        ("english ryegrass", "clay"): 165, 
        ("perennial ryegrass", "clay"): 200, 

        ("empty","sand"): 0,
        ("empty","clay"): 0,
       
        ("green manure","sand"): 50,
        ("green manure","clay"): 60,
        
        ("consumer potatoes", "sand"): 188,
        ("seed potatoes", "sand"): 120,
        ("starch potatoes", "sand"): 230,
        ("winter wheat", "sand"): 160,
        ("summer wheat", "sand"): 100,
        ("winter barley", "sand"): 140, 
        ("summer barley", "sand"): 80,
        ("sugar beets", "sand"): 145,

        ("seed onions", "sand"): 120,
        ("corn cob", "sand"): 112,
        ("grain maize", "sand"): 112,
        ("silage maize", "sand"): 112,
    }

    
    Q_seedlings = {
        ("seed potatoes", "clay"): 5200,

        ("consumer potatoes", "sand"): 2700,
    }



    current_plan_initialize = {
    'clay': {
        'sugar beets': 28.7,
        'seed onions': 6.32,
        'winter wheat': 19.9,
        'seed potatoes': 10,
        'silage maize': 7.9,
        'consumer potatoes': 23.3,
        'empty': 3.9,
    },

    'sand': {
        'sugar beets': 21.5,
        'consumer potatoes':11.9,
        'starch potatoes': 16,
        'silage maize': 34.5,
        'seed onions': 4.24,
        # "summer barley": 4.9,
        'winter wheat': 5.6,
        'empty': 5.2,
    },
    }
    
    # Make dict for the current plan
    current_plan = {
    (soil, crop): perc
    for soil, crop_dict in current_plan_initialize.items()
    for crop, perc in crop_dict.items()
    }
    


    ### model sets and var###


    model = pe.ConcreteModel()
    model.C = pe.Set(initialize=crops, ordered=False)
    model.CR = pe.Set(initialize = rest_crops, ordered=False)
    model.Y = pe.RangeSet(0, years-1)
    model.M = pe.Set(initialize = months, ordered = False)
    model.S = pe.Set(initialize=soil, ordered=False)
    model.F = pe.RangeSet(1,Farms)
    model.KPI = pe.Set(initialize=["div", "cover", "cr", "eos", "n"])


    model.f_A = pe.Param(model.F, initialize=f_A)
    model.f_soil = pe.Param(model.F, initialize=f_soil, within=Any)
    model.p_cym = pe.Param(model.C, model.Y, model.M, initialize=p_cym)
    model.min_A = pe.Param(initialize=min_A)
    model.rotm = pe.Param(initialize=rotm)
    model.years = pe.Param(initialize=years)
    model.N_fertilizer = pe.Param(model.C, model.S, initialize=N_fertilizer)
    model.N_content = pe.Param(model.C, model.S, initialize = N_content)
    model.Q_seedlings = pe.Param(model.C, model.S, initialize=Q_seedlings)
    model.yield_kg_ha = pe.Param(model.C, model.S, initialize=yield_kg_ha)
    model.eos_crops = pe.Param(model.C, initialize= eos_crops)
    model.gross_margin = pe.Param(model.S, model.C, initialize= gross_margin)
    model.current_plan = pe.Param(model.S, model.C, initialize = current_plan, default=0)
    model.subsidy = pe.Param(model.S, model.KPI, initialize=0, mutable=True)
    model.kpi_baseline = pe.Param(model.S, model.KPI, initialize=0, mutable=True)
    model.subsidy_budget = pe.Param(initialize=200, mutable=True)
    model.eos_pig_manure = pe.Param(initialize=EOS_Pig_manure)
    model.percentage_N_in_manure = pe.Param(model.S, initialize=Percentage_N_in_manure)

    
    model.kpi_met = pe.Var(model.F, model.Y, model.KPI, within=pe.Binary)
    model.x = pe.Var(model.C, model.Y, model.F, domain = pe.NonNegativeReals)
    model.z = pe.Var(model.C, model.Y, model.F, domain = pe.Binary)

    
    return model

