# VEHICLE OPTIONS
from dataclasses import dataclass
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import copy
import colorama
from colorama import Fore

# =============================================================================
# CONTROL CONSTANTS
# =============================================================================
# TIME
YEARS = pd.Index(range(2023,2034))
YEARS_OF_INTEREST_OFFSETS = [5,8,10]

# TAXES
TAX_RATE = .0988
MILES_PER_YEAR = 12000

REBATES = {
    'Model Y': 7500+2000
}

# FUEL COSTS
AVG_COST_PER_GALLON = 4.5
AVG_COST_PER_KWH = .30

# CAPITAL COSTS - .3
INFLATION =  0.03
CONSTANT_MONETARY_POLICY = [.045-INFLATION]*11

# INSURANCE COSTS
INSURANCE_LINEAR_MODEL_SLOPE = .045
INSURANCE_LINEAR_MODEL_INTERCEPT = 620

# MAINTENANCE COSTS
TIRE_COSTS = {
    'Model Y': 750,
    'Crosstrek': 500,
    'Prius': 350
} 
MILES_PER_TIRE_CAHNGE = 20000

OIL_CHANGE_COST = 50
MILES_PER_OIL_CHANGE = 5000

# REPAIR COSTS
# assuming the following:
# - first 50,000 there are no repair costs due to warranty
# - between 50,000 and 100,000 miles the repair costs average $500 per year at 12,000 miles per year
# - between 100,000 and 150,000 miles the repair costs average $1000 per year at 12,000 miles per year
# - between 150,000 and 200,000 miles the repair costs average $2000 per year at 12,000 miles per year
GT_50K_REPAIRS_COST = 500/12000
GT_100K_REPAIRS_COST = 1000/12000
GT_150K_REPAIRS_COST = 2000/12000
GT_200K_REPAIRS_COST = 2500/12000

# REGISTRATION COSTS
REGISTRATION_LINEAR_MODEL_SLOPE = .0098
REGISTRATION_LINEAR_MODEL_INTERCEPT = 139

# Depreciation model = 20% first year, 15% per year after that
DEPRECIATION_RATE_FIRST_YEAR = 0.2
DEPRECIATION_RATE_LATER_YEARS = 0.15

@dataclass
class Vehicle:
    name:str
    year:int
    value:int
    miles_per:float
    mileage:int
    fuel:str
        
    @property
    def description(self):
        return f'{self.name} {str(self.year).replace("20","")}'
        
VEHICLES = [Vehicle('Model Y', 2023,  51000, 3.5, 0, 'EV'), 
            Vehicle('Crosstrek', 2023, 30000, 30, 0, 'GAS'),
            Vehicle('Crosstrek', 2016, 22000, 29, 50000, 'GAS'),
            # Vehicle('Crosstrek', 2015, 16000, 29, 100000, 'GAS'),
            Vehicle('Prius', 2015, 22000, 48, 50000, 'GAS'),
            # Vehicle('Prius', 2012, 12000, 48, 100000, 'GAS'),
           ]

BASELINE_VEHICLE = 'Crosstrek 16'


# =============================================================================
# COST MODELS
# =============================================================================

def tax_cost(vehicle, years_since_purchase):
    if years_since_purchase == 0:
        return TAX_RATE*vehicle.value
    if years_since_purchase == 1:
        return -REBATES.get(vehicle.name, 0)
    return 0


def yearly_capital_cost(total_spent, year, capital_scenario):
    return capital_scenario[year] * total_spent

#NOTE: Need to account for inflation

def yearly_insurance_cost(vehicle):
    return INSURANCE_LINEAR_MODEL_SLOPE*vehicle.value + INSURANCE_LINEAR_MODEL_INTERCEPT

def fuel_cost_per_mile(vehicle):
    if vehicle.fuel == 'GAS':
        cost_per = AVG_COST_PER_GALLON
    elif vehicle.fuel == 'EV':
        cost_per = AVG_COST_PER_KWH
    
    return cost_per/vehicle.miles_per

