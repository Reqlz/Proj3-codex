"""Storage and prestige policy, independent of rendering and wall-clock time."""
import math
from astral_systems import VIOLET_DISCOUNT

BASE_CAPACITIES=(250000,100000,15000,500)
MAX_LEVELS=(10,10,10,10,3)

def capacities(state):
    return [base*(1+.5*state.awakenings)*2**state.storage_levels[i]
            for i,base in enumerate(BASE_CAPACITIES)]+[state.rebirth_goal*2**state.storage_levels[4]]

def room(state):
    return [max(0.,limit-stock) for stock,limit in zip(state.resources,capacities(state))]

def upgrade_price(state,target):
    recipe=[0]*5
    if type(target) is not int or not 0<=target<5 or state.storage_levels[target]>=MAX_LEVELS[target]:return tuple(recipe)
    discount=(1-.05*state.spell_ranks['Sanctuary'][0])*(1-VIOLET_DISCOUNT if target==1 and 1 in state.talismans else 1)
    recipe[target]=math.ceil(capacities(state)[target]*(.25 if target==4 else .1)*discount-1e-9)
    return tuple(recipe)

def grant(state,reward):
    accepted=[min(max(0.,amount),space) for amount,space in zip(reward,room(state))]
    overflow=[max(0.,amount-got) for amount,got in zip(reward,accepted)]
    state.resources=[stock+got for stock,got in zip(state.resources,accepted)]
    return accepted,overflow

def transaction_fits(state,cost,reward):
    return all(stock+1e-8>=price and (amount<=0 or stock-price+amount<=limit+1e-8)
               for stock,price,amount,limit in zip(state.resources,cost,reward,capacities(state)))

def transact(state,cost,reward):
    if not transaction_fits(state,cost,reward):return False
    state.resources=[max(0.,stock-price)+amount for stock,price,amount in zip(state.resources,cost,reward)]
    return True

def banked_stardust(state):
    return state.rebirth_dust

def seal_multiplier(seals):
    effective=seals if seals<=250 else 250+500*(math.sqrt(1+(seals-250)/250)-1)
    return 1+.1*min(10000,effective)
