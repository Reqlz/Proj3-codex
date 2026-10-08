"""Run-limited shelving and small, optional sanctuary discoveries."""
from storage import grant
import math
import random

SHELF_COSTS=((600,120,0,0,0),(2400,600,0,0,0))
TRANSMUTATION_BATCHES=(1,100,1000,10000,"max")
STATION_EVENT_MIN=240.
STATION_EVENT_MAX=420.
STATION_EVENT_DURATION=60.
STATION_EVENT_OUTPUT_SECONDS=20.
STATION_EVENT_NAMES=("A wellspring glimmers", "A crystal cluster ripens", "A clear distillate settles", "A perfect potion forms", "A star fragment descends")

MATERIAL_GUIDES=(
    ("Mana funds your sanctuary.", "The apprentice spark and Spirit Wells make Mana automatically.", "Buy stations, craft magical items, and pay workshop fees.", ("Spark + Wells", "Mana", "Stations / Workshop")),
    ("Shards build physical improvements.", "Crystal Gardens grow Shards. Distilleries consume them to make Essence.", "Build projects, expand the charm shelf, craft charm bodies. Later quarry commissions supply more.", ("Crystal Gardens", "Shards", "Construction / Essence")),
    ("Essence shapes specialised magic.", "Distilleries convert Shards into Essence. More capacity needs more Shard supply.", "Buy spells, enchant charm targets and activity modes, and supply Potion Crucibles.", ("Shards", "Distillery", "Essence")),
    ("Elixirs sustain magic.", "Potion Crucibles consume Essence to make Elixirs.", "Infuse new charms, recharge active charms, and supply Astral Circles.", ("Essence", "Crucible", "Elixirs")),
    ("Stardust carries your progress forward.", "Astral Circles consume Elixirs to produce Stardust.", "Reawaken, fund late spells, light the Lantern, reallocate legacies, or exchange for Mana. Deposit it in Reawakening to fill the bar. Deposits free storage, cannot be withdrawn, and survive ordinary spending.", ("Elixirs", "Astral Circle", "Stardust")),
)

def legacy_points(awakening):
    return min(3,(max(1,awakening)+1)//2)

def total_legacy_points(awakenings):
    return sum(legacy_points(i) for i in range(1,min(awakenings,6)+1))+max(0,awakenings-6)*3

def cabinet_capacity(state, allocation=None):
    return 1+state.shelf_level+min(2,(state.legacies if allocation is None else allocation)[6])

def pedestal_ring(awakenings):
    """Keep the first completed ring visible; show later six-stone rings compactly."""
    completed,current=divmod(awakenings,6)
    return completed, current

class StationEvents:
    def __init__(self,economy,rng=None):
        self.economy=economy
        self.rng=rng or random.Random()

    def advance(self,seconds,visible=True):
        s=self.economy.state
        if not visible or not math.isfinite(seconds) or seconds<=0:return False
        if s.station_event:
            s.station_event["remaining"]=max(0.,s.station_event["remaining"]-seconds)
            if not s.station_event["remaining"]:
                s.station_event=None;s.station_event_wait=self.rng.uniform(STATION_EVENT_MIN,STATION_EVENT_MAX)
                return True
            return False
        flows,_=self.economy.flows()
        eligible=[i for i,n in enumerate(s.owned) if n and flows[i]>0]
        if not eligible:return False
        s.station_event_wait=max(0.,s.station_event_wait-seconds)
        if s.station_event_wait:return False
        target=self.rng.choice(eligible)
        s.station_event=dict(target=target,amount=flows[target]*STATION_EVENT_OUTPUT_SECONDS,remaining=STATION_EVENT_DURATION)
        return True

    def claim(self,target):
        s=self.economy.state;event=s.station_event
        if not event or event["target"]!=target or not s.owned[target]:return 0.
        amount=event["amount"]
        s.station_event=None
        s.station_event_wait=self.rng.uniform(STATION_EVENT_MIN,STATION_EVENT_MAX)
        reward=[0.]*5;reward[target]=amount
        accepted,overflow=grant(s,reward)
        if overflow[target]:self.economy.record(f"Station discovery: {overflow[target]:g} could not fit in storage.")
        # Gifts do not increase historical production counters.
        return accepted[target]