def repairs_cost_per_mile(vehicle):
    if vehicle.mileage < 50000:
        return 0
    elif vehicle.mileage < 100000:
        return GT_50K_REPAIRS_COST
    elif vehicle.mileage < 150000:
        return GT_100K_REPAIRS_COST
    elif vehicle.mileage < 200000:
        return GT_150K_REPAIRS_COST
    else:
        return GT_200K_REPAIRS_COST

def maintenance_costs_per_mile(vehicle):
    '''
    Includes both consumables costs such as oil changes as well as repairs costs
    '''
    repairs_costs = repairs_cost_per_mile(vehicle)
    consumables_costs = 0
    if vehicle.fuel == 'GAS':
        consumables_costs += OIL_CHANGE_COST/MILES_PER_OIL_CHANGE

    consumables_costs += TIRE_COSTS[vehicle.name]/MILES_PER_TIRE_CAHNGE
    return repairs_costs + consumables_costs
    

def depreciation(vehicle, year):
    if vehicle.year == year:
        return vehicle.value*DEPRECIATION_RATE_FIRST_YEAR
    else:
        return vehicle.value * DEPRECIATION_RATE_LATER_YEARS

def yearly_registration_cost(vehicle):
    return REGISTRATION_LINEAR_MODEL_SLOPE*vehicle.value + REGISTRATION_LINEAR_MODEL_INTERCEPT

# =============================================================================
# COST COMPUTATIONS
# =============================================================================

# COSTS PER YEAR
def compute_costs():
    costs = ['Taxes', 'Insurance', 'Registration', 'Deprecation', 'Maintenance', 'Fuel', 'Capital']
    vehicles = copy.deepcopy(VEHICLES)
    fig, axs = plt.subplots(len(VEHICLES), figsize=(10,30))
    all_costs_data = pd.DataFrame()
    for i, v in enumerate(vehicles):
        ax = axs[i]
        costs_data = pd.DataFrame(index=YEARS, columns=costs)
        total_cash_outlay = v.value
        for y in YEARS:
            # Actual capital expendatures/loss
            costs_data['Taxes'][y] = tax_cost(v,y-YEARS[0])
            costs_data['Insurance'][y] = yearly_insurance_cost(v)
            costs_data['Registration'][y] = yearly_registration_cost(v) 
            costs_data['Maintenance'][y] = maintenance_costs_per_mile(v)*MILES_PER_YEAR
            costs_data['Fuel'][y] = fuel_cost_per_mile(v)*MILES_PER_YEAR
            costs_data['Capital'][y] = yearly_capital_cost(total_cash_outlay,y-YEARS[0],CONSTANT_MONETARY_POLICY)
            
            total_cash_outlay += costs_data.loc[y,:].sum()
            
            # Value loss
            costs_data['Deprecation'][y] = depreciation(v, y)
            
            if costs_data['Taxes'][y] < 0:
                # we are dealing with a tax credit, unfortunatly negative numbers are a real pain for plotting, 
                # so we will devide up the credit proportionally between all of the other expenses
                tax_credit = -costs_data['Taxes'][y]
                wo_taxes = costs_data.loc[:,costs_data.columns != 'Taxes']
                total_wo_taxes = wo_taxes.loc[y,:].sum()
                for c in wo_taxes.columns:
                    cost_percent_of_total = wo_taxes[c][y]/total_wo_taxes
                    costs_data[c][y] -= tax_credit*cost_percent_of_total
                costs_data['Taxes'][y] = 0

            v.value -= costs_data['Deprecation'][y]
            v.mileage += MILES_PER_YEAR
        print(costs_data.astype(float).round(0))
        # costs_data.plot(ax=ax, kind='area', title=v.description)
        print((v.description,v.value))
        ax.set_ylim(0, 25000)
        costs_data = pd.concat([costs_data], axis=1, keys=[v.description], names=['Vehicle'])
        all_costs_data = pd.concat([all_costs_data,costs_data],axis=1)
        
    for ax in axs:
        ax.plot(all_costs_data['Model Y 23'].sum(axis=1), label='Model Y 23', linestyle='--')
        # ax.plot(all_costs_data['Prius 12'].sum(axis=1), label='Prius 12', linestyle='--')
        ax.legend()

# plt.show()

# TOTAL COST OF OWNERSHIP
    tco = pd.DataFrame(index=YEARS, columns=[v.description for v in VEHICLES])
    fig, ax = plt.subplots(figsize=(10,5))
    for y in YEARS:
        for v in VEHICLES:
            veh_data = all_costs_data[v.description]
            cumulative_cost = veh_data.loc[veh_data.index <= y,:].sum().sum()
            tco[v.description][y] = cumulative_cost

    tco.plot(ax=ax)
# plt.show()

# COMPARTIVE SUMMARY
    baseline = tco[BASELINE_VEHICLE]
    fig, axs = plt.subplots(2,figsize=(10,5))
    tco_delta = tco.subtract(baseline, axis=0)
    tco_delta_percent = tco_delta.divide(baseline, axis=0)*100

# print(tco_delta.astype(int).round(0))
# print(tco_delta_percent.astype(int).round(0))
    tco_delta.plot(ax=axs[0])
    tco_delta_percent.plot(ax=axs[1])
# plt.show()


# AVG/PER YEAR DELTAS AT CHECKPOINTS
    years_of_interest = [y for i,y in enumerate(YEARS) if i in YEARS_OF_INTEREST_OFFSETS]
    checkpoint_avg_tco_per_year = pd.DataFrame(index=years_of_interest, columns=[v.description for v in VEHICLES])
    checkpoint_avg_delta_tco_per_year = pd.DataFrame(index=years_of_interest, columns=[v.description for v in VEHICLES])
    checkpoint_avg_delta_pct_tco_per_year = pd.DataFrame(index=years_of_interest, columns=[v.description for v in VEHICLES])

    for y in years_of_interest:
        for v in VEHICLES:
            checkpoint_avg_tco_per_year[v.description][y] = tco[v.description][y]/(y-YEARS[0])
            checkpoint_avg_delta_tco_per_year[v.description][y] = tco_delta[v.description][y]/(y-YEARS[0])
            checkpoint_avg_delta_pct_tco_per_year[v.description][y] = (tco_delta[v.description][y]/(y-YEARS[0]))/checkpoint_avg_tco_per_year[v.description][y]*100
            
    print('AVG TCO/YEAR')
    print(checkpoint_avg_tco_per_year.astype(float).round(0)) 

    print('\n\nDELTAS FROM AVG TCO/YEAR OF 2016 CROSSTREK')
    print(checkpoint_avg_delta_tco_per_year.astype(float).round(0)) 
    
    print('\n\nDELTAS PERCENT FROM AVG TCO/YEAR OF 2016 CROSSTREK')
    print(checkpoint_avg_delta_pct_tco_per_year.astype(float).round(0)) 


print(Fore.BLUE + 'With $4.50/gal gas price and $0.30/KWh electricity price' + Fore.RESET)
compute_costs()
print('\n\n\n\n')
print(Fore.BLUE + 'With $4.50/gal gas price and $0.20/KWh electricity price' + Fore.RESET)
AVG_COST_PER_GALLON = 4.5
AVG_COST_PER_KWH = .20
compute_costs()
print('\n\n\n\n')
print(Fore.BLUE + 'With $6.00/gal gas price and $0.30/KWh electricity price' + Fore.RESET)
AVG_COST_PER_GALLON = 6.0
AVG_COST_PER_KWH = .30
compute_costs()
print('\n\n\n\n')
