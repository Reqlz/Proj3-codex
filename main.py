"""Starstruck Atelier: a parchment-and-starlight incremental game.

Run this file to play. Economy and persistence can be imported without a display.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import math
import os
import random
import shutil
import time
import tkinter as tk

from PIL import Image, ImageDraw, ImageFilter, ImageTk
from presentation import WindowFrame, CursorSet, CanvasButtons
from spell_graph import SpellGraph


RESOURCES = ("Mana", "Shards", "Essence", "Elixirs", "Stardust")
INK = "#3f3027"
MUTED = "#79654d"
BURGUNDY = "#743c40"
TEAL = "#246b66"
GOLD = "#ad8950"
PAPER = "#ecddbb"
LIGHT = "#f7edda"
PRESTIGE_TARGET = 120.0
SAVE_VERSION = 7
REBIRTH_TARGETS=(120,280,520,1590,3960,8130,13500,20300,29500,40100,51800,68000)
LEGACIES=(
    ("Dawn memory",1,(0,),.05,"+5% Mana production"),
    ("Crystal memory",1,(1,),.05,"+5% Shard production"),
    ("Tide memory",1,(2,),.05,"+5% Essence production"),
    ("Ember memory",2,(3,),.05,"+5% Elixir production"),
    ("Astral memory",3,(4,),.05,"+5% Stardust production"),
    ("Moonweaver",5,(0,1,2,3,4),.02,"+2% production of every resource"),
)


def rebirth_target(awakenings):
    if awakenings<len(REBIRTH_TARGETS):return float(REBIRTH_TARGETS[awakenings])
    return float(math.ceil(REBIRTH_TARGETS[-1]*(1+(awakenings-11)/11)**3/100)*100)
SCENE_ANCHORS = ((250, 660), (750, 660), (390, 765), (610, 765), (500, 260))
SCENE_FOOTPRINTS = ((63, 25), (63, 25), (57, 22), (57, 22), (67, 67))
CHARM_RECIPES = ((300,40,0,0,0),(1800,180,0,0,0),(9000,700,0,0,0),(40000,2000,0,0,0))
RECHARGE_COSTS = (10,25,60,150)
RESOURCE_ROLES = ("Funds the work: stations, crafting fees and transmutation.", "Physical construction: restoration and charm bodies.", "Enchantment: charm targeting, modes and the spell tree.", "Sustaining magic: infuse charms and recharge their duration.", "Reawakening: earn Moon Seals; also binds the Star Compass.")
TREE = {
    "Charmcraft": ("Economical bodies", "Lasting magic", "Potent inscriptions", "Enduring refills"),
    "Deliveries": ("Trusted courier", "Material gifts", "Swift returns", "Two possibilities"),
    "Sanctuary": ("Careful construction", "Resonant restoration", "Frugal transmutation", "Sanctuary radiance"),
}
ADVANCED_NAMES = {"Charmcraft":("Lasting Infusion","Crystal Cutting"),"Deliveries":("Generous Parcels","Efficient Packing"),"Sanctuary":("Resonant Masonry","Careful Recovery")}
SPELL_EFFECTS = {
    "Charmcraft":("Charm ingredient discount: {v}%","New charm duration: +{v}%","New charm potency: +{v} percentage points","Recharge price growth: ×1.6","Infusion duration bonus: +75%","Additional charm Shard discount: 15 percentage points"),
    "Deliveries":("Mana payout: +{v}%","Material gift: {v} minutes of gross output","Courier cooldown reduction: {v} minutes","Two alternative contracts each cycle","Supplementary material gifts: +50%","Future requested quantities: −10%"),
    "Sanctuary":("Construction discount: {v}%","Restoration bonus: +{v} percentage points","Transmutation Mana fee discount: {v}%","Mana production: +10%","Additional restoration bonus: +2 percentage points","Reverse-transmutation output: +20%"),
}
SPELL_SECONDARY = {
    "Charmcraft":((1,(250,750,2250)),(3,(10,30,90)),(1,(1000,3000,9000))),
    "Deliveries":((1,(250,750,2250)),(3,(10,30,90)),(1,(500,1500,4500))),
    "Sanctuary":((1,(1000,3000,9000)),(1,(1000,3000,9000)),(1,(0,0,0))),
}
TALISMAN_COSTS = ((1200,600,20,0,0),(2500,1200,40,0,0),(6000,150,400,6,0),(15000,300,80,120,0),(35000,800,160,30,45))
RESTORATION_NAMES = ("Lantern Path","Crystal Planters","Glasswork Shelves","Hearth Mosaic","Celestial Inlay")
RESTORATION_COSTS = ((600,100,0,0,0),(1800,400,0,0,0),(6000,1600,0,0,0),(16000,6400,0,0,0),(45000,25000,0,0,0))
CONSTRUCTION_MAX_LEVEL=5
CONSTRUCTION_SHARD_GROWTH=6
CONSTRUCTION_MANA_GROWTH=2
STAGES = ("Level 1 · Weathered","Level 2 · Restored","Level 3 · Awakened","Level 3 · Masterwork")
SPIRIT_PERCENTAGES = (15,20,25,30,40,50)
TALISMAN_NAMES = ("Dawn Vessel", "Violet Crown", "Tideglass", "Ember Heart", "Star Compass")
CHAPTERS = (
    ("first", "A first spark", "Welcome to Starstruck Atelier. Your apprentice spark makes Mana without ingredients. Buy a Spirit Well to increase that supply, then plant a Crystal Garden. Nothing here needs a hurried hand.\n\nThe guided first steps highlight useful controls. You may skip or restart them at any time from this tome."),
    ("production", "The working sanctuary", "Mana buys buildings. The ×1, ×10, and MAX bookmarks choose how many to purchase. Unlocks depend on total Mana earned this run, not the amount left in your purse.\n\nSelect a building in the illustration to find its journal card. Cards show gross output and capacity; the resource strip shows net inventory change after ingredients are consumed.\n\nMoonlight → Shards → Essence → Elixirs → Stardust"),
    ("offline", "While you are away", "Each sanctuary continues producing while you visit another slot or close the game. There is no offline time cap. Purchases and research never happen automatically.\n\nOnline charms rest while you are away. Offline charms work only while away. Combined charms work in both conditions. An expired charm stops contributing immediately, even during a long absence.\n\nYour welcome-back page reports net changes, including ingredients used by converters."),
    ("research", "Ink and resonance", "Each building has three research inscriptions. Spend its output resource to double its capacity. A converter's ingredient demand grows with its output.\n\nThe first inscription earns a restoration seal and reveals its talisman recipe. Research resets at Reawakening; your discoveries and this book remain."),
    ("distillery", "The art of distillation", "3 Shards → 1 Essence\n\nThe Essence Distillery consumes Shards automatically. If your gardens cannot keep up, the distillery slows to match their supply. Nothing is wasted or allowed to become negative.\n\nImprove upstream production before adding more hungry converters. Unlocking this stage also reveals offline charm recipes."),
    ("crucible", "A patient flame", "4 Essence → 1 Elixir\n\nPotion Crucibles need a steady flow of Essence. A large stockpile may temporarily hide a bottleneck: watch the net rates in the resource strip.\n\nThis stage reveals combined charms, whose timers run both online and offline."),
    ("astral", "Conversations with stars", "5 Elixirs → 1 Stardust\n\nThe Astral Circle hangs deliberately above the terrace. Its Stardust funds research, charms, and the Star Compass talisman.\n\nAll Stardust earned during a run counts toward Reawakening, including what you have already spent."),
    ("charms", "Three hooks, five arts", "Crafting opens after your first research inscription. A charm targets one resource. Hold or equip only one charm of that type, regardless of recipe or mode; three different charms can hang on the rack.\n\nChoose +40% for 15 eligible minutes or +20% for 60. Online charms tick only in the loaded sanctuary, offline charms only while away, and combined charms in both. Minimized windows still count as online.\n\nStored charms do not tick. Equipping starts their clock; dismantling destroys them without a refund. Charms reset at Reawakening."),
    ("talismans", "Constellations made solid", "Each first research inscription reveals a permanent talisman recipe. Trace the reference constellation by clicking its stars in order. Undo, Reset, and Hint are free; mistakes cost no materials. Payment happens only after a complete, valid trace.\n\nEach of the five talismans has its own collection slot and grants +20% to its resource. All owned talismans are active. Their bonuses add to charms, then multiply by Moon Seals.\n\nAt Reawakening you may retain up to three. Unselected talismans are lost, but their recipes remain discoverable."),
    ("reawakening", "The pages we carry", "Establish all five buildings and earn 120 Stardust this run to Reawaken. The first ritual grants three Moon Seals; each cumulative seal adds 10% production. Waiting longer grants more, with diminishing returns.\n\nChoose up to three talismans to retain. Mana, materials, buildings, research, charms, and unselected talismans reset. Your chosen talismans, Moon Seals, discoveries, tome history, and settings remain.\n\nThe confirmation lists exactly what you keep and lose."),
)
CHAPTER_ADDITIONS = {
    "research": "\n\nStation stages: default buildings are Weathered. The first inscription restores them; the second Awakens them with additional effects; the third creates a Masterwork. Every purchase still doubles capacity.",
    "charms": "Choose a target, tier I–IV, duration style, and Online/Offline/Combined mode. Gentle grants +10/20/30/40% for 60 eligible minutes; Intense grants +25/50/75/100% for 15. Both styles use the same mixed-material recipe.\n\nTier I needs a research inscription; tiers II, III, and IV require an owned Distillery, Crucible, and Astral Circle respectively. Offline recipes cost 1.25×; Combined recipes cost 1.5×.\n\nOnline timers pause while away; Offline timers pause while loaded; Combined timers always run. Three different active charms fit on the rack, and you may hold only one charm per target type. Stored charms do not tick. Dismantling gives no refund.",
    "talismans": "\n\nTalismans now require mixed materials. All ingredients are checked and paid together when you bind a completed constellation. Previously crafted talismans remain yours.",
    "reawakening": "\n\nRestoration projects, their bonuses, spirit encounters, and active blessings also reset. Global display and music settings stay unchanged.",
}
CHAPTERS = tuple((key,title,CHAPTER_ADDITIONS[key] if key=="charms" else body+CHAPTER_ADDITIONS.get(key,"")) for key,title,body in CHAPTERS) + (
    ("restoration","Small works of wonder","The Restoration bench offers five visible improvements, each granting +5% to its resource for the current run. Buy each once using mixed materials. Reawakening removes the artwork and bonus.\n\nLantern Path → Mana\nCrystal Planters → Shards\nGlasswork Shelves → Essence\nHearth Mosaic → Elixirs\nCelestial Inlay → Stardust"),
    ("transmutation","Unweaving the elements","Recover earlier materials from later ones, paying Mana for the work:\n\n1 Stardust + 50 Mana → 3 Elixirs\n1 Elixir + 15 Mana → 2 Essence\n1 Essence + 5 Mana → 2 Shards\n\nOwn the source station to unlock its recipe. Choose 1, 10, or Max and review the complete totals. This is deliberately lossy, not a way to make new Stardust. Recovered materials do not count as lifetime earnings."),
    ("spirits","A visitor in the sky","After two resources become available, a spirit crosses the sanctuary every 2–4 minutes of visible play. Click it within 15 seconds to receive two choices of resource and bonus.\n\nChoose one blessing: +15% to +50% for two online minutes. It uses no charm hook and adds to other bonuses. Only one blessing may be active. Its timer pauses while away from this slot.\n\nThere is no penalty for missing a visitor. Encounters wait while minimized, in menus, or reading the tome. Reduced motion shows a stationary spirit."),
)
CHAPTERS = tuple((key,title,body) for key,title,body in CHAPTERS if key not in ("charms","restoration","spirits")) + (
    ("charms","Bodies, enchantments and infusions","Mana pays the work; Shards build a charm's body. Choose tier I–IV: Gentle grants +10/20/30/40% for 60 minutes; Intense +25/50/75/100% for 15. Tier II needs a Distillery, III a Crucible, IV a Circle.\n\nEssence specialises advanced targets and Offline/Combined modes. Mana and Shard targeting is free of Essence. Elixir infusion adds 50% initial duration after the Crucible is established. Every ingredient and shortfall is shown before payment.\n\nOnly one charm of each target can be held, and three can be equipped. Online timers run only in a loaded slot, Offline only while away, Combined in both. Stored charms never tick. Crafting stats are fixed at creation."),
    ("restoration","Construction in crystal","Shards build the sanctuary. Each of five projects has five levels: +5%, +10%, +15%, +20%, and +25% to its associated resource. Sanctuary spells add their bonus once per built project.\n\nEach next level costs six times as many Shards and twice as much Mana. The first Lantern Path costs 100 Shards; its fifth level alone costs 129,600. The Celestial Inlay's fifth level costs 32.4 million Shards. These are long-term construction goals, not requirements for Reawakening.\n\nCards show current level, the next bonus, complete ingredient costs and shortages. Every level adds visible terrace detail. Existing projects migrate to Level I. All construction levels and their bonuses reset at Reawakening."),
    ("spirits","Celestial visitor","An ivory celestial moth crosses the sanctuary after 2–4 minutes of visible play. Click its luminous wings within 15 seconds and choose between two random resource blessings, +15% to +50% for two online minutes. The choice is untimed and saved.\n\nBlessings stack with crafting and do not occupy a hook. Missing a moth costs nothing. Visits pause behind pages and dialogs; reduced motion gives the moth a stationary pose."),
    ("enchantments","The branching spell tree","Open Enchantments in the Workshop to explore 18 connected nodes across Charmcraft, Deliveries and Sanctuary. Follow the constellation outward from its central star. Circular nodes show only icons and rank counts; hover for names and select a node for its description. Drag the starfield to pan; scroll to zoom. Fit tree restores the overview; Centre selected finds your current node. Selecting a node is free. Its detail panel shows current and next effects, all costs and missing ingredients before purchase.\n\nDelivery skills remain locked until you own a Crucible with its second inscription. Lasting Infusion requires an owned Crucible. Roots cost 250/750/2,250 Essence. Specialisations cost 1,000/3,000/9,000; advanced nodes cost 5,000; capstones cost 25,000. Shards pay for physical improvements and Elixirs for sustained magic, as listed on each node. Root rank one unlocks specialisations. Their second ranks unlock advanced nodes; both advanced nodes unlock the capstone.\n\nLasting Infusion increases new infused duration to +75%; Crystal Cutting reduces charm Shard costs by another 15 percentage points. Generous Parcels increases delivery gifts by 50%; Efficient Packing reduces future requests by 10%. Resonant Masonry adds two percentage points to each construction bonus; Careful Recovery yields 20% more reverse-transmutation output.\n\nAll paths remain open. Skills reset at Reawakening; existing charms keep crafted stats and contracts keep their saved terms. Previously purchased capstones remain active after migration."),
    ("recharge","Elixirs keep magic alive","Own a Crucible to infuse newly crafted charms or refill equipped, unexpired charms. Infusion adds 50% initial duration. Recharging returns a charm to its crafted maximum, never banking extra time.\n\nTier I–IV recharge costs start at 10/25/60/150 Elixirs and double with each refill of that charm. Charmcraft's capstone changes growth to ×1.6. Replacement charms start fresh; expired charms disappear. Legacy charms retain their old strength and full duration, with Tier II recharge pricing."),
    ("deliveries","The celestial courier","Own a Crucible with its second inscription to receive deliveries. A contract requests two of Shards, Essence and Elixirs, using 12–18 minutes of sustainable surplus with empty inventories and no temporary boosts. If fewer than two have surplus, improve upstream production.\n\nPayment is 20 minutes of baseline Mana production, increased by Delivery spells. Terms stay fixed until fulfilled or declined. Either action starts a 15-minute cooldown (as low as 12 with spells); time passes offline but contracts never accumulate. Gifts exclude requested materials and never increase prestige earnings.\n\nUpgrade upstream stations to make future contracts easier. No Mana or Stardust is ever requested."),
)
CHAPTERS=tuple((key,title,body.replace("Its Stardust funds research, charms, and the Star Compass talisman.","Its Stardust counts toward Reawakening and funds research and the Star Compass.")+ ("\n\nReawakening also clears spell-tree ranks, contracts, cooldowns, construction and blessings." if key=="reawakening" else "")) for key,title,body in CHAPTERS)
CHAPTERS=tuple((key,title,"The first Reawakening requires 120 run-earned Stardust and all five stations. Later runs require more: 280, 520, 1,590, 3,960, and onward. Your journal shows the current and next goal. Spent Stardust still counts.\n\nEach ritual grants Moon Seals and one permanent, stackable legacy choice. Base seal rewards start at three and increase by one every three completed Reawakenings; extra Stardust increases rewards with square-root scaling against the current goal. Each seal still adds 10% production.\n\nChoose Dawn, Crystal or Tide memory for +5% Mana, Shards or Essence per choice. The second Reawakening unlocks Ember memory (+5% Elixirs), the third Astral memory (+5% Stardust), and the fifth Moonweaver (+2% all resources). These bonuses add to other resource bonuses before Moon Seals.\n\nKeep up to three talismans. Materials, stations, research, charms, construction levels, spell ranks, courier offers and blessings reset. Legacy choices, Moon Seals and permanent records remain. Existing saves keep their current Stardust goal and receive unclaimed legacy choices for previous Reawakenings. Claim those on the Reawakening page without another reset." if key=="reawakening" else body) for key,title,body in CHAPTERS)
CHAPTER_KEYS = {chapter[0] for chapter in CHAPTERS}


def recipe_text(recipe):
    return " + ".join(f"{number(n)} {RESOURCES[i]}" for i,n in enumerate(recipe) if n)


def can_pay(state, recipe):
    return all(have+1e-8 >= need for have,need in zip(state.resources,recipe))


def pay(state, recipe):
    if not can_pay(state,recipe):
        return False
    state.resources = [max(0.,have-need) for have,need in zip(state.resources,recipe)]
    return True


@dataclass(frozen=True)
class Building:
    name: str
    subtitle: str
    cost: float
    growth: float
    rate: float
    ratio: float
    unlock: float
    research: tuple[float, float, float]
    colour: str
    story: str


BUILDINGS = (
    Building("Spirit Well", "A little light, drawn from the deep.", 30, 1.20, .65, 0, 0,
             (1000, 15000, 180000), "#91d3cb", "The old well sings again. Beneath the stones, something answers."),
    Building("Crystal Garden", "Where moonlight learns to take shape.", 60, 1.22, .30, 0, 0,
             (80, 1200, 12000), "#b9a1ed", "Violet crystals break through the soil, like flowers remembering spring."),
    Building("Essence Distillery", "Patience, glass, and a drop of wonder.", 700, 1.24, .12, 3, 1000,
             (30, 400, 4000), "#7cdbcb", "The first distillation carries the scent of rain on ancient stone."),
    Building("Potion Crucible", "Bottle the things a dream is made of.", 10000, 1.26, .035, 4, 30000,
             (12, 120, 1200), "#e0a586", "Amber warmth fills the atelier. Its hearth has found a purpose again."),
    Building("Astral Circle", "A quiet conversation with the stars.", 40000, 1.28, .010, 5, 200000,
             (6, 45, 300), "#dec679", "Above the circle, a constellation returns to a sky that had forgotten it."),
)


def number(value: float) -> str:
    if not math.isfinite(value):
        return "—"
    for threshold, suffix in ((1e15, "Q"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "k")):
        if abs(value) >= threshold:
            return f"{value / threshold:,.2f}{suffix}"
    if 0 < abs(value) < 1:
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{value:,.1f}" if abs(value) < 100 else f"{value:,.0f}"


def duration(seconds: float) -> str:
    seconds = int(max(0, seconds))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m" if hours else f"{minutes}m {remainder % 60}s"


@dataclass
class State:
    resources: list[float] = field(default_factory=lambda: [60., 0., 0., 0., 0.])
    owned: list[int] = field(default_factory=lambda: [0] * 5)
    research: list[int] = field(default_factory=lambda: [0] * 5)
    run_mana: float = 0.
    run_dust: float = 0.
    lifetime_mana: float = 0.
    played: float = 0.
    seals: int = 0
    awakenings: int = 0
    discoveries: list[str] = field(default_factory=list)
    journal: list[str] = field(default_factory=lambda: ["A key, a quiet ruin, and a sky full of possibilities."])
    reduced_motion: bool = False
    saved_at: float = field(default_factory=time.time)
    sanctuary_name: str = "A new sanctuary"
    tutorial_step: int = 0
    tutorial_skipped: bool = False
    tutorial_invite: bool = False
    tutorial_mana_start: float = 0.
    garden_selected: bool = False
    tome_opened: bool = False
    chapters_unlocked: list[str] = field(default_factory=lambda: ["first", "production", "offline"])
    chapters_read: list[str] = field(default_factory=list)
    charms: list[dict] = field(default_factory=list)
    talismans: list[int] = field(default_factory=list)
    legacy_imported: bool = False
    restorations: list[int] = field(default_factory=list)
    restoration_levels: list[int] = field(default_factory=lambda:[0]*5)
    rebirth_goal: float = PRESTIGE_TARGET
    legacies: list[int] = field(default_factory=lambda:[0]*len(LEGACIES))
    legacy_pending: int = 0
    spirit_wait: float = field(default_factory=lambda: random.uniform(120,240))
    spirit_remaining: float = 0.
    spirit_offer: list[dict] = field(default_factory=list)
    blessing: dict | None = None
    spell_ranks: dict = field(default_factory=lambda: {branch:[0,0,0,0] for branch in TREE})
    spell_advanced: dict = field(default_factory=lambda: {branch:[0,0] for branch in TREE})
    contracts: list[dict] = field(default_factory=list)
    delivery_cooldown: float = 0.

    @classmethod
    def parse(cls, data: dict) -> State:
        if not isinstance(data, dict) or set(data) != set(cls.__dataclass_fields__):
            raise ValueError("Save fields are missing or unsupported")
        state = cls(**data)
        if type(state.rebirth_goal) not in (int,float) or not math.isfinite(state.rebirth_goal) or state.rebirth_goal<PRESTIGE_TARGET:
            raise ValueError("Invalid Reawakening goal")
        if not isinstance(state.legacies,list) or len(state.legacies)!=len(LEGACIES) or any(type(n) is not int or n<0 for n in state.legacies) or type(state.legacy_pending) is not int or state.legacy_pending<0:
            raise ValueError("Invalid legacy choices")
        for name in ("resources", "owned", "research"):
            values = getattr(state, name)
            if not isinstance(values, list) or len(values) != 5:
                raise ValueError(f"Invalid {name}")
            for value in values:
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError(f"Invalid {name}")
                if name != "resources" and (type(value) is not int or value > (3 if name == "research" else 10000)):
                    raise ValueError(f"Invalid {name}")
        for name in ("run_mana", "run_dust", "lifetime_mana", "played", "saved_at", "seals", "awakenings"):
            value = getattr(state, name)
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid {name}")
        if type(state.seals) is not int or type(state.awakenings) is not int or type(state.reduced_motion) is not bool:
            raise ValueError("Invalid settings or prestige")
        for name in ("discoveries", "journal"):
            values = getattr(state, name)
            if not isinstance(values, list) or len(values) > 200 or any(not isinstance(v, str) or len(v) > 1000 for v in values):
                raise ValueError(f"Invalid {name}")
        if not isinstance(state.sanctuary_name, str) or not 1 <= len(state.sanctuary_name.strip()) <= 32:
            raise ValueError("Invalid sanctuary name")
        if type(state.tutorial_step) is not int or not 0 <= state.tutorial_step <= 5:
            raise ValueError("Invalid tutorial step")
        for name in ("tutorial_skipped", "tutorial_invite", "garden_selected", "tome_opened", "legacy_imported"):
            if type(getattr(state, name)) is not bool:
                raise ValueError("Invalid tutorial or migration status")
        if type(state.tutorial_mana_start) not in (int, float) or not math.isfinite(state.tutorial_mana_start) or state.tutorial_mana_start < 0:
            raise ValueError("Invalid tutorial production marker")
        for name in ("chapters_unlocked", "chapters_read"):
            values = getattr(state, name)
            if not isinstance(values, list) or any(not isinstance(v, str) or v not in CHAPTER_KEYS for v in values) or len(values) != len(set(values)):
                raise ValueError("Invalid tome chapters")
        if not isinstance(state.talismans, list) or any(type(i) is not int or not 0 <= i < 5 for i in state.talismans) or len(state.talismans) != len(set(state.talismans)):
            raise ValueError("Invalid talismans")
        if not isinstance(state.charms, list) or len(state.charms) > 5:
            raise ValueError("Invalid charm inventory")
        types = set()
        for charm in state.charms:
            if not isinstance(charm, dict) or set(charm) != {"target", "mode", "long", "remaining", "equipped", "tier", "bonus", "max_duration", "recharges", "infused"}:
                raise ValueError("Invalid charm")
            target = charm["target"]
            if type(target) is not int or not 0 <= target < 5 or target in types:
                raise ValueError("Duplicate or invalid charm type")
            types.add(target)
            if type(charm["tier"]) is not int or not 1 <= charm["tier"] <= 4 or type(charm["bonus"]) not in (int,float) or not math.isfinite(charm["bonus"]) or not 0 < charm["bonus"] <= 1.16:
                raise ValueError("Invalid charm potency")
            if charm["mode"] not in ("online", "offline", "both") or type(charm["long"]) is not bool or type(charm["equipped"]) is not bool:
                raise ValueError("Invalid charm recipe")
            remaining = charm["remaining"]
            if type(charm["max_duration"]) not in (int,float) or not 0 < charm["max_duration"] <= 8190 or type(charm["recharges"]) is not int or not 0 <= charm["recharges"] <= 1000 or type(charm["infused"]) is not bool:
                raise ValueError("Invalid recharge data")
            if type(remaining) not in (int, float) or not math.isfinite(remaining) or not 0 < remaining <= charm["max_duration"]:
                raise ValueError("Invalid charm duration")
        if sum(c["equipped"] for c in state.charms) > 3:
            raise ValueError("Charm rack is over capacity")
        if not isinstance(state.restorations,list) or any(type(i) is not int or not 0<=i<5 for i in state.restorations) or len(set(state.restorations)) != len(state.restorations):
            raise ValueError("Invalid restoration projects")
        if not isinstance(state.restoration_levels,list) or len(state.restoration_levels)!=5 or any(type(n) is not int or not 0<=n<=CONSTRUCTION_MAX_LEVEL for n in state.restoration_levels):
            raise ValueError("Invalid construction levels")
        for name,maximum in (("spirit_wait",240),("spirit_remaining",15)):
            value=getattr(state,name)
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=maximum:
                raise ValueError("Invalid spirit timing")
        if not isinstance(state.spirit_offer,list) or len(state.spirit_offer) not in (0,2):
            raise ValueError("Invalid spirit offer")
        for offer in state.spirit_offer:
            if not isinstance(offer,dict) or set(offer)!={"target","percent"} or type(offer["target"]) is not int or not 0<=offer["target"]<5 or type(offer["percent"]) is not int or offer["percent"] not in SPIRIT_PERCENTAGES:
                raise ValueError("Invalid spirit choice")
        if state.spirit_offer and state.spirit_offer[0]["target"]==state.spirit_offer[1]["target"]:
            raise ValueError("Spirit choices must differ")
        if state.blessing is not None:
            b=state.blessing
            if not isinstance(b,dict) or set(b)!={"target","percent","remaining"} or type(b["target"]) is not int or not 0<=b["target"]<5 or type(b["percent"]) is not int or b["percent"] not in SPIRIT_PERCENTAGES or type(b["remaining"]) not in (int,float) or not math.isfinite(b["remaining"]) or not 0<b["remaining"]<=120:
                raise ValueError("Invalid spirit blessing")
        if not isinstance(state.spell_ranks,dict) or set(state.spell_ranks)!=set(TREE):
            raise ValueError("Invalid spell tree")
        for ranks in state.spell_ranks.values():
            if not isinstance(ranks,list) or len(ranks)!=4 or any(type(v) is not int or not 0<=v<=(1 if i==3 else 3) for i,v in enumerate(ranks)):
                raise ValueError("Invalid spell ranks")
        if not isinstance(state.spell_advanced,dict) or set(state.spell_advanced)!=set(TREE) or any(not isinstance(v,list) or len(v)!=2 or any(type(n) is not int or n not in (0,1) for n in v) for v in state.spell_advanced.values()):
            raise ValueError("Invalid advanced spells")
        if type(state.delivery_cooldown) not in (int,float) or not math.isfinite(state.delivery_cooldown) or not 0<=state.delivery_cooldown<=900:
            raise ValueError("Invalid delivery timer")
        if not isinstance(state.contracts,list) or len(state.contracts)>2:
            raise ValueError("Invalid contracts")
        for offer in state.contracts:
            if not isinstance(offer,dict) or set(offer)!={"cost","reward"}:
                raise ValueError("Invalid contract")
            for vector in offer.values():
                if not isinstance(vector,list) or len(vector)!=5 or any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in vector):
                    raise ValueError("Invalid contract quantities")
            if offer["cost"][0] or offer["cost"][4] or sum(v>0 for v in offer["cost"])!=2 or offer["reward"][4]:
                raise ValueError("Invalid contract materials")
        return state


class Economy:
    """Acyclic continuous flows; integrate exactly between inventory-depletion events."""
    def __init__(self, state: State | None = None):
        self.state = state or State()

    @property
    def multiplier(self):
        return 1 + .1 * self.state.seals

    def unlocked(self, index):
        return self.state.run_mana >= BUILDINGS[index].unlock

    def bonus(self, index, offline=False):
        bonus = .2 if index in self.state.talismans else 0.
        bonus += sum(count*entry[3] for count,entry in zip(self.state.legacies,LEGACIES) if index in entry[2])
        ranks=self.state.spell_ranks["Sanctuary"]
        bonus += self.construction_bonus(index)
        bonus += .1 if index==0 and ranks[3] else 0.
        blessing=self.state.blessing
        if not offline and blessing and blessing["target"]==index:
            bonus += blessing["percent"]/100
        for charm in self.state.charms:
            if charm["target"] == index and self.charm_active(charm, offline):
                bonus += charm["bonus"]
        return 1 + bonus

    def construction_level(self,index):
        return max(self.state.restoration_levels[index],int(index in self.state.restorations))

    def construction_bonus(self,index,level=None):
        level=self.construction_level(index) if level is None else level
        return (.05*level+.01*self.state.spell_ranks["Sanctuary"][1]+.02*self.state.spell_advanced["Sanctuary"][0]) if level else 0.

    @staticmethod
    def charm_active(charm, offline=False):
        return charm["equipped"] and charm["remaining"] > 1e-8 and charm["mode"] in (("offline", "both") if offline else ("online", "both"))

    def capacities(self, offline=False):
        return [b.rate * n * 2 ** tier * self.multiplier * self.bonus(i, offline)
                for i, (b, n, tier) in enumerate(zip(BUILDINGS, self.state.owned, self.state.research))]

    def flows(self, offline=False):
        capacity = self.capacities(offline)
        flows = capacity[:]
        flows[0] += self.multiplier * self.bonus(0, offline)
        for i in range(2, 5):
            if self.state.resources[i - 1] <= 1e-8:
                flows[i] = min(capacity[i], flows[i - 1] / BUILDINGS[i].ratio)
        net = flows[:]
        for i in range(2, 5):
            net[i - 1] -= flows[i] * BUILDINGS[i].ratio
        return flows, net

    def advance(self, seconds, offline=False):
        if not math.isfinite(seconds) or seconds < 0:
            return
        self.state.delivery_cooldown=max(0.,self.state.delivery_cooldown-seconds)
        remaining = seconds
        while remaining > 1e-9:
            flows, net = self.flows(offline)
            step = remaining
            ticking = [c for c in self.state.charms if self.charm_active(c, offline)]
            if ticking:
                step = min(step, min(c["remaining"] for c in ticking))
            if not offline and self.state.blessing:
                step=min(step,self.state.blessing["remaining"])
            for stock, rate in zip(self.state.resources, net):
                if rate < -1e-10 and stock > 1e-8:
                    step = min(step, stock / -rate)
            for i, rate in enumerate(net):
                self.state.resources[i] = max(0., self.state.resources[i] + rate * step)
                if self.state.resources[i] < 1e-8:
                    self.state.resources[i] = 0.
            self.state.run_mana += flows[0] * step
            self.state.lifetime_mana += flows[0] * step
            self.state.run_dust += flows[4] * step
            self.state.played += step
            if not offline and self.state.blessing:
                self.state.blessing["remaining"]-=step
                if self.state.blessing["remaining"]<=1e-8:
                    self.state.blessing=None
                    self.record("The visitor’s blessing fades gently into the stars.")
            for charm in ticking:
                charm["remaining"] = max(0., charm["remaining"] - step)
                if charm["remaining"] <= 1e-8:
                    self.record(f"The {RESOURCES[charm['target']]} charm has faded. Its hook is free again.")
            self.state.charms = [c for c in self.state.charms if c["remaining"] > 1e-8]
            remaining -= step
        self.discover()
        Guide(self).update()

    def offline(self, now):
        elapsed = max(0., now - self.state.saved_at)
        before = self.state.resources[:]
        self.advance(elapsed, offline=True)
        self.state.saved_at = now
        return elapsed, [a - b for a, b in zip(self.state.resources, before)]

    def cost(self, index, quantity=1):
        b = BUILDINGS[index]
        if quantity <= 0:
            return 0.
        try:
            return b.cost * b.growth ** self.state.owned[index] * (b.growth ** quantity - 1) / (b.growth - 1)
        except OverflowError:
            return math.inf

    def affordable(self, index):
        price = self.cost(index)
        if not math.isfinite(price):
            return 0
        b = BUILDINGS[index]
        count = max(0, int(math.log1p(self.state.resources[0] * (b.growth - 1) / price) / math.log(b.growth)))
        while count and self.cost(index, count) > self.state.resources[0] + 1e-8:
            count -= 1
        while self.cost(index, count + 1) <= self.state.resources[0] + 1e-8:
            count += 1
        return count

    def buy(self, index, quantity=1):
        if quantity == "max":
            quantity = self.affordable(index)
        if type(quantity) is not int or quantity < 1 or not self.unlocked(index):
            return False
        price = self.cost(index, quantity)
        if price > self.state.resources[0] + 1e-8:
            return False
        first = self.state.owned[index] == 0
        self.state.resources[0] = max(0., self.state.resources[0] - price)
        self.state.owned[index] += quantity
        if first:
            self.record(BUILDINGS[index].story)
        self.discover()
        return True

    def study(self, index):
        tier = self.state.research[index]
        if tier >= 3 or not self.state.owned[index]:
            return False
        price = BUILDINGS[index].research[tier]
        if self.state.resources[index] + 1e-8 < price:
            return False
        self.state.resources[index] = max(0., self.state.resources[index] - price)
        self.state.research[index] += 1
        self.record(f"{BUILDINGS[index].name}: {('Attunement', 'Resonance', 'Transcendence')[tier]} inscribed. Production doubled.")
        self.discover()
        return True

    def record(self, text):
        self.state.journal.append(text)
        self.state.journal = self.state.journal[-40:]

    def discover(self):
        for i, b in enumerate(BUILDINGS):
            for key, condition, text in (
                (f"unlock-{i}", self.unlocked(i), f"A new page opens: {b.name}."),
                (f"study-{i}", self.state.research[i] >= 1, f"Restoration seal earned: {b.name}."),
            ):
                if condition and key not in self.state.discoveries:
                    self.state.discoveries.append(key)
                    self.record(text)

    def reward(self):
        if not all(self.state.owned) or self.state.run_dust < self.state.rebirth_goal:
            return 0
        base=3+self.state.awakenings//3
        return max(base,int(base*math.sqrt(self.state.run_dust/self.state.rebirth_goal)))

    def choose_legacy(self,choice):
        if type(choice) is not int or not 0<=choice<len(LEGACIES) or not self.state.legacy_pending or self.state.awakenings<LEGACIES[choice][1]:
            return False
        self.state.legacies[choice]+=1
        self.state.legacy_pending-=1
        self.record(LEGACIES[choice][0]+" joins your permanent legacy.")
        return True

    def reawaken(self, retain=(), legacy_choice=None):
        reward = self.reward()
        if not reward or len(retain) > 3 or len(set(retain)) != len(retain) or any(i not in self.state.talismans for i in retain):
            return False
        if legacy_choice is not None and (type(legacy_choice) is not int or not 0<=legacy_choice<len(LEGACIES) or self.state.awakenings+1<LEGACIES[legacy_choice][1]):
            return False
        old = self.state
        self.state = State(seals=old.seals + reward, awakenings=old.awakenings + 1,
                           lifetime_mana=old.lifetime_mana, played=old.played,
                           discoveries=old.discoveries[:], journal=old.journal[:],
                           reduced_motion=old.reduced_motion, sanctuary_name=old.sanctuary_name,
                           tutorial_step=old.tutorial_step, tutorial_skipped=old.tutorial_skipped,
                           tutorial_mana_start=0., garden_selected=old.garden_selected, tome_opened=old.tome_opened,
                           chapters_unlocked=old.chapters_unlocked[:], chapters_read=old.chapters_read[:],
                           talismans=list(retain), legacy_imported=old.legacy_imported,
                           rebirth_goal=rebirth_target(old.awakenings+1),legacies=old.legacies[:],legacy_pending=old.legacy_pending+1)
        if legacy_choice is not None:self.choose_legacy(legacy_choice)
        self.record(f"Reawakening {self.state.awakenings}. {reward} Moon Seals remain; the atelier remembers.")
        return True


class Guide:
    def __init__(self, economy):
        self.economy = economy

    def update(self):
        s = self.economy.state
        conditions = {"research": any(s.research) or any(n and tier < 3 and s.resources[i] >= BUILDINGS[i].research[tier]
                                      for i, (n, tier) in enumerate(zip(s.owned, s.research))),
                      "distillery": self.economy.unlocked(2), "crucible": self.economy.unlocked(3),
                      "astral": self.economy.unlocked(4), "charms": any(s.research),
                      "talismans": any(s.research),
                      "restoration": any(s.research), "transmutation": s.owned[2]>0,
                      "spirits": s.owned[1]>0, "enchantments":s.owned[2]>0, "recharge":s.owned[3]>0, "deliveries":s.owned[3]>0 and s.research[3]>=2,
                      "reawakening": all(s.owned) and s.run_dust >= s.rebirth_goal*.8}
        for key, condition in conditions.items():
            if condition and key not in s.chapters_unlocked:
                s.chapters_unlocked.append(key)
                if key in ("charms","restoration","enchantments","recharge","deliveries","transmutation"):
                    self.economy.record("Workshop discovery: "+dict((k,t) for k,t,_ in CHAPTERS)[key]+". A new tome page awaits.")
        if not s.tutorial_skipped and not s.tutorial_invite:
            while s.tutorial_step < 5:
                done = (s.owned[0] > 0, s.run_mana >= s.tutorial_mana_start+1,
                        s.owned[1] > 0, s.garden_selected, s.tome_opened)[s.tutorial_step]
                if not done:
                    break
                s.tutorial_step += 1
                if s.tutorial_step == 1:
                    s.tutorial_mana_start = s.run_mana

    def read(self, chapter):
        if chapter not in CHAPTER_KEYS:
            return False
        if chapter not in self.economy.state.chapters_read:
            self.economy.state.chapters_read.append(chapter)
        return True

    def restart(self):
        s = self.economy.state
        s.tutorial_step = 0
        s.tutorial_skipped = s.tutorial_invite = s.garden_selected = s.tome_opened = False
        s.tutorial_mana_start = s.run_mana
        self.update()


class Crafting:
    def __init__(self, economy):
        self.economy = economy

    def charm(self, target):
        return next((c for c in self.economy.state.charms if c["target"] == target), None)

    def price(self,target,long=False,mode="online",tier=1,infused=False):
        recipe=list(CHARM_RECIPES[tier-1])
        recipe[2]={0:0,1:0,2:8,3:20,4:50}[target]*tier
        recipe[2]+={"online":(0,)*4,"offline":(10,40,120,300),"both":(25,100,300,800)}[mode][tier-1]
        recipe[3]=RECHARGE_COSTS[tier-1] if infused else 0
        return tuple(math.ceil(n*(1-.05*self.economy.state.spell_ranks["Charmcraft"][0]-(.15*self.economy.state.spell_advanced["Charmcraft"][1] if i==1 else 0))-1e-9) for i,n in enumerate(recipe))

    def crafted_stats(self,long,tier,infused=False):
        ranks=self.economy.state.spell_ranks["Charmcraft"]
        return tier*(.1 if long else .25)+.05*ranks[2], (3600 if long else 900)*(1+.1*ranks[1])*((1.75 if self.economy.state.spell_advanced["Charmcraft"][0] else 1.5) if infused else 1)

    def tier_unlocked(self,tier):
        s=self.economy.state
        return any(s.research) and (tier==1 or s.owned[tier]>0)

    def can_craft(self, target, long=False, mode="online", tier=1, infused=False):
        s = self.economy.state
        unlocked_mode = mode == "online" or (mode == "offline" and s.owned[2]) or (mode == "both" and s.owned[3])
        return (self.tier_unlocked(tier) and s.owned[target] > 0 and unlocked_mode and not self.charm(target)
                and (not infused or s.owned[3]) and can_pay(s,self.price(target,long,mode,tier,infused)))

    def craft(self, target, long=False, mode="online", tier=1, infused=False):
        if not self.can_craft(target, long, mode, tier, infused):
            return False
        s = self.economy.state
        pay(s,self.price(target,long,mode,tier,infused))
        bonus,maximum=self.crafted_stats(long,tier,infused)
        s.charms.append(dict(target=target,mode=mode,long=long,remaining=maximum,max_duration=maximum,recharges=0,infused=infused,equipped=False,tier=tier,bonus=bonus))
        self.economy.record(f"A {RESOURCES[target]} charm waits beside the rack.")
        return True

    def equip(self, target):
        charm = self.charm(target)
        if not charm or charm["equipped"] or sum(c["equipped"] for c in self.economy.state.charms) >= 3:
            return False
        charm["equipped"] = True
        return True

    def dismantle(self, target):
        charm = self.charm(target)
        if not charm:
            return False
        self.economy.state.charms.remove(charm)
        return True

    def talisman_unlocked(self, target):
        s = self.economy.state
        return s.research[target] > 0 or f"study-{target}" in s.discoveries

    def can_talisman(self, target):
        s = self.economy.state
        return self.talisman_unlocked(target) and target not in s.talismans and can_pay(s,TALISMAN_COSTS[target])

    def finish_talisman(self, puzzle):
        if not puzzle.complete or not self.can_talisman(puzzle.target):
            return False
        s = self.economy.state
        pay(s,TALISMAN_COSTS[puzzle.target])
        s.talismans.append(puzzle.target)
        self.economy.record(f"{TALISMAN_NAMES[puzzle.target]} takes its place in the collection.")
        return True

    def restore(self,target):
        s=self.economy.state
        level=self.economy.construction_level(target)
        if not any(s.research) or not s.owned[target] or level>=CONSTRUCTION_MAX_LEVEL or not pay(s,self.restoration_price(target)):
            return False
        if target not in s.restorations:s.restorations.append(target)
        s.restoration_levels[target]=level+1
        self.economy.record(f"{RESTORATION_NAMES[target]} reaches level {level+1}. +{self.economy.construction_bonus(target)*100:g}% {RESOURCES[target]} until Reawakening.")
        return True

    def restoration_price(self,target):
        level=self.economy.construction_level(target)
        if level>=CONSTRUCTION_MAX_LEVEL:return (0,)*5
        return tuple(math.ceil(n*((CONSTRUCTION_MANA_GROWTH if i==0 else CONSTRUCTION_SHARD_GROWTH)**level)*(1-.05*self.economy.state.spell_ranks["Sanctuary"][0])-1e-9) for i,n in enumerate(RESTORATION_COSTS[target]))

    def recharge_price(self,charm,extra=0):
        growth=1.6 if self.economy.state.spell_ranks["Charmcraft"][3] else 2
        return math.ceil(RECHARGE_COSTS[charm["tier"]-1]*growth**(charm["recharges"]+extra))

    def recharge(self,target):
        charm=self.charm(target)
        if not self.economy.state.owned[3] or not charm or not charm["equipped"] or not 0<charm["remaining"]<charm["max_duration"]:
            return False
        if not pay(self.economy.state,(0,0,0,self.recharge_price(charm),0)):
            return False
        charm["remaining"]=charm["max_duration"]
        charm["recharges"]+=1
        return True

    def transmutation(self,source,quantity=1):
        if source not in (2,3,4):
            return (0,)*5,(0,)*5,0
        fee={2:5,3:15,4:50}[source]*(1-.1*self.economy.state.spell_ranks["Sanctuary"][2])
        s=self.economy.state
        if quantity=="max":
            quantity=int(min(s.resources[source],s.resources[0]//fee))
        if type(quantity) is not int or quantity<1 or not s.owned[source]:
            quantity=0
        cost=[0]*5
        output=[0]*5
        cost[0],cost[source]=fee*quantity,quantity
        output[source-1]=(3 if source==4 else 2)*quantity*(1+.2*s.spell_advanced["Sanctuary"][1])
        return tuple(cost),tuple(output),quantity

    def transmute(self,source,quantity=1):
        cost,output,count=self.transmutation(source,quantity)
        if not count or not pay(self.economy.state,cost):
            return False
        self.economy.state.resources=[a+b for a,b in zip(self.economy.state.resources,output)]
        return True


class SpellTree:
    def __init__(self,economy):
        self.economy=economy

    def price(self,branch,node):
        rank=self.rank(branch,node)
        if rank>=self.maximum(node):
            return (0,)*5
        recipe=[0,0,0,0,0]
        recipe[2]=5000 if node>=4 else 25000 if node==3 else ((250,750,2250) if node==0 else (1000,3000,9000))[rank]
        if node<3:
            resource,costs=SPELL_SECONDARY[branch][node]
            recipe[resource]=costs[rank]
        elif node==3:
            recipe[1],recipe[3]={"Charmcraft":(10000,200),"Deliveries":(8000,150),"Sanctuary":(20000,0)}[branch]
        else:
            resource,cost={"Charmcraft":((3,80),(1,6000)),"Deliveries":((3,80),(1,6000)),"Sanctuary":((1,10000),(3,80))}[branch][node-4]
            recipe[resource]=cost
        return tuple(recipe)

    def rank(self,branch,node):
        return (self.economy.state.spell_ranks[branch][node] if node<4 else self.economy.state.spell_advanced[branch][node-4])

    @staticmethod
    def maximum(node):
        return 3 if node<3 else 1

    @staticmethod
    def name(branch,node):
        return TREE[branch][node] if node<4 else ADVANCED_NAMES[branch][node-4]

    @staticmethod
    def prerequisites(node):
        return () if node==0 else ((0,1),) if node in (1,2) else ((node-3,2),) if node>=4 else ((4,1),(5,1))

    def effect(self,branch,node,rank=None):
        rank=self.rank(branch,node) if rank is None else rank
        if node>=3:
            return SPELL_EFFECTS[branch][node] if rank else "Not yet learned"
        increments={"Charmcraft":(5,10,5),"Deliveries":(10,1,1),"Sanctuary":(5,1,10)}[branch]
        return SPELL_EFFECTS[branch][node].format(v=rank*increments[node])

    def available(self,branch,node):
        return not self.unlock_reason(branch,node) and self.rank(branch,node)<self.maximum(node) and all(self.rank(branch,n)>=r for n,r in self.prerequisites(node))

    def unlock_reason(self,branch,node):
        s=self.economy.state
        if not s.owned[2]:return "Own an Essence Distillery to unlock the spell tree."
        if branch=="Deliveries" and (not s.owned[3] or s.research[3]<2):
            return "Unlock Deliveries: own a Potion Crucible and complete its second inscription."
        if branch in ("Charmcraft","Sanctuary") and not any(s.research):
            return "Complete a first research inscription to unlock charms and construction."
        if branch=="Charmcraft" and node==4 and not s.owned[3]:
            return "Own a Potion Crucible to unlock Elixir infusion."
        return ""

    def buy(self,branch,node):
        if not self.available(branch,node) or not pay(self.economy.state,self.price(branch,node)):
            return False
        if node<4:
            self.economy.state.spell_ranks[branch][node]+=1
        else:
            self.economy.state.spell_advanced[branch][node-4]+=1
        return True


class Deliveries:
    def __init__(self,economy,rng=None):
        self.economy=economy
        self.rng=rng or random.Random()

    def unlocked(self):
        s=self.economy.state
        return s.owned[3]>0 and s.research[3]>=2

    def baseline(self):
        state=State.parse(asdict(self.economy.state))
        state.resources=[0.]*5
        state.charms=[]
        state.blessing=None
        game=Economy(state)
        return game.flows()

    def generate(self):
        s=self.economy.state
        if not self.unlocked() or s.contracts or s.delivery_cooldown>0:
            return False
        gross,net=self.baseline()
        eligible=[i for i in (1,2,3) if net[i]>1e-8]
        if len(eligible)<2:
            return False
        for _ in range(2 if s.spell_ranks["Deliveries"][3] else 1):
            targets=self.rng.sample(eligible,2)
            cost=[0.]*5
            reward=[0.]*5
            for i in targets:
                cost[i]=max(1,math.ceil(net[i]*self.rng.uniform(720,1080)*(1-.1*s.spell_advanced["Deliveries"][1])))
            reward[0]=net[0]*1200*(1+.1*s.spell_ranks["Deliveries"][0])
            gifts=[i for i in (1,2,3) if i not in targets and s.owned[i]]
            if gifts:
                i=gifts[0]
                reward[i]=gross[i]*60*s.spell_ranks["Deliveries"][1]*(1+.5*s.spell_advanced["Deliveries"][0])
            s.contracts.append(dict(cost=cost,reward=reward))
        return True

    def finish(self,index=None):
        s=self.economy.state
        if not s.contracts:
            return False
        if index is not None:
            if type(index) is not int or not 0<=index<len(s.contracts):
                return False
            offer=s.contracts[index]
            if not pay(s,offer["cost"]):
                return False
            s.resources=[a+b for a,b in zip(s.resources,offer["reward"])]
        s.contracts=[]
        s.delivery_cooldown=900-60*s.spell_ranks["Deliveries"][2]
        return True


class Encounters:
    def __init__(self,economy,rng=None):
        self.economy=economy
        self.rng=rng or random.Random()

    def eligible(self):
        return [0]+[i for i in range(1,5) if self.economy.state.owned[i]]

    def advance(self,seconds,visible=True):
        s=self.economy.state
        if not visible or seconds<=0 or s.spirit_offer or len(self.eligible())<2:
            return False
        if s.spirit_remaining>0:
            s.spirit_remaining=max(0.,s.spirit_remaining-seconds)
            if s.spirit_remaining==0:
                s.spirit_wait=self.rng.uniform(120,240)
                return True
        else:
            s.spirit_wait=max(0.,s.spirit_wait-seconds)
            if s.spirit_wait==0 and not s.blessing:
                s.spirit_remaining=15.
                return True
        return False

    def capture(self):
        s=self.economy.state
        if not s.spirit_remaining or s.spirit_offer or s.blessing or len(self.eligible())<2:
            return False
        s.spirit_offer=[dict(target=i,percent=self.rng.choice(SPIRIT_PERCENTAGES)) for i in self.rng.sample(self.eligible(),2)]
        s.spirit_remaining=0.
        return True

    def choose(self,index):
        s=self.economy.state
        if index not in (0,1) or len(s.spirit_offer)!=2 or s.blessing:
            return False
        s.blessing=dict(s.spirit_offer[index],remaining=120.)
        self.dismiss()
        return True

    def dismiss(self):
        s=self.economy.state
        s.spirit_offer=[]
        s.spirit_remaining=0.
        s.spirit_wait=self.rng.uniform(120,240)


class Constellation:
    """An ordered trace; UI-free so completion/payment can be tested independently."""
    def __init__(self, target):
        self.target = target
        self.count = 6 + target
        self.path = []
        self.order = list(range(self.count))
        random.Random(73+target).shuffle(self.order)
        self.points = [(math.cos(2*math.pi*i/self.count-math.pi/2),
                        math.sin(2*math.pi*i/self.count-math.pi/2)) for i in range(self.count)]

    @property
    def complete(self):
        return self.path == self.order

    def select(self, star):
        if self.complete or star != self.order[len(self.path)]:
            return False
        self.path.append(star)
        return True

    def undo(self):
        if self.path:
            self.path.pop()

    def hint(self):
        return None if self.complete else self.order[len(self.path)]


class SaveStore:
    def __init__(self, path=None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
        self.path = Path(path) if path else base / "StarstruckAtelier" / "slot-1.json"
        self.backup = self.path.with_suffix(".backup.json")
        self.blocked = False

    def read(self, path):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") not in (1,2,3,4,5,6,SAVE_VERSION):
            raise ValueError("Unsupported save version")
        if data["version"] == 1:
            old_fields = {"resources", "owned", "research", "run_mana", "run_dust", "lifetime_mana", "played", "seals", "awakenings", "discoveries", "journal", "reduced_motion", "saved_at"}
            if not isinstance(data.get("state"), dict) or set(data["state"]) != old_fields:
                raise ValueError("Invalid legacy save")
            defaults = asdict(State(tutorial_invite=True, tutorial_skipped=True))
            defaults.update(data["state"])
            data["state"] = defaults
        if data["version"]<3:
            upgraded=dict(data["state"])
            for name in ("restorations","spirit_wait","spirit_remaining","spirit_offer","blessing"):
                upgraded.setdefault(name,asdict(State())[name])
            upgraded["charms"]=[dict(charm,tier=0,bonus=.2 if charm["long"] else .4) for charm in upgraded["charms"]]
            data["state"]=upgraded
        if data["version"]<4:
            defaults=asdict(State())
            for name in ("spell_ranks","contracts","delivery_cooldown"):
                data["state"].setdefault(name,defaults[name])
            for charm in data["state"]["charms"]:
                charm["tier"]=charm.get("tier") or 2
                charm.update(max_duration=3600. if charm["long"] else 900.,recharges=0,infused=False)
        if data["version"]<5:
            data["state"].setdefault("spell_advanced",asdict(State())["spell_advanced"])
        if data["version"]<6:
            data["state"]["restoration_levels"]=[int(i in data["state"]["restorations"]) for i in range(5)]
        if data["version"]<7:
            data["state"]["rebirth_goal"]=PRESTIGE_TARGET
            data["state"]["legacies"]=[0]*len(LEGACIES)
            data["state"]["legacy_pending"]=data["state"]["awakenings"]
        return State.parse(data["state"])

    def load(self):
        errors = []
        for path in (self.path, self.backup):
            if path.exists():
                try:
                    state = self.read(path)
                    return state, "Recovered your sanctuary from its last-good backup." if errors else ""
                except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
                    errors.append(str(exc))
        self.blocked = bool(errors)
        return State(), ("Both available save copies could not be read. Your files are preserved. Start a fresh sanctuary?" if errors else "")

    def preserve_invalid(self):
        stamp = time.time_ns()
        for path in (self.path, self.backup):
            if path.exists():
                shutil.copy2(path, path.with_name(f"{path.stem}.unreadable-{stamp}.json"))
        self.blocked = False

    def save(self, state, touch=True):
        if self.blocked:
            raise OSError("Save recovery needs a decision before writing.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        saved_at = time.time() if touch else state.saved_at
        data = asdict(state)
        data["saved_at"] = saved_at
        payload = json.dumps({"version": SAVE_VERSION, "state": data}, indent=2, allow_nan=False)
        temporary = self.path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if self.path.exists():
            try:
                self.read(self.path)
            except (OSError, ValueError, KeyError, TypeError, OverflowError):
                pass  # Never replace a good backup with a broken primary.
            else:
                backup_tmp = self.backup.with_suffix(".tmp")
                shutil.copy2(self.path, backup_tmp)
                os.replace(backup_tmp, self.backup)
        os.replace(temporary, self.path)
        state.saved_at = saved_at


class SlotManager:
    """Exactly three stores; no loaded-slot state is shared between sanctuaries."""
    def __init__(self, directory=None, legacy=None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
        self.directory = Path(directory) if directory else base / "StarstruckAtelier"
        self.legacy = Path(legacy) if legacy else base / "MoonveilAtelier" / "save.json"
        self.marker = self.directory / "migration-complete.json"

    def store(self, slot):
        if type(slot) is not int or slot not in (1, 2, 3):
            raise ValueError("Choose a slot from 1 to 3")
        return SaveStore(self.directory / f"slot-{slot}.json")

    def occupied(self, slot):
        store = self.store(slot)
        return store.path.exists() or store.backup.exists()

    def summaries(self):
        return [(self.store(i).load() if self.occupied(i) else (None, "")) for i in (1, 2, 3)]

    def mark_migrated(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        temp = self.marker.with_suffix(".tmp")
        temp.write_text(json.dumps({"complete": True}), encoding="utf-8")
        os.replace(temp, self.marker)

    def migrate(self):
        if self.marker.exists():
            return ""
        # A crash after the slot write but before the marker must not import twice.
        for state, _ in self.summaries():
            if state and state.legacy_imported:
                self.mark_migrated()
                return ""
        legacy = SaveStore(self.legacy)
        if not legacy.path.exists() and not legacy.backup.exists():
            self.mark_migrated()
            return ""
        state, warning = legacy.load()
        if legacy.blocked:
            return "Your old Moonveil save could not be read. Its original files remain untouched."
        empty = next((i for i in (1, 2, 3) if not self.occupied(i)), None)
        if empty is None:
            return "Your Moonveil save is preserved; all three sanctuary slots are occupied."
        state.sanctuary_name = "Moonveil inheritance"
        state.legacy_imported = True
        state.tutorial_invite = state.tutorial_skipped = True
        self.store(empty).save(state, touch=False)
        self.mark_migrated()
        return f"Your old sanctuary was copied to slot {empty}. The original is preserved." + (" Its backup was used." if warning else "")

    def create(self, slot, name):
        if self.occupied(slot):
            raise ValueError("This slot already holds a sanctuary")
        name = name.strip()
        if not 1 <= len(name) <= 32:
            raise ValueError("Use a name between 1 and 32 characters")
        self.store(slot).save(State(sanctuary_name=name))

    def rename(self, slot, name):
        name = name.strip()
        if not 1 <= len(name) <= 32 or not self.occupied(slot):
            raise ValueError("Choose an occupied slot and a name of 1–32 characters")
        store = self.store(slot)
        state, _ = store.load()
        if store.blocked:
            raise ValueError("Recover this sanctuary before renaming it")
        state.sanctuary_name = name
        store.save(state, touch=False)  # Renaming must not discard offline time.

    def delete(self, slot):
        store = self.store(slot)
        for path in (store.path, store.backup):
            path.unlink(missing_ok=True)

    def open(self, slot, now=None):
        if not self.occupied(slot):
            raise ValueError("This sanctuary has not been created")
        store = self.store(slot)
        state, warning = store.load()
        if store.blocked:
            raise ValueError(warning)
        game = Economy(state)
        elapsed, gains = game.offline(time.time() if now is None else now)
        store.save(game.state, touch=False)
        return store, game, elapsed, gains, warning


class Preferences:
    DEFAULTS=dict(fullscreen=True,width=1440,height=900,fps=30,reduced_motion=False,
                  density="Standard",spirits=True,music=True,volume=40,shuffle=False,celestial_cursor=True,station_cursors=True)

    def __init__(self,path,reduced_motion=False):
        self.path=Path(path)
        self.values=dict(self.DEFAULTS,reduced_motion=reduced_motion)
        self.notice=""
        if self.path.exists():
            try:
                data=json.loads(self.path.read_text(encoding="utf-8"))
                for key,value in data.items():
                    if key not in self.DEFAULTS:
                        continue
                    if type(value) is not type(self.DEFAULTS[key]):
                        raise ValueError("Invalid setting type")
                    if key=="fps" and value not in (30,60) or key=="density" and value not in ("Low","Standard","High"):
                        raise ValueError("Invalid setting option")
                    if key=="volume" and not 0<=value<=100 or key in ("width","height") and not 400<=value<=12000:
                        raise ValueError("Invalid setting range")
                    self.values[key]=value
            except (OSError,ValueError,AttributeError) as exc:
                self.values=dict(self.DEFAULTS,reduced_motion=reduced_motion)
                self.notice="Preferences could not be read; defaults are in use. "+str(exc)

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temp=self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.values,indent=2),encoding="utf-8")
        os.replace(temp,self.path)


class MusicPlayer:
    """Stream local music only; no pygame display/event loop is created."""
    def __init__(self,directory,preferences,backend=None):
        self.directory=Path(directory)
        self.preferences=preferences
        self.backend=backend
        self.tracks=[]
        self.index=-1
        self.paused=False
        self.playing=False
        self.initialized=False
        self.status="No music loaded. Add tracks to assets/music and reload the playlist."
        self.warning=""
        self.reload()

    def init(self):
        if self.initialized:
            return True
        try:
            if self.backend is None:
                os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
                from pygame import mixer
                self.backend=mixer
            self.backend.init()
            self.initialized=True
            return True
        except Exception as exc:
            self.status="Audio unavailable; the game will continue silently. "+str(exc)
            return False

    def stop(self):
        if self.initialized:
            try:
                self.backend.music.stop()
            except Exception:
                pass
        self.playing=False
        self.paused=False

    def reload(self):
        self.stop()
        self.tracks=[]
        self.warning=""
        try:
            data=json.loads((self.directory/"playlist.json").read_text(encoding="utf-8"))
            names=data["tracks"]
            if not isinstance(names,list) or any(not isinstance(n,str) for n in names):
                raise ValueError("tracks must be a list of filenames")
            for name in names:
                path=(self.directory/name).resolve()
                if not path.is_relative_to(self.directory.resolve()) or path.suffix.lower() not in (".ogg",".mp3",".wav") or not path.is_file():
                    self.warning+="Skipped missing or unsupported track: "+name+". "
                    continue
                self.tracks.append(path)
        except (OSError,ValueError,KeyError,TypeError) as exc:
            self.status="Playlist could not be read: "+str(exc)
            return
        if self.preferences.values["shuffle"]:
            random.shuffle(self.tracks)
        self.index=-1
        self.status="Playlist is empty. Add your own music and reload."
        if self.tracks:
            self.next()

    def next(self):
        if not self.tracks:
            return
        if not self.preferences.values["music"]:
            self.status="Music is disabled. Your playlist is ready."
            return
        if not self.init():
            return
        for _ in range(len(self.tracks)):
            self.index=(self.index+1)%len(self.tracks)
            try:
                self.backend.music.load(str(self.tracks[self.index]))
                self.backend.music.set_volume(self.preferences.values["volume"]/100)
                self.backend.music.play()
                self.playing=True
                self.paused=False
                self.status="Playing: "+self.tracks[self.index].name
                return
            except Exception as exc:
                self.warning="Could not play "+self.tracks[self.index].name+": "+str(exc)
        self.playing=False
        self.status="No playable tracks. The game will continue silently."

    def apply(self):
        if not self.preferences.values["music"]:
            self.stop()
            self.status="Music is disabled."
        elif not self.playing:
            self.next()
        elif self.initialized:
            try:
                self.backend.music.set_volume(self.preferences.values["volume"]/100)
            except Exception as exc:
                self.status="Audio unavailable: "+str(exc)
                self.stop()

    def pause(self):
        if self.playing and self.initialized:
            try:
                (self.backend.music.unpause if self.paused else self.backend.music.pause)()
                self.paused=not self.paused
            except Exception as exc:
                self.status="Audio unavailable: "+str(exc)
                self.stop()

    def poll(self):
        if self.playing and not self.paused:
            try:
                if not self.backend.music.get_busy():
                    self.next()
            except Exception as exc:
                self.status="Audio unavailable: "+str(exc)
                self.stop()

    def close(self):
        self.stop()
        if self.initialized:
            try:
                self.backend.quit()
            except Exception:
                pass


class Artwork:
    """Deterministic procedural art, cached as Tk images at the current sizes."""
    def __init__(self):
        self.cache = {}

    def astral(self,width,height):
        key=("astral",width,height)
        if key not in self.cache:
            image=Image.new("RGB",(width,height))
            d=ImageDraw.Draw(image)
            for y in range(height):
                p=y/max(1,height-1)
                d.line((0,y,width,y),fill=(int(10+10*p),int(15+8*p),int(31+17*p)))
            mist=Image.new("RGBA",(width,height))
            m=ImageDraw.Draw(mist)
            m.ellipse((width*.15,height*.05,width*.9,height*.9),fill=(75,45,117,60))
            m.ellipse((-width*.2,height*.2,width*.45,height*1.2),fill=(29,96,109,45))
            image=Image.alpha_composite(image.convert("RGBA"),mist.filter(ImageFilter.GaussianBlur(max(15,width//9))))
            d=ImageDraw.Draw(image)
            rng=random.Random(881)
            for i in range(130):
                x,y=rng.randrange(width),rng.randrange(height)
                r=1 if i%9 else 2
                colour=rng.choice(("#566182","#9394bc","#dedcf0","#819cae"))
                d.ellipse((x-r,y-r,x+r,y+r),fill=colour)
                if i%29==0:
                    d.line((x-4,y,x+4,y),fill=colour)
                    d.line((x,y-4,x,y+4),fill=colour)
            self.cache[key]=ImageTk.PhotoImage(image)
        return self.cache[key]

    def parchment(self, width, height):
        key = ("paper", width, height)
        if key not in self.cache:
            rng = random.Random(49)
            w, h = max(1, width // 3), max(1, height // 3)
            image = Image.new("RGB", (w, h))
            pixels = []
            for y in range(h):
                for x in range(w):
                    edge = min(x, y, w - 1 - x, h - 1 - y)
                    shade = 12 * math.exp(-edge / 8) + rng.gauss(0, 1.8)
                    crease = 2 * math.sin(x / 25 + y / 130)
                    pixels.append(tuple(max(0, min(255, int(c - shade + crease))) for c in (239, 225, 196)))
            image.putdata(pixels)
            image = image.resize((width, height), Image.Resampling.BICUBIC)
            draw = ImageDraw.Draw(image)
            draw.rectangle((5, 5, width - 6, height - 6), outline="#c2a674")
            draw.rectangle((9, 9, width - 10, height - 10), outline="#dcc69f")
            self.cache[key] = ImageTk.PhotoImage(image)
        return self.cache[key]

    def moth(self,frame=0):
        key=("moth",frame)
        if key not in self.cache:
            scale=3
            image=Image.new("RGBA",(160*scale,120*scale))
            d=ImageDraw.Draw(image)
            d.ellipse((28*scale,18*scale,132*scale,108*scale),fill=(179,160,242,100))
            image=image.filter(ImageFilter.GaussianBlur(14*scale))
            d=ImageDraw.Draw(image)
            spread=.58+.42*(.5+.5*math.cos(frame*math.tau/12))
            def point(x,y,side):
                return ((80+side*x*spread)*scale,y*scale)
            for side in (-1,1):
                for inset,colour in ((0,(220,207,251,150)),(5,(249,242,226,235))):
                    upper=[point(x,y,side) for x,y in ((3,53),(27,20+inset),(66-inset,10+inset),(60-inset,49),(37,70),(5,71))]
                    lower=[point(x,y,side) for x,y in ((4,65),(39,59),(53-inset,88),(28,103-inset),(7,83))]
                    d.polygon(upper,fill=colour)
                    d.polygon(lower,fill=colour)
                d.line([point(x,y,side) for x,y in ((5,62),(27,45),(49,29),(37,62),(21,81))],fill=(167,143,212,230),width=2*scale)
                for x,y in ((27,45),(49,29),(37,62),(21,81)):
                    px,py=point(x,y,side)
                    d.ellipse((px-3*scale,py-3*scale,px+3*scale,py+3*scale),fill=(255,252,236,255),outline=(203,165,95,255),width=scale)
                d.line([point(2,53,side),point(8,36,side),point(15,31,side)],fill=(238,205,136,255),width=scale)
            d.ellipse((76*scale,47*scale,84*scale,86*scale),fill=(226,186,101,255),outline=(255,231,173,255),width=scale)
            d.ellipse((75*scale,45*scale,85*scale,55*scale),fill=(255,234,182,255))
            self.cache[key]=ImageTk.PhotoImage(image.resize((160,120),Image.Resampling.LANCZOS))
        return self.cache[key]

    def glow(self, colour, width, height):
        key = ("glow", colour, width, height)
        if key not in self.cache:
            image = Image.new("RGBA", (160, 160))
            rgb = tuple(int(colour[i:i+2],16) for i in (1,3,5))
            draw = ImageDraw.Draw(image)
            draw.ellipse((32,32,128,128), fill=rgb+(75,))
            image = image.filter(ImageFilter.GaussianBlur(22))
            image = image.resize((max(1,width),max(1,height)),Image.Resampling.LANCZOS)
            self.cache[key] = ImageTk.PhotoImage(image)
        return self.cache[key]

    def sky(self, width, height):
        key = ("sky", width, height)
        if key in self.cache:
            return self.cache[key]
        w, h = 1000, 1000
        im = Image.new("RGB", (w, h))
        d = ImageDraw.Draw(im)
        for y in range(h):
            t = y / h
            d.line((0, y, w, y), fill=(int(21 + t * 30), int(28 + t * 27), int(51 + t * 25)))
        rng = random.Random(37)
        for _ in range(170):
            x, y = rng.randrange(w), rng.randrange(610)
            r = rng.choice((.7, 1, 1, 1.5))
            d.ellipse((x-r, y-r, x+r, y+r), fill=rng.choice(("#918caa", "#d1c9b8", "#586781")))
        glow = Image.new("RGBA", im.size)
        gd = ImageDraw.Draw(glow)
        gd.ellipse((635, 15, 905, 285), fill=(205, 206, 189, 35))
        im = Image.alpha_composite(im.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(45)))
        d = ImageDraw.Draw(im)
        d.ellipse((726, 86, 812, 172), fill="#e8dfbb")
        d.ellipse((747, 76, 822, 151), fill="#252e47")
        for layer, colour in ((0, "#343950"), (1, "#2b3c4d"), (2, "#213b43")):
            points = [(0, 780)] + [(x, 455 + layer*75 + rng.randrange(-65, 60)) for x in range(0, 1101, 90)] + [(1000, 1000), (0, 1000)]
            d.polygon(points, fill=colour)
        # Broken cathedral arches and gold astronomical tracery.
        for cx in (180, 820):
            d.rectangle((cx-21, 280, cx+21, 720), fill="#454553", outline="#69626b", width=3)
            d.rectangle((cx-29, 696, cx+29, 729), fill="#68606a")
            d.rectangle((cx-29, 277, cx+29, 300), fill="#777078")
            d.line((cx-9, 310, cx-9, 685), fill="#827781", width=3)
        d.arc((180, 95, 820, 605), 180, 360, fill="#595562", width=38)
        d.arc((180, 95, 820, 605), 180, 360, fill="#8b7b78", width=3)
        d.arc((204, 122, 796, 603), 180, 360, fill="#bd9c68", width=2)
        d.ellipse((330, 235, 670, 575), outline="#82715d", width=2)
        d.ellipse((348, 253, 652, 557), outline="#564e57", width=2)
        for a in range(0, 360, 30):
            r = math.radians(a)
            x, y = 500+170*math.cos(r), 405+170*math.sin(r)
            d.ellipse((x-3, y-3, x+3, y+3), fill="#c3a16a")
        # Floating stone terrace, stepped edges, and inlaid geometry.
        d.polygon(((75, 704), (500, 549), (933, 707), (500, 939)), fill="#252d3d")
        d.polygon(((75, 677), (500, 536), (933, 680), (500, 904)), fill="#77716e", outline="#a99780", width=3)
        d.polygon(((95, 676), (500, 547), (910, 681), (500, 883)), fill="#555965", outline="#b19b7c", width=2)
        for f in (.23, .46, .69):
            d.line((95+(500-95)*f, 676+(547-676)*f, 500+(910-500)*f, 883+(681-883)*f), fill="#74717a", width=2)
            d.line((500+(910-500)*f, 547+(681-547)*f, 95+(500-95)*f, 676+(883-676)*f), fill="#74717a", width=2)
        for y in (792, 810, 828, 846):
            d.polygon(((420, y), (500, y+38), (584, y), (584, y+12), (500, y+50), (420, y+12)), fill="#807a79", outline="#a1917e")
        # Dense silhouette foliage frames the illustration.
        for side in (0, 1):
            for _ in range(34):
                x = rng.randrange(0, 140) if not side else rng.randrange(870, 1000)
                y = rng.randrange(590, 1020)
                d.line((x, y+55, x+8, y-45), fill="#354c4b", width=3)
                for j in range(5):
                    yy = y-j*13
                    d.ellipse((x-22, yy-12, x+6, yy+2), fill=rng.choice(("#354d4e", "#3e5854", "#52675c")))
                    d.ellipse((x+4, yy-18, x+29, yy-4), fill="#3e5854")
        im = im.resize((width, height), Image.Resampling.LANCZOS)
        self.cache[key] = ImageTk.PhotoImage(im)
        return self.cache[key]


class Tooltip:
    def __init__(self, root):
        self.root, self.window, self.timer = root, None, None
        self.current_text = None

    def hide(self, event=None):
        self.current_text = None
        if self.timer:
            self.root.after_cancel(self.timer)
            self.timer = None
        if self.window:
            self.window.destroy()
            self.window = None

    def show(self, text, event):
        if text == self.current_text:
            return
        self.hide()
        self.current_text = text
        x, y = event.x_root, event.y_root
        def open_tip():
            self.timer = None
            self.window = tk.Toplevel(self.root)
            self.window.overrideredirect(True)
            self.window.configure(bg=GOLD)
            tk.Label(self.window, text=text, bg=LIGHT, fg=INK, font=("Segoe UI", 10),
                     wraplength=280, justify="left", padx=12, pady=10).pack(padx=1, pady=1)
            self.window.update_idletasks()
            xx = min(x+12, self.root.winfo_screenwidth()-self.window.winfo_reqwidth()-12)
            yy = min(y+18, self.root.winfo_screenheight()-self.window.winfo_reqheight()-12)
            self.window.geometry(f"+{max(0,xx)}+{max(0,yy)}")
        self.timer = self.root.after(550, open_tip)


class AtelierApp(SpellGraph):
    def spell_tree(self):
        return SpellTree(self.economy)

    def __init__(self, root, store=None, start_loop=True, show_welcome=True, slots=None, apply_preferences=True):
        self.root = root
        # Match the sanctuary crystal, retaining crisp pixel edges at icon sizes.
        icon = Image.new("RGBA", (32, 32))
        ink = ImageDraw.Draw(icon)
        ink.polygon(((16,2),(24,19),(16,29),(8,19)), fill="#b1a1e0")
        ink.polygon(((16,2),(16,29),(8,19)), fill="#6e6ba4")
        ink.line(((16,2),(24,19),(16,29),(8,19),(16,2)), fill="#ebe0fa", width=1)
        self.window_icons = [ImageTk.PhotoImage(icon.resize((size,size), Image.Resampling.NEAREST), master=root) for size in (16,32,48,64)]
        root.iconphoto(True, *self.window_icons)
        root.title("Starstruck Atelier · An alchemist’s idle journal")
        root.geometry("1440x900")
        root.minsize(1100, 720)
        root.configure(bg="#3e3530")
        self.slots = slots or SlotManager()
        self.in_menu = store is None
        self.active_slot = None
        self.menu_notice = "Three journals. Three skies. Choose a sanctuary to tend."
        self.slot_summaries = []
        if self.in_menu:
            try:
                self.menu_notice = self.slots.migrate() or self.menu_notice
            except (OSError, ValueError) as exc:
                self.menu_notice = "Could not import the old sanctuary: " + str(exc)
            self.slot_summaries = self.slots.summaries()
        self.store = store or self.slots.store(1)
        state, recovery = self.store.load() if not self.in_menu else (State(), "")
        initial_motion=state.reduced_motion
        if self.in_menu:
            initial_motion=next((s.reduced_motion for s,_ in self.slot_summaries if s),False)
        settings_directory=self.store.path.parent if store else self.slots.directory
        self.preferences=Preferences(settings_directory/"settings.json",initial_motion)
        self.settings_open=False
        self.settings_status=self.preferences.notice
        self.music=MusicPlayer(Path(__file__).parent/"assets"/"music",self.preferences)
        self.use_window_preferences=apply_preferences
        if apply_preferences:
            root.geometry(f"{self.preferences.values['width']}x{self.preferences.values['height']}")
            root.attributes("-fullscreen",self.preferences.values["fullscreen"])
        self.economy = Economy(state)
        self.offline_time, self.offline_gains = self.economy.offline(time.time()) if not self.in_menu else (0, [0]*5)
        self.economy.discover()
        self.guide = Guide(self.economy)
        self.crafting = Crafting(self.economy)
        self.encounters=Encounters(self.economy)
        self.guide.update()
        self.charm_mode = "online"
        self.charm_long = False
        self.charm_tier=1
        self.charm_infused=False
        self.crafting_section="Home"
        self.transmute_quantity=1
        self.tome_window = None
        self.tome_all = False
        self.tome_chapter = "first"
        self.tome_body = None
        self.retain = set()
        self.legacy_selection=None
        self.art = Artwork()
        self.cursors=CursorSet(settings_directory)
        self.tree_window=None
        self.tree_view=[.65,20.,20.]
        self.tree_selected=("Charmcraft",0)
        self.frames={}
        self.feedback_until=0.
        self.feedback_text=""
        self.consume_release=False
        self.tooltip = Tooltip(root)
        self.tab = "Production"
        self.quantity = 1
        self.selected = None
        self.panel_signature = None
        self.modal = None
        self.timer = None
        self.last_time = time.monotonic()
        self.last_ui = 0.
        self.last_save = self.last_time
        self.save_status = "Your journal saves automatically"
        self.background = tk.Canvas(root, highlightthickness=0, bg=PAPER)
        self.background.pack(fill="both", expand=True, padx=10, pady=10)
        self.scene = tk.Canvas(self.background, highlightthickness=1, highlightbackground=GOLD, bg="#20283e")
        self.panel = tk.Canvas(self.background, highlightthickness=0, bg=PAPER)
        self.scroll = tk.Scrollbar(self.background, orient="vertical", command=self.panel.yview,
                                   bg=PAPER, troughcolor="#dac7a3", activebackground=GOLD, width=12)
        self.panel.configure(yscrollcommand=self.scroll.set)
        for canvas in (self.background, self.panel):
            canvas.hover_regions = []
            canvas.bind("<Motion>", lambda e, c=canvas: self.hover(c, e))
            canvas.bind("<Leave>", lambda e, c=canvas: (c.configure(cursor=""), self.tooltip.hide()))
        for i in range(5):
            self.scene.tag_bind(f"building-{i}", "<Button-1>", lambda e, idx=i: self.select_building(idx))
            self.scene.tag_bind(f"building-{i}", "<Enter>", lambda e,idx=i:self.cursor_on(self.scene,idx+1 if self.economy.state.owned[idx] else 0))
            self.scene.tag_bind(f"building-{i}", "<Leave>", lambda e:self.cursor_on(self.scene))
        self.scene.tag_bind("visitor","<Button-1>",lambda e:self.capture_spirit())
        self.scene.tag_bind("visitor","<Enter>",lambda e:self.scene.configure(cursor="hand2"))
        self.scene.tag_bind("visitor","<Leave>",lambda e:self.scene.configure(cursor=""))
        self.panel.bind("<MouseWheel>", lambda e: self.panel.yview_scroll(-int(e.delta / 120), "units"))
        self.panel.bind("<Button-4>", lambda e: self.panel.yview_scroll(-1, "units"))
        self.panel.bind("<Button-5>", lambda e: self.panel.yview_scroll(1, "units"))
        self.background.bind("<Configure>", self.resize)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", lambda e: self.escape())
        self.root.bind("<F11>",lambda e:self.toggle_fullscreen())
        self.width, self.height = 1420, 880
        self.scene_width, self.scene_height = 700, 530
        self.resize_timer = None
        self.anim_time = 0.
        root.bind_class("AtelierDismiss","<ButtonPress-1>",self.outside_press)
        root.bind_class("AtelierDismiss","<ButtonRelease-1>",self.outside_release)
        self.shield(root)
        self.root.update_idletasks()
        self.frames[root]=WindowFrame(self,root,"Starstruck Atelier",self.close,main=True)
        self.shield(root)
        self.layout()
        if start_loop:
            self.tick()
        if show_welcome and not self.in_menu:
            if self.store.blocked:
                self.dialog("A page we cannot read", recovery, "Begin a fresh journal", self.fresh_save, cancel="Close game", on_cancel=self.close)
            elif recovery:
                self.dialog("Your sanctuary is safe", recovery + "\n\n" + self.offline_summary(), "Return to the atelier")
            elif self.offline_time > 60:
                self.dialog("While the moon was watching…", self.offline_summary(), "Open the journal")

    def refresh_slots(self):
        self.slot_summaries = self.slots.summaries()
        self.draw_ui()

    def draw_slots(self):
        c, w, h = self.background, self.width, self.height
        self.text(c, w/2, 53, "STARSTRUCK ATELIER", 32, BURGUNDY, "Georgia", anchor="center")
        self.text(c, w/2, 98, "T H E   S A N C T U A R Y   A R C H I V E", 11, MUTED, anchor="center")
        self.button(c,w-132,30,100,30,"Settings",self.open_settings)
        self.text(c, w/2, 136, self.menu_notice, 11, TEAL, anchor="n", width=w-160)
        gap, left = 24, 52
        card_w = (w-2*left-2*gap)/3
        top, bottom = 210, h-105
        for i, (state, warning) in enumerate(self.slot_summaries):
            x = left+i*(card_w+gap)
            c.create_rectangle(x+5,top+7,x+card_w+5,bottom+7,fill="#c7ae83",outline="")
            c.create_rectangle(x,top,x+card_w,bottom,fill=LIGHT,outline=GOLD,width=2)
            self.text(c,x+card_w/2,top+27,f"VOLUME  {('I','II','III')[i]}",12,MUTED,"Georgia",anchor="center")
            self.text(c,x+card_w/2,top+77,"✧",36,BURGUNDY,"Georgia",anchor="center")
            self.text(c,x+card_w/2,top+126,state.sanctuary_name if state else "An unwritten sky",20,BURGUNDY,"Georgia",anchor="n",width=card_w-30)
            if state:
                info = (f"{len(state.discoveries)}/10 restoration seals\n{state.awakenings} Reawakenings · {state.seals} Moon Seals\nLast tended\n"+
                        time.strftime("%d %b %Y · %H:%M",time.localtime(min(state.saved_at, 253402214400))))
                if warning:
                    info = "This journal needs recovery.\nIts files remain protected.\n\nContinue for recovery options."
                self.text(c,x+card_w/2,top+192,info,11,MUTED,anchor="n",justify="center",width=card_w-32)
                self.button(c,x+20,bottom-102,card_w-40,34,"Continue",lambda slot=i+1:self.open_slot(slot),primary=True)
                self.button(c,x+20,bottom-55,(card_w-50)/2,28,"Rename",lambda slot=i+1:self.name_slot(slot,False))
                self.button(c,x+30+(card_w-50)/2,bottom-55,(card_w-50)/2,28,"Delete",lambda slot=i+1:self.delete_slot(slot))
            else:
                self.text(c,x+card_w/2,top+199,"A quiet ruin waits for its keeper.\nA separate journey, entirely yours.",11,MUTED,anchor="n",justify="center",width=card_w-32)
                self.button(c,x+20,bottom-65,card_w-40,36,"New sanctuary",lambda slot=i+1:self.name_slot(slot,True),primary=True)
        self.text(c,w/2,h-49,"Every sanctuary keeps its own progress. The others continue while you are away.",11,MUTED,anchor="center")

    def name_slot(self, slot, new):
        current = self.slot_summaries[slot-1][0]
        self.dialog("Name your sanctuary" if new else "Rename this sanctuary",
                    "Choose a name of up to 32 characters for this journal.","Create sanctuary" if new else "Save name",cancel="Cancel")
        entry = tk.Entry(self.modal,font=("Georgia",17),bg=LIGHT,fg=BURGUNDY,relief="solid",bd=1)
        entry.place(x=30,y=188,width=488,height=42)
        entry.insert(0,f"Sanctuary {slot}" if new else current.sanctuary_name)
        entry.select_range(0,"end")
        entry.focus_set()
        def apply_name():
            name=entry.get().strip()
            try:
                if new:
                    self.slots.create(slot,name)
                else:
                    self.slots.rename(slot,name)
            except (OSError,ValueError) as exc:
                error.configure(text=str(exc))
                return
            self.dismiss(force=True)
            self.refresh_slots()
            if new:
                self.open_slot(slot)
        error=tk.Label(self.modal,text="",bg=PAPER,fg=BURGUNDY,font=("Segoe UI",10),wraplength=485)
        error.place(x=30,y=245,width=488,height=50)
        # Replace the generic dialog's accept action while preserving validation.
        self.modal_accept = apply_name
        entry.bind("<Return>",lambda e:apply_name())
        self.shield(self.modal)

    def delete_slot(self, slot):
        state=self.slot_summaries[slot-1][0]
        def remove():
            try:
                self.slots.delete(slot)
                self.menu_notice=f"Slot {slot} is ready for a new sanctuary."
            except OSError as exc:
                self.menu_notice="Could not delete this sanctuary: "+str(exc)
            self.refresh_slots()
        self.dialog("Close this journal forever?",f'Delete “{state.sanctuary_name}”?\n\nThis removes its progress and backup. The other two sanctuaries and original Moonveil files are untouched.',"Delete sanctuary",remove,cancel="Keep sanctuary")

    def open_slot(self, slot):
        try:
            store,game,elapsed,gains,warning=self.slots.open(slot)
        except (OSError,ValueError) as exc:
            broken=self.slots.store(slot)
            broken.load()
            if broken.blocked:
                def recover():
                    try:
                        broken.preserve_invalid()
                        broken.save(State(sanctuary_name=f"Sanctuary {slot}"))
                        self.refresh_slots()
                        self.open_slot(slot)
                    except OSError as err:
                        self.dialog("Files remain protected",str(err),"Return to the archive")
                self.dialog("A page we cannot read",str(exc),"Archive files & start fresh",recover,cancel="Return to archive")
            else:
                self.dialog("Could not open the sanctuary",str(exc),"Return to the archive")
            return
        self.store,self.economy,self.active_slot=store,game,slot
        self.guide,self.crafting=Guide(game),Crafting(game)
        self.encounters=Encounters(game)
        self.guide.update()
        self.offline_time,self.offline_gains=elapsed,gains
        self.in_menu=False
        self.tab,self.quantity,self.selected="Production",1,None
        self.tome_chapter,self.tome_all="first",False
        self.charm_mode,self.charm_long="online",False
        self.charm_tier=1
        self.charm_infused=False
        self.crafting_section="Home"
        self.last_time=self.last_save=time.monotonic()
        self.save_status=f"Slot {slot} · {game.state.sanctuary_name}"
        self.layout()
        if warning or elapsed > 60:
            self.dialog("While the stars were watching…",(warning+"\n\n" if warning else "")+self.offline_summary(),"Open the journal",self.tutorial_invitation)
        else:
            self.tutorial_invitation()

    def tutorial_invitation(self):
        if self.economy.state.tutorial_invite:
            def accept():
                self.guide.restart()
                self.save()
                self.draw_ui()
            def skip():
                self.economy.state.tutorial_invite=False
                self.save()
            self.dialog("A familiar sky, a new journal", "Your sanctuary is safe. Would you like a short tour of Starstruck Atelier’s controls? The Spell Tome is always available.","Take the guided tour",accept,cancel="Explore on my own",on_cancel=skip)

    @property
    def reduced_motion(self):
        return self.preferences.values["reduced_motion"]

    def save_preferences(self):
        try:
            self.preferences.save()
            self.settings_status="Preferences saved. Sanctuary progress is unchanged."
        except OSError as exc:
            self.settings_status="Could not save preferences: "+str(exc)

    def toggle_fullscreen(self):
        current=bool(self.root.attributes("-fullscreen"))
        if not current:
            self.preferences.values["width"]=self.root.winfo_width()
            self.preferences.values["height"]=self.root.winfo_height()
        self.root.attributes("-fullscreen",not current)
        self.preferences.values["fullscreen"]=not current
        if current:
            self.root.geometry(f"{self.preferences.values['width']}x{self.preferences.values['height']}")
        self.frames[self.root].update_visibility()
        self.frames[self.root].centre()
        self.save_preferences()
        self.layout()
        return "break"

    def escape(self):
        if self.modal:
            self.dismiss(force=True)
        elif self.tree_window:
            self.close_tree()
        elif self.tome_window:
            self.close_tome()
        elif self.settings_open:
            self.close_settings()
        elif self.root.attributes("-fullscreen"):
            self.toggle_fullscreen()
        return "break"

    def open_settings(self):
        self.tooltip.hide()
        self.close_tome()
        self.close_tree()
        self.settings_open=True
        self.panel.yview_moveto(0)
        self.layout()

    def close_settings(self):
        self.settings_open=False
        self.panel.yview_moveto(0)
        self.layout()

    def set_preference(self,key,value):
        self.preferences.values[key]=value
        if key=="shuffle":
            self.music.reload()
        elif key in ("music","volume"):
            self.music.apply()
        self.save_preferences()
        self.draw_ui()

    def reset_preferences(self):
        def reset():
            self.preferences.values=dict(Preferences.DEFAULTS)
            self.root.attributes("-fullscreen",True)
            self.frames[self.root].update_visibility()
            self.music.reload()
            self.save_preferences()
            self.layout()
        self.dialog("Restore default preferences?","Fullscreen, effects and music preferences will return to their defaults. Your three sanctuaries and all their progress remain intact.","Reset preferences",reset,cancel="Keep preferences")

    def settings_page(self):
        c,w=self.panel,self.panel_width
        p=self.preferences.values
        self.text(c,24,20,"DISPLAY",16,BURGUNDY,"Georgia")
        self.text(c,24,58,"F11 toggles fullscreen. Escape closes the foremost page, then exits fullscreen.",11,MUTED,width=w-48)
        self.button(c,24,99,210,34,"Exit fullscreen" if self.root.attributes("-fullscreen") else "Enter fullscreen",self.toggle_fullscreen)
        self.text(c,260,110,f"Remembered window: {p['width']} × {p['height']}",11,MUTED)
        self.text(c,24,159,"Frame rate",11,INK)
        for j,fps in enumerate((30,60)):
            self.button(c,180+j*120,150,105,32,f"{fps} FPS",lambda v=fps:self.set_preference("fps",v),primary=p["fps"]==fps)
        self.text(c,24,217,"EFFECTS",16,BURGUNDY,"Georgia")
        self.button(c,24,258,240,33,"Reduced motion: "+("On" if p["reduced_motion"] else "Off"),lambda:self.set_preference("reduced_motion",not p["reduced_motion"]))
        self.button(c,285,258,240,33,"Celestial visitors: "+("On" if p["spirits"] else "Off"),lambda:self.set_preference("spirits",not p["spirits"]))
        self.text(c,24,321,"Effect density",11,INK)
        for j,density in enumerate(("Low","Standard","High")):
            self.button(c,180+j*120,312,105,32,density,lambda v=density:self.set_preference("density",v),primary=p["density"]==density)
        self.text(c,24,389,"AUDIO",16,BURGUNDY,"Georgia")
        self.button(c,24,430,150,32,"Music: "+("On" if p["music"] else "Off"),lambda:self.set_preference("music",not p["music"]))
        self.button(c,190,430,110,32,"Resume" if self.music.paused else "Pause",self.music.pause,enabled=self.music.playing)
        self.button(c,316,430,110,32,"Next track",self.music.next,enabled=bool(self.music.tracks))
        self.button(c,442,430,160,32,"Reload playlist",self.music.reload)
        self.text(c,24,485,f"Volume: {p['volume']}%",12,INK)
        self.button(c,180,477,78,30,"− 5",lambda:self.set_preference("volume",max(0,p["volume"]-5)))
        self.button(c,270,477,78,30,"+ 5",lambda:self.set_preference("volume",min(100,p["volume"]+5)))
        self.button(c,370,477,232,30,"Playlist: "+("Shuffle" if p["shuffle"] else "In order"),lambda:self.set_preference("shuffle",not p["shuffle"]))
        self.text(c,24,537,self.music.status,11,TEAL,width=w-48)
        self.text(c,24,577,self.music.warning,10,BURGUNDY,width=w-48)
        self.text(c,24,650,"YOUR MUSIC · A LITTLE PRACTICE",16,BURGUNDY,"Georgia")
        instructions='1. Copy .ogg, .mp3 or .wav files into Proj3-codex/assets/music/.\n2. Edit playlist.json with exact filenames in double quotes:\n\n    {"tracks": ["night-garden.ogg", "starlight.mp3"]}\n\n3. Use Reload playlist above. Turn music on and set the volume.\n\nSeparate filenames with commas; no comma after the last item.\nTry adding a second song and reversing their order. Nothing is uploaded.'
        self.text(c,24,692,instructions,12,INK,width=w-48)
        self.text(c,24,938,"HELP & PREFERENCES",16,BURGUNDY,"Georgia")
        def tour():
            self.close_settings()
            self.restart_tutorial()
        self.button(c,24,980,250,34,"Replay guided first steps",tour,enabled=not self.in_menu)
        self.button(c,294,980,250,34,"Reset preferences",self.reset_preferences)
        self.text(c,24,1045,self.settings_status,11,MUTED,width=w-48)
        self.text(c,24,1090,"CELESTIAL POINTER",16,BURGUNDY,"Georgia")
        self.button(c,24,1130,250,32,"Cursor: "+("Celestial" if p["celestial_cursor"] else "System"),lambda:self.set_preference("celestial_cursor",not p["celestial_cursor"]))
        self.button(c,294,1130,250,32,"Station motifs: "+("On" if p["station_cursors"] else "Off"),lambda:self.set_preference("station_cursors",not p["station_cursors"]))
        self.text(c,24,1180,"Drag blank space in the spell tree; scroll to zoom. Click behind a popup to close it. Escape never confirms an action.",11,MUTED,width=w-48)

    def capture_spirit(self):
        if self.encounters.capture():
            self.save()
            # Finish the scene click before opening: otherwise that same click
            # reaches the outside-click handler and dismisses the new window.
            self.root.after_idle(self.show_spirit_offer)

    def show_spirit_offer(self):
        if not self.economy.state.spirit_offer:
            return
        def dismiss_offer():
            self.encounters.dismiss()
            self.save()
        self.dialog("Celestial visitor","Choose one blessing. It adds to your other bonuses for two online minutes, uses no charm hook, and pauses while you are away.","Decide later",cancel="Let the visitor go",on_cancel=dismiss_offer)
        c=self.modal_canvas
        for i,offer in enumerate(self.economy.state.spirit_offer):
            def choose(index=i):
                if self.encounters.choose(index):
                    self.save()
                    self.dismiss(force=True)
                    self.draw_ui()
            self.button(c,28,225+i*57,490,43,f"+{offer['percent']}% {RESOURCES[offer['target']]} · 2 minutes",choose,primary=True)

    def return_to_slots(self):
        self.sync_time()
        if not self.save():
            self.dialog("The journal could not be saved",self.save_status+"\n\nYour current sanctuary remains open.","Retry switching",self.return_to_slots,cancel="Keep playing")
            return False
        self.close_tome()
        self.tooltip.hide()
        self.in_menu=True
        self.active_slot=None
        self.menu_notice="Three journals. Three skies. Choose a sanctuary to tend."
        self.slot_summaries=self.slots.summaries()
        self.layout()
        return True

    def fresh_save(self):
        try:
            self.store.preserve_invalid()
            self.save()
        except OSError as exc:
            self.dialog("The journal is still protected", str(exc), "Close game", self.close)

    def offline_summary(self):
        lines = [f"Your sanctuary worked for {duration(self.offline_time)}.", ""]
        lines += [f"{name}: {'+' if value >= 0 else ''}{number(value)}" for name, value in zip(RESOURCES, self.offline_gains)]
        lines += ["", "Ingredient changes include materials used by your converters. Offline production has no time cap."]
        return "\n".join(lines)

    def resize(self, event):
        if event.widget is not self.background:
            return
        if self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        self.resize_timer = self.root.after(100, self.layout)

    def layout(self):
        self.resize_timer = None
        self.width = max(1080, self.background.winfo_width())
        self.height = max(640, self.background.winfo_height())
        self.left = int(self.width * .545)
        self.scene_width = self.left - 44
        self.scene_height = self.height - 330
        self.scene.place(x=24, y=191, width=self.scene_width, height=self.scene_height)
        self.panel_x = self.left + 16
        self.panel_width = self.width - self.panel_x - 36
        self.panel.place(x=self.panel_x, y=231, width=self.panel_width, height=self.height - 273)
        self.scroll.place(x=self.width-29, y=231, width=12, height=self.height-273)
        if self.settings_open:
            self.panel_width=self.width-130
            self.panel.place(x=56,y=128,width=self.panel_width,height=self.height-166)
            self.scroll.place(x=self.width-66,y=128,width=12,height=self.height-166)
            self.scene.place_forget()
        self.art.cache.clear()
        self.cursor_on(self.background)
        self.cursor_on(self.scene)
        self.cursor_on(self.panel)
        self.panel_signature = None
        if self.in_menu and not self.settings_open:
            self.scene.place_forget()
            self.panel.place_forget()
            self.scroll.place_forget()
        self.draw_ui()
        if not self.in_menu and not self.settings_open:
            self.draw_scene()

    def text(self, canvas, x, y, text, size=11, fill=INK, family="Segoe UI", anchor="nw", **kw):
        return canvas.create_text(x, y, text=text, fill=fill, font=(family, size), anchor=anchor, **kw)

    def button(self, canvas, x, y, w, h, label, callback, enabled=True, primary=False, tip=None):
        if not hasattr(canvas,"controls"):
            canvas.controls=CanvasButtons(self,canvas)
            self.shield(canvas)
        if not enabled and not tip:
            tip="Unavailable: check the ingredients and prerequisites shown on this page."
        shadow=canvas.create_rectangle(x+2,y+3,x+w+2,y+h+3,fill="#c8b48e",outline="")
        face=canvas.create_rectangle(x,y,x+w,y+h,fill=LIGHT,outline=GOLD)
        text=self.text(canvas,x+w/2,y+h/2,label,10,LIGHT if primary and enabled else INK,anchor="center")
        canvas.controls.add((x,y,x+w,y+h),label,callback,enabled,primary,tip,(shadow,face,text))

    def clear_page(self, canvas):
        for tag,binding in getattr(canvas,"button_bindings",[]):
            canvas.tag_unbind(tag,"<Button-1>",binding)
        canvas.button_bindings=[]
        if hasattr(canvas,"controls"):canvas.controls.clear()
        canvas.hover_regions=[]
        canvas.delete("all")

    def hover(self,canvas,event):
        if hasattr(canvas,"controls"):canvas.controls.motion(event)
        else:self.cursor_on(canvas)

    def cursor_on(self,widget,kind=0):
        p=self.preferences.values
        self.cursors.apply(widget,p["celestial_cursor"],kind if p["station_cursors"] else 0)

    def shield(self,widget):
        tags=widget.bindtags()
        if "AtelierDismiss" not in tags:widget.bindtags(("AtelierDismiss",)+tags)
        for child in widget.winfo_children():self.shield(child)

    def outside_press(self,event):
        front=self.modal or self.tree_window or self.tome_window
        if not front:return
        x,y=event.x_root,event.y_root
        def within(win):
            return win.winfo_rootx()<=x<win.winfo_rootx()+win.winfo_width() and win.winfo_rooty()<=y<win.winfo_rooty()+win.winfo_height()
        if not within(front) and (within(self.root) or (self.tree_window and within(self.tree_window)) or (self.tome_window and within(self.tome_window))):
            if self.modal:self.dismiss(force=True)
            elif self.tree_window:self.close_tree()
            else:self.close_tome()
            self.consume_release=True
            return "break"

    def outside_release(self,event):
        if self.consume_release:
            self.consume_release=False
            return "break"

    def frame_window(self,window,title,close):
        if window not in self.frames:
            self.frames[window]=WindowFrame(self,window,title,close)
        self.frames[window].title=title
        self.frames[window].draw()
        self.frames[window].bar.tk.call("raise",self.frames[window].bar._w)
        self.shield(window)
        window.update()
        width=min(window.winfo_width(),self.root.winfo_screenwidth()-20)
        height=min(window.winfo_height(),self.root.winfo_screenheight()-40)
        x=max(0,(self.root.winfo_screenwidth()-width)//2)
        y=max(0,(self.root.winfo_screenheight()-height)//2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def destroy_window(self,window):
        self.dispose_controls(window)
        frame=self.frames.pop(window,None)
        if frame:frame.dispose()
        window.destroy()

    def dispose_controls(self,widget):
        if hasattr(widget,"controls"):widget.controls.dispose()
        for child in widget.winfo_children():self.dispose_controls(child)

    def feedback(self,text):
        self.feedback_text=text
        self.feedback_until=time.monotonic()+(1.2 if self.reduced_motion else 1.8)

    def set_tab(self, tab):
        self.tooltip.hide()
        self.tab = tab
        self.panel.yview_moveto(0)
        self.panel_signature = None
        self.draw_ui()

    def set_quantity(self, value):
        self.quantity = value
        self.draw_ui()

    def action(self, method, index):
        if self.store.blocked:
            return
        self.sync_time()
        changed = self.economy.buy(index, self.quantity) if method == "buy" else self.economy.study(index)
        if changed:
            self.feedback("Inscription added" if method=="study" else "Purchase complete")
            self.guide.update()
            self.save()
            self.draw_ui()

    def toggle_motion(self):
        self.set_preference("reduced_motion",not self.reduced_motion)

    def draw_ui(self):
        c, w, h = self.background, self.width, self.height
        self.clear_page(c)
        c.create_image(0, 0, image=self.art.parchment(w, h), anchor="nw")
        if self.settings_open:
            self.text(c,56,29,"SETTINGS · YOUR ATELIER",25,BURGUNDY,"Georgia")
            self.text(c,57,76,"Display, atmosphere, music, and a little help.",11,MUTED)
            self.button(c,w-193,36,135,34,"Back",self.close_settings)
            self.draw_panel()
            return
        if self.in_menu:
            self.draw_slots()
            return
        self.text(c, 26, 19, "STARSTRUCK ATELIER", 25, BURGUNDY, "Georgia")
        self.text(c, 29, 61, f"AN ALCHEMIST’S JOURNAL  /  {self.economy.state.sanctuary_name}", 10, MUTED)
        unread=len(set(self.economy.state.chapters_unlocked)-set(self.economy.state.chapters_read))
        self.button(c,w-420,26,139,31,f"Spell Tome · {unread}" if unread else "Spell Tome",self.open_tome,primary=unread>0)
        self.button(c,w-270,26,119,31,"Sanctuaries",self.return_to_slots)
        self.button(c,w-140,26,109,31,"Settings",self.open_settings)
        flows, net = self.economy.flows()
        card_w = (w - 50) / 5
        for i, name in enumerate(RESOURCES):
            x = 25 + i*card_w
            c.create_rectangle(x, 91, x+card_w-8, 157, fill=LIGHT, outline="#c6ac7e")
            c.create_line(x+1, 92, x+card_w-9, 92, fill=GOLD, width=2)
            self.text(c, x+13, 98, name.upper(), 9, MUTED)
            self.text(c, x+13, 116, number(self.economy.state.resources[i]), 19, BURGUNDY, "Georgia")
            self.text(c, x+card_w-20, 136, f"{'+' if net[i] >= 0 else ''}{number(net[i])}/s", 10, TEAL if net[i] >= 0 else BURGUNDY, anchor="se")
            self.button(c,x+card_w-60,96,40,19,"Uses",lambda target=i:self.resource_guide(target),tip=RESOURCE_ROLES[i])
        self.text(c, 25, 169, "I.   THE SANCTUARY", 11, BURGUNDY, "Georgia")
        self.text(c, self.left-21, 172, f"{len(self.economy.state.discoveries)}/10 restoration seals", 9, MUTED, anchor="ne")
        if self.economy.state.spirit_offer:
            self.button(c,190,164,177,23,"Celestial visitor",self.show_spirit_offer,primary=True)
        if time.monotonic()<self.feedback_until:
            self.text(c,self.width/2,70,self.feedback_text,11,TEAL,anchor="center")
        c.create_line(self.left+3, 176, self.left+3, h-43, fill="#bd9f70")
        c.create_line(self.left+6, 176, self.left+6, h-43, fill="#f9edd4")
        self.text(c, self.panel_x, 169, "II.   THE WORKING JOURNAL", 11, BURGUNDY, "Georgia")
        tab_w = (self.panel_width-18)/4
        for i, tab in enumerate(("Production", "Research", "Workshop", "Reawakening")):
            self.button(c, self.panel_x+i*(tab_w+6), 195, tab_w, 28, tab, lambda t=tab: self.set_tab(t), primary=tab == self.tab)
        log_y = 191 + self.scene_height + 15
        self.text(c, 26, log_y, "FIELD NOTES", 9, BURGUNDY)
        if not self.economy.state.tutorial_skipped and self.economy.state.tutorial_step < 5 and not self.economy.state.tutorial_invite:
            self.draw_tutorial(log_y)
        else:
            entries = self.economy.state.journal[-2:]
            for i, entry in enumerate(reversed(entries)):
                self.text(c, 28, log_y+23+i*33, "✧  " + entry, 10, MUTED, width=self.scene_width-12)
        c.create_line(25, h-34, w-25, h-34, fill="#bfa474")
        self.text(c, 27, h-23, self.save_status, 9, MUTED, anchor="w")
        state = self.economy.state
        self.text(c, w-27, h-23, f"{state.seals} Moon Seals   ·   {self.economy.multiplier:.1f}× production   ·   {duration(state.played)} tended", 9, MUTED, anchor="e")
        self.draw_panel()

    def draw_panel(self):
        c, w = self.panel, self.panel_width
        position = c.yview()[0]
        self.clear_page(c)
        if self.settings_open:
            total=1260
        elif self.tab == "Workshop":
            total = {"Home":1100,"Charms":1880,"Talismans":1380,"Restoration":1380,"Transmutation":1110,"Enchantments":1050,"Infusion & Recharge":1350,"Deliveries":1100}[self.crafting_section]
        elif self.tab == "Reawakening":
            total = max(self.height-273, 1200)
        else:
            total = 62+5*190
        c.create_image(0, 0, image=self.art.parchment(w, total), anchor="nw")
        if self.settings_open:
            self.settings_page()
        elif self.tab == "Production":
            self.text(c, 16, 17, "THE ART OF PATIENCE", 10, MUTED)
            for j, q in enumerate((1, 10, "max")):
                self.button(c, w-205+j*62, 12, 56, 27, str(q).upper() if q == "max" else f"×{q}", lambda v=q: self.set_quantity(v), primary=self.quantity == q)
            for i in range(5):
                self.production_card(i, 54+i*190)
        elif self.tab == "Research":
            self.text(c, 17, 17, "MARGINALIA & DISCOVERIES", 10, MUTED)
            for i in range(5):
                self.research_card(i, 54+i*190)
        elif self.tab == "Workshop":
            self.crafting_page()
        else:
            self.prestige_page()
        c.configure(scrollregion=(0, 0, w, total))
        c.yview_moveto(position)

    def card_base(self, i, y):
        c, w = self.panel, self.panel_width
        c.create_rectangle(12, y+3, w-12, y+181, fill="#cdb992", outline="")
        c.create_rectangle(10, y, w-15, y+178, fill="#f3e7ce", outline=BURGUNDY if self.selected == i else "#c8ad80", width=2 if self.selected == i else 1)
        c.create_oval(23, y+15, 56, y+48, fill="#e4d3af", outline=GOLD)
        self.text(c, 40, y+31, ("☽", "◇", "⚗", "♨", "✧")[i], 18, BURGUNDY, "Georgia", anchor="center")
        self.text(c, 66, y+13, BUILDINGS[i].name, 16, BURGUNDY, "Georgia")
        self.text(c, 66, y+40, BUILDINGS[i].subtitle, 9, MUTED)

    def production_card(self, i, y):
        c, w, b, state = self.panel, self.panel_width, BUILDINGS[i], self.economy.state
        self.card_base(i, y)
        if not self.economy.unlocked(i):
            self.text(c, 25, y+74, "A page yet to be written", 12, BURGUNDY, "Georgia")
            self.text(c, 25, y+100, f"Earn {number(b.unlock)} total Mana this run to uncover it.", 10, MUTED)
            progress = min(1, state.run_mana/b.unlock)
            c.create_rectangle(25, y+136, w-32, y+141, fill="#d9c8a6", outline="")
            c.create_rectangle(25, y+136, 25+(w-57)*progress, y+141, fill=GOLD, outline="")
            self.text(c, w-33, y+154, f"{number(state.run_mana)} / {number(b.unlock)} Mana", 9, MUTED, anchor="e")
            return
        flows, net = self.economy.flows()
        cap = self.economy.capacities()[i] + (self.economy.multiplier*self.economy.bonus(0) if i == 0 else 0)
        self.text(c, w-29, y+24, f"{state.owned[i]} owned", 10, MUTED, anchor="e")
        recipe = ("The apprentice spark + wells → Mana" if i == 0 else "Moonlight → Shards" if i == 1 else f"{b.ratio:g} {RESOURCES[i-1]} → 1 {RESOURCES[i]}")
        self.text(c, 25, y+66, recipe, 10, INK)
        self.text(c, 25, y+90, f"{number(flows[i])} / {number(cap)} {RESOURCES[i]}/s", 11, TEAL)
        if i >= 2:
            status = f"Uses {number(flows[i]*b.ratio)} {RESOURCES[i-1]}/s"
            if flows[i] < cap-1e-8:
                status += f"  ·  Needs more {RESOURCES[i-1]}"
        else:
            status = "Always flowing · no ingredients required"
        self.text(c, 25, y+112, status, 9, MUTED)
        if i >= 2 and flows[i] < cap-1e-8:
            self.button(c,w-153,y+64,124,22,"Read in the tome",lambda:self.open_tome(("distillery","crucible","astral")[i-2]))
        quantity = self.economy.affordable(i) if self.quantity == "max" else self.quantity
        cost = self.economy.cost(i, max(1, quantity))
        enabled = quantity > 0 and cost <= state.resources[0]+1e-8
        extra = b.rate*2**state.research[i]*self.economy.multiplier*self.economy.bonus(i)
        self.text(c, 25, y+148, f"+{number(extra)} capacity / building", 9, MUTED)
        self.button(c, w-210, y+135, 181, 30, f"Buy {quantity or 1} · {number(cost)} Mana", lambda: self.action("buy", i), enabled=enabled,
                    tip=f"Adds {number(extra)} {RESOURCES[i]}/s maximum production per building. Converters need a matching ingredient supply.")
        s=self.economy.state
        if not s.tutorial_skipped and ((s.tutorial_step == 0 and i == 0) or (s.tutorial_step == 2 and i == 1)):
            c.create_rectangle(w-214,y+131,w-25,y+169,outline="#c28b29",width=3)

    def research_card(self, i, y):
        c, w, b, state = self.panel, self.panel_width, BUILDINGS[i], self.economy.state
        self.card_base(i, y)
        tier = state.research[i]
        names = ("Attunement", "Resonance", "Transcendence")
        self.text(c,25,y+68,STAGES[tier]+f" · {tier}/3 inscriptions",11,TEAL)
        self.text(c,25,y+94,"Masterwork complete · 8× base capacity" if tier==3 else "Next: "+STAGES[tier+1]+" · 2× capacity",10,INK)
        self.text(c,25,y+117,("Restore worn materials","Awaken moving magic","Finish with gilded effects","Your finest workmanship")[tier],9,MUTED)
        if tier < 3:
            price = b.research[tier]
            self.button(c, w-242, y+141, 213, 27, f"Inscribe · {number(price)} {RESOURCES[i]}", lambda: self.action("study", i), enabled=state.owned[i] > 0 and state.resources[i] >= price,
                        tip="Research uses this building’s output. The first inscription also earns a permanent restoration seal.")
        else:
            self.text(c, w-30, y+153, "✧  MASTERWORK", 10, BURGUNDY, anchor="e")

    def draw_tutorial(self, y):
        c,s=self.background,self.economy.state
        messages=("Buy a Spirit Well in the Production journal. Your first well costs 30 Mana.",
                  "Watch the Mana strip grow. The apprentice spark and your well work automatically.",
                  "Plant a Crystal Garden for 60 Mana. Wait a moment if you need more Mana.",
                  "Select the Crystal Garden in the illustration to find its production card.",
                  "Open the Spell Tome above. New chapters appear as your sanctuary grows.")
        c.create_rectangle(23,y-3,self.left-18,y+86,fill=LIGHT,outline=GOLD)
        self.text(c,32,y+5,f"GUIDED FIRST STEPS  ·  {s.tutorial_step+1}/5",9,BURGUNDY)
        self.text(c,32,y+28,messages[s.tutorial_step],10,INK,width=self.scene_width-119)
        self.button(c,self.left-104,y+42,76,26,"Skip tour",self.skip_tutorial)
        if s.tutorial_step == 1:
            c.create_rectangle(22,88,25+(self.width-50)/5-5,160,outline="#c28b29",width=3)
        elif s.tutorial_step == 4:
            c.create_rectangle(self.width-424,22,self.width-277,61,outline="#c28b29",width=3)

    def skip_tutorial(self):
        self.economy.state.tutorial_skipped=True
        self.save()
        self.draw_ui()

    def restart_tutorial(self):
        self.guide.restart()
        self.close_tome()
        self.set_tab("Production")
        self.save()

    def close_tome(self):
        if self.tome_window:
            self.destroy_window(self.tome_window)
            self.tome_window=None
            self.tome_body=None

    def open_tome(self, chapter=None):
        self.close_tree()
        if self.in_menu:
            return
        self.economy.state.tome_opened=True
        self.guide.update()
        if chapter:
            self.tome_chapter=chapter
            if chapter not in self.economy.state.chapters_unlocked:
                self.tome_all=True
        self.guide.read(self.tome_chapter)
        self.save()
        if not self.tome_window:
            win=tk.Toplevel(self.root)
            self.tome_window=win
            win.title("The Spell Tome · Starstruck Atelier")
            win.transient(self.root)
            win.resizable(False,False)
            win.configure(bg="#44302b")
            self.tome_canvas=tk.Canvas(win,width=960,height=600,bg="#44302b",highlightthickness=0)
            self.tome_canvas.pack()
            self.tome_contents=tk.Canvas(win,bg=LIGHT,highlightthickness=0)
            self.tome_contents.place(x=49,y=157,width=226,height=350)
            contents_scroll=tk.Scrollbar(win,command=self.tome_contents.yview)
            contents_scroll.place(x=277,y=157,width=14,height=350)
            self.tome_contents.configure(yscrollcommand=contents_scroll.set)
            self.tome_contents.bind("<MouseWheel>",lambda e:self.tome_contents.yview_scroll(-int(e.delta/120),"units"))
            self.tome_body=tk.Text(win,bg=LIGHT,fg=INK,font=("Segoe UI",12),wrap="word",relief="flat",
                                   padx=12,pady=10,spacing3=12,highlightthickness=0,cursor="xterm")
            self.tome_body.place(x=350,y=154,width=545,height=273)
            scrollbar=tk.Scrollbar(win,command=self.tome_body.yview)
            scrollbar.place(x=897,y=154,width=12,height=273)
            self.tome_body.configure(yscrollcommand=scrollbar.set)
            win.protocol("WM_DELETE_WINDOW",self.close_tome)
            win.bind("<Escape>",lambda e:self.close_tome())
            win.bind("<F11>",lambda e:self.toggle_fullscreen())
            x=max(0,self.root.winfo_rootx()+(self.root.winfo_width()-960)//2)
            y=max(0,self.root.winfo_rooty()+(self.root.winfo_height()-600)//2)
            win.geometry(f"960x600+{x}+{y}")
        self.draw_tome()
        self.frame_window(self.tome_window,"The Spell Tome",self.close_tome)
        self.tome_window.lift()
        self.draw_ui()

    def choose_chapter(self, chapter):
        self.tome_chapter=chapter
        self.guide.read(chapter)
        self.save()
        self.draw_tome()
        self.draw_ui()

    def toggle_tome_all(self):
        self.tome_all=not self.tome_all
        if not self.tome_all and self.tome_chapter not in self.economy.state.chapters_unlocked:
            self.tome_chapter="first"
            self.guide.read("first")
        self.draw_tome()

    def draw_tome(self):
        if not self.tome_window:
            return
        c,s=self.tome_canvas,self.economy.state
        reading_position=self.tome_body.yview()[0] if getattr(self,"tome_rendered_chapter",None)==self.tome_chapter else 0
        self.clear_page(c)
        c.paper_image=self.art.parchment(904,550)
        c.create_rectangle(12,12,948,588,fill="#56382e",outline=GOLD,width=2)
        c.create_rectangle(25,24,936,579,fill="#bca37a",outline="#c7b28d")
        c.create_image(28,22,image=c.paper_image,anchor="nw")
        for dx,colour in ((301,"#b59a73"),(304,"#c8b18a"),(309,"#dcc69f"),(314,"#f4e5c6")):
            c.create_line(dx,25,dx,569,fill=colour,width=4)
        self.text(c,52,48,"THE SPELL TOME",19,BURGUNDY,"Georgia")
        self.text(c,52,82,"A keeper’s marginalia",10,MUTED)
        self.button(c,49,113,226,28,"View relevant chapters" if self.tome_all else "View all chapters",self.toggle_tome_all)
        visible=[ch for ch in CHAPTERS if self.tome_all or ch[0] in s.chapters_unlocked]
        contents=self.tome_contents
        position=contents.yview()[0]
        self.clear_page(contents)
        for i,(key,title,_) in enumerate(visible):
            unread=key in s.chapters_unlocked and key not in s.chapters_read
            prefix="● " if unread else "◇ " if key not in s.chapters_unlocked else ""
            self.button(contents,2,3+i*34,219,28,prefix+title,lambda k=key:self.choose_chapter(k),primary=key==self.tome_chapter)
            if unread:
                contents.create_oval(5,13+i*34,10,18+i*34,fill="#be8c2e",outline="")
        contents.configure(scrollregion=(0,0,226,len(visible)*34+7))
        contents.yview_moveto(position)
        key,title,body=next(ch for ch in CHAPTERS if ch[0]==self.tome_chapter)
        self.text(c,355,51,"CHAPTER "+str(next(i+1 for i,ch in enumerate(CHAPTERS) if ch[0]==key)),10,MUTED)
        self.text(c,355,80,title,25,BURGUNDY,"Georgia",width=550)
        self.text(c,355,125,"A preview of a future art" if key not in s.chapters_unlocked else "✧  Notes from your sanctuary",10,TEAL)
        self.tome_body.configure(state="normal")
        self.tome_body.delete("1.0","end")
        self.tome_body.insert("1.0",body)
        self.tome_body.configure(state="disabled")
        self.tome_body.yview_moveto(reading_position)
        self.tome_rendered_chapter=self.tome_chapter
        diagram={"first":("Spark","Spirit Well","Garden"),
                 "research":("Materials","Inscription","2× capacity"),
                 "distillery":("3 Shards","Distillation","1 Essence"),
                 "crucible":("4 Essence","Crucible","1 Elixir"),
                 "astral":("5 Elixirs","Astral Circle","1 Stardust"),
                 "charms":("Stored","Equipped","Expired"),
                 "talismans":("Trace","Bind","+20%"),
                 "reawakening":("Stardust","Keep up to 3","New chapter"),
                 "offline":("Leave a slot","Time passes","Return & collect")}.get(key,RESOURCES)
        for j,label in enumerate(diagram):
            x=389+j*476/(len(diagram)-1)
            if j:
                c.create_line(previous_x+11,451,x-14,451,fill=GOLD,arrow="last")
            c.create_oval(x-9,442,x+9,460,outline=BURGUNDY,width=2)
            self.text(c,x,451,"✧",10,BURGUNDY,"Georgia",anchor="center")
            self.text(c,x,478,label,9,MUTED,anchor="center")
            previous_x=x
        index=next(i for i,ch in enumerate(visible) if ch[0]==key)
        self.button(c,354,500,120,30,"Previous",lambda:self.choose_chapter(visible[index-1][0]),enabled=index>0)
        self.button(c,780,500,120,30,"Next page",lambda:self.choose_chapter(visible[index+1][0]),enabled=index<len(visible)-1)
        self.text(c,625,516,f"{index+1} / {len(visible)}",11,MUTED,anchor="center")
        self.button(c,49,528,226,29,"Restart guided first steps",self.restart_tutorial)
        self.tome_signature=(tuple(s.chapters_unlocked),tuple(s.chapters_read))

    def set_recipe(self, mode=None, long=None, tier=None):
        if mode is not None:
            self.charm_mode=mode
        if long is not None:
            self.charm_long=long
        if tier is not None:
            self.charm_tier=tier
        self.draw_ui()

    def crafting_action(self, action, target):
        self.sync_time()
        if action=="craft":
            changed=self.crafting.craft(target,self.charm_long,self.charm_mode,self.charm_tier,self.charm_infused)
        elif action=="equip":
            changed=self.crafting.equip(target)
        elif action=="restore":
            changed=self.crafting.restore(target)
        elif action=="transmute":
            changed=self.crafting.transmute(target,self.transmute_quantity)
        else:
            changed=self.crafting.dismantle(target)
        if changed:
            self.feedback("Charm updated" if action in ("equip","dismantle") else "Workshop purchase complete")
            self.save()
        self.draw_ui()

    def confirm_dismantle(self, target):
        self.dialog("Let this charm fade?",f"Dismantle your {RESOURCES[target]} charm?\n\nIts remaining duration and materials will be lost. You can then craft another of this type.","Dismantle charm",lambda:self.crafting_action("dismantle",target),cancel="Keep charm")

    def toggle_infusion(self):
        self.charm_infused=not self.charm_infused
        self.draw_ui()

    def resource_guide(self,target):
        self.tab="Workshop"
        self.set_crafting_section("Home")
        s=self.economy.state
        available=(any(s.research),any(s.research),s.owned[2]>0,s.owned[3]>0,True)[target]
        section=("Charms","Restoration","Enchantments","Infusion & Recharge","Home")[target]
        def explore():
            if target==4:
                self.set_tab("Reawakening")
            else:
                self.set_crafting_section(section if available else "Home")
        self.dialog(RESOURCES[target],RESOURCE_ROLES[target]+"\n\n"+("Visit Construction and Charms in the workshop." if target==1 else "Visit Enchantments for the spell tree." if target==2 else "Visit Infusion & Recharge to sustain charms." if target==3 else "The workshop introduces activities as your sanctuary grows."),"View Reawakening" if target==4 else "Open related activity",explore)

    def workshop_home(self):
        c,w,s=self.panel,self.panel_width,self.economy.state
        self.text(c,24,22,"THE CELESTIAL WORKSHOP",19,BURGUNDY,"Georgia")
        self.text(c,24,63,"Build with Shards. Enchant with Essence. Sustain with Elixirs.",11,TEAL,width=w-48)
        activities=(
            ("Charms",any(s.research),"First research inscription","Build a body, choose a target and hang it on the rack."),
            ("Restoration",any(s.research),"First research inscription","Construction: turn Shards into lasting sanctuary improvements."),
            ("Enchantments",s.owned[2]>0,"Own a Distillery","Spend Essence in three branches of the spell tree."),
            ("Transmutation",s.owned[2]>0,"Own a Distillery","Recover earlier materials with lossy reverse conversion."),
            ("Infusion & Recharge",s.owned[3]>0,"Own a Crucible","Elixirs extend new charms and refill equipped magic."),
            ("Deliveries",Deliveries(self.economy).unlocked(),"Crucible's second inscription","Meet the courier: trade surplus materials for Mana."),
            ("Talismans",any(self.crafting.talisman_unlocked(i) for i in range(5)),"A station's first inscription","Trace constellations and choose what survives rebirth."),
        )
        for i,(name,available,gate,body) in enumerate(activities):
            y=115+i*130
            c.create_rectangle(14,y,w-14,y+114,fill=LIGHT if available else PAPER,outline=GOLD)
            self.text(c,28,y+12,"Construction" if name=="Restoration" else name,17,BURGUNDY,"Georgia")
            self.text(c,28,y+45,body if available else "Unlock: "+gate,10,MUTED,width=w-56)
            if available:
                self.button(c,w-164,y+77,135,25,"Open activity",lambda value=name:self.open_tree() if value=="Enchantments" else self.set_crafting_section(value))

    def workshop_change(self,callback):
        self.sync_time()
        if callback():
            self.feedback("Workshop purchase complete")
            self.guide.update()
            self.save()
        self.draw_ui()

    def workshop_activity(self):
        c,w,s=self.panel,self.panel_width,self.economy.state
        section=self.crafting_section
        chapter={"Enchantments":"enchantments","Infusion & Recharge":"recharge","Deliveries":"deliveries"}[section]
        self.text(c,24,64,section.upper(),18,BURGUNDY,"Georgia")
        self.button(c,w-161,17,137,28,"Read in the tome",lambda:self.open_tome(chapter))
        if section=="Enchantments":
            self.text(c,24,115,"Three connected branches. Spend Essence and the materials each art specialises in. Existing inscriptions remain yours.",12,INK,width=w-48)
            self.button(c,24,230,w-48,40,"Open branching spell tree",self.open_tree,primary=True)
            self.text(c,24,295,"Drag to explore, scroll to zoom, and select a node to compare its next rank before purchasing.",11,MUTED,width=w-48)
            return
        if section=="Infusion & Recharge":
            self.text(c,24,111,f"Infusion adds {75 if s.spell_advanced['Charmcraft'][0] else 50}% duration at creation. Enable it on the Charms page. Recharging replaces remaining time with the original maximum.",11,MUTED,width=w-48)
            self.button(c,24,180,w-48,30,"Craft an infused charm",lambda:self.set_crafting_section("Charms"))
            for i in range(5):
                y=240+i*205
                ch=self.crafting.charm(i)
                c.create_rectangle(14,y,w-14,y+187,fill=LIGHT,outline=GOLD)
                self.text(c,28,y+12,RESOURCES[i],17,BURGUNDY,"Georgia")
                if not ch:
                    self.text(c,28,y+56,"No charm held. Craft one in the charm workshop.",10,MUTED,width=w-56)
                    continue
                price=self.crafting.recharge_price(ch)
                gained=ch["max_duration"]-ch["remaining"]
                self.text(c,28,y+46,f"{duration(ch['remaining'])} / {duration(ch['max_duration'])} · refill gains {duration(gained)}",10,TEAL,width=w-56)
                self.text(c,28,y+80,f"Cost {number(price)} Elixirs · have {number(s.resources[3])}",11,INK)
                self.text(c,28,y+109,f"Next refill: {number(self.crafting.recharge_price(ch,1))} Elixirs",10,MUTED)
                self.button(c,28,y+142,w-56,29,"Refill to crafted maximum" if ch["equipped"] else "Equip this charm before refilling",lambda target=i:self.workshop_change(lambda:self.crafting.recharge(target)),enabled=bool(s.owned[3] and ch["equipped"] and gained>1e-8 and s.resources[3]>=price))
            return
        courier=Deliveries(self.economy)
        self.text(c,24,110,"A courier waits beneath a sky of folded letters.",12,TEAL,"Georgia",width=w-48)
        c.create_polygon(w/2-33,156,w/2+33,156,w/2+33,195,w/2-33,195,fill="#d9c8a4",outline=GOLD,width=2)
        c.create_line(w/2-33,156,w/2,178,w/2+33,156,fill=BURGUNDY,width=2)
        self.text(c,24,217,"Offers stay fixed. Completing or declining starts a cooldown; improving upstream production can make the next contract easier.",11,MUTED,width=w-48)
        if not s.contracts:
            if s.delivery_cooldown:
                message="The courier returns in "+duration(s.delivery_cooldown)+". This clock also runs while away."
            else:
                _,net=courier.baseline()
                blocked=[RESOURCES[i] for i in (1,2,3) if net[i]<=1e-8]
                message="A contract needs two materials with sustainable surplus. No surplus: "+", ".join(blocked)+". Add upstream capacity or research; downstream stations currently consume the supply."
            self.text(c,24,300,message,12,BURGUNDY,width=w-48)
            return
        _,net=courier.baseline()
        for index,offer in enumerate(s.contracts):
            y=300+index*340
            c.create_rectangle(14,y,w-14,y+320,fill=LIGHT,outline=GOLD)
            self.text(c,28,y+15,f"Courier contract {index+1}",18,BURGUNDY,"Georgia")
            self.recipe_lines(c,28,y+58,offer["cost"])
            self.text(c,28,y+116,"Receive: "+recipe_text(offer["reward"]),11,TEAL,width=w-56)
            waits=[max(0,n-s.resources[i])/net[i] if net[i]>1e-8 else (0 if s.resources[i]>=n else math.inf) for i,n in enumerate(offer["cost"]) if n]
            eta=max(waits)
            self.text(c,28,y+175,"Gathering estimate: "+(duration(eta) if math.isfinite(eta) else "increase upstream production"),10,MUTED,width=w-56)
            self.text(c,28,y+211,"Uses baseline surplus, excluding temporary boosts.",10,MUTED,width=w-56)
            self.button(c,28,y+266,w-56,30,"Fulfil this contract",lambda j=index:self.workshop_change(lambda:courier.finish(j)),enabled=can_pay(s,offer["cost"]),primary=True)
        self.button(c,24,315+len(s.contracts)*340,w-48,30,"Decline · begin courier cooldown",lambda:self.workshop_change(lambda:courier.finish()))

    def set_spell_branch(self,branch):
        self.spell_branch=branch
        self.draw_ui()

    def crafting_page(self):
        c,w,s=self.panel,self.panel_width,self.economy.state
        if self.crafting_section=="Home":
            self.workshop_home()
            return
        self.button(c,22,16,155,29,"Back to workshop",lambda:self.set_crafting_section("Home"))
        if self.crafting_section in ("Enchantments","Infusion & Recharge","Deliveries"):
            self.workshop_activity()
            return
        if self.crafting_section!="Charms":
            self.crafting_other_page()
            return
        self.text(c,22,65,"THE CHARM RACK",17,BURGUNDY,"Georgia")
        self.button(c,w-156,62,133,27,"Read in the tome",lambda:self.open_tome("charms"))
        c.create_rectangle(32,112,w-32,125,fill="#85654a",outline="#b39669")
        equipped=[ch for ch in s.charms if ch["equipped"]]
        for j in range(3):
            x=48+j*(w-96)/3+(w-96)/6
            c.create_line(x,120,x,140,fill=GOLD,width=3)
            c.create_oval(x-29,140,x+29,198,fill="#e6d4ac",outline=GOLD,width=2)
            if j<len(equipped):
                charm=equipped[j]
                self.text(c,x,170,("☽","◇","✧","♨","☆")[charm["target"]],26,BURGUNDY,"Georgia",anchor="center")
                self.text(c,x,214,RESOURCES[charm["target"]],10,INK,anchor="center")
                self.text(c,x,234,duration(charm["remaining"]),9,TEAL,anchor="center")
                self.text(c,x,251,{"online":"Online","offline":"Awaits offline","both":"Online + offline"}[charm["mode"]],8,MUTED,anchor="center")
            else:
                self.text(c,x,170,"·",27,MUTED,"Georgia",anchor="center")
                self.text(c,x,217,"Empty hook",9,MUTED,anchor="center")
        self.text(c,23,274,"POTENCY · TIERS I–IV",9,MUTED)
        tier_w=(w-64)/4
        for j in range(4):
            self.button(c,23+j*(tier_w+6),296,tier_w,28,("I","II","III","IV")[j],lambda value=j+1:self.set_recipe(tier=value),enabled=self.crafting.tier_unlocked(j+1),primary=self.charm_tier==j+1,
                        tip=("First research inscription","Own a Distillery","Own a Crucible","Own an Astral Circle")[j])
        bw=(w-58)/3
        for j,mode in enumerate(("online","offline","both")):
            enabled=mode=="online" or bool(s.owned[2 if mode=="offline" else 3])
            self.button(c,23+j*(bw+6),338,bw,29,{"online":"Online","offline":"Offline","both":"Combined"}[mode],lambda m=mode:self.set_recipe(mode=m),enabled=enabled,primary=self.charm_mode==mode)
        self.button(c,23,381,(w-52)/2,31,f"Intense +{25*self.charm_tier}% · 15m",lambda:self.set_recipe(long=False),primary=not self.charm_long)
        self.button(c,29+(w-52)/2,381,(w-52)/2,31,f"Gentle +{10*self.charm_tier}% · 60m",lambda:self.set_recipe(long=True),primary=self.charm_long)
        self.button(c,23,425,w-46,27,"Elixir infusion: "+(f"ON (+{75 if s.spell_advanced['Charmcraft'][0] else 50}% duration)" if self.charm_infused else "OFF"),self.toggle_infusion,enabled=bool(s.owned[3]),tip="Elixirs sustain the charm: 10/25/60/150 by tier. Costs are shown below.")
        for i,name in enumerate(RESOURCES):
            y=460+i*270
            c.create_rectangle(12,y,w-14,y+254,fill=LIGHT,outline="#c8ad80")
            self.text(c,26,y+14,name+" charm",17,BURGUNDY,"Georgia")
            charm=self.crafting.charm(i)
            if charm:
                status="Stored · clock has not started"
                if charm["equipped"]:
                    status="Awaiting offline time" if charm["mode"]=="offline" else "Active in this sanctuary"
                self.text(c,26,y+48,f"+{charm['bonus']*100:g}% · {charm['mode'].title()} · {duration(charm['remaining'])}",11,TEAL)
                self.text(c,26,y+78,status,10,MUTED)
                self.text(c,26,y+109,"Legacy charm · original potency preserved" if charm["tier"]==0 else f"Tier {charm['tier']} · ingredients paid · equipping is free",10,MUTED,width=w-52)
                self.button(c,26,y+210,125,29,"Equipped" if charm["equipped"] else "Equip",lambda target=i:self.crafting_action("equip",target),enabled=not charm["equipped"] and len(equipped)<3,primary=True)
                self.button(c,w-155,y+210,125,29,"Dismantle",lambda target=i:self.confirm_dismantle(target))
            else:
                price=self.crafting.price(i,self.charm_long,self.charm_mode,self.charm_tier,self.charm_infused)
                bonus,maximum=self.crafting.crafted_stats(self.charm_long,self.charm_tier,self.charm_infused)
                self.text(c,26,y+47,f"+{bonus*100:g}% · {duration(maximum)} · {self.charm_mode.title()}",11,TEAL)
                for row,(label,vector) in enumerate((("Construction",price[:2]),("Enchantment",(price[2],)),("Infusion",(price[3],)))):
                    text=(f"{number(price[0])} Mana + {number(price[1])} Shards" if row==0 else number(vector[0])+ (" Essence" if row==1 else " Elixirs"))
                    self.text(c,26,y+78+row*22,label+": "+text,10,MUTED)
                missing=[f"{number(max(0,n-s.resources[j]))} {RESOURCES[j]}" for j,n in enumerate(price) if n>s.resources[j]+1e-8]
                self.text(c,26,y+150,"Missing: "+", ".join(missing) if missing else "All ingredients ready",10,BURGUNDY if missing else TEAL,width=w-52)
                self.text(c,26,y+181,"Have: "+recipe_text(tuple(s.resources[j] if n else 0 for j,n in enumerate(price))),9,MUTED,width=w-52)
                self.button(c,w-210,y+213,181,27,"Craft for inventory",lambda target=i:self.crafting_action("craft",target),enabled=self.crafting.can_craft(i,self.charm_long,self.charm_mode,self.charm_tier,self.charm_infused),primary=True)

    def set_crafting_section(self,section):
        self.crafting_section=section
        self.panel.yview_moveto(0)
        self.draw_ui()

    def recipe_lines(self,canvas,x,y,recipe):
        row=0
        for i,need in enumerate(recipe):
            if need:
                have=self.economy.state.resources[i]
                missing=max(0,need-have)
                self.text(canvas,x,y+row*22,f"{RESOURCES[i]}: {number(have)} / {number(need)}"+(f" · need {number(missing)} more" if missing>1e-8 else "  ✓"),10,BURGUNDY if missing>1e-8 else TEAL)
                row+=1

    def crafting_other_page(self):
        c,w,s=self.panel,self.panel_width,self.economy.state
        section=self.crafting_section
        self.text(c,24,67,section.upper(),17,BURGUNDY,"Georgia")
        chapter={"Talismans":"talismans","Restoration":"restoration","Transmutation":"transmutation"}[section]
        self.button(c,w-157,62,133,28,"Read in the tome",lambda:self.open_tome(chapter))
        if section=="Transmutation":
            self.text(c,24,107,"Unweave advanced materials. Conversion is one-way and lossy.",10,MUTED,width=w-48)
            for j,q in enumerate((1,10,"max")):
                self.button(c,24+j*109,149,98,28,str(q).upper(),lambda v=q:self.set_transmute_quantity(v),primary=self.transmute_quantity==q)
            for j,source in enumerate((4,3,2)):
                y=208+j*278
                cost,output,count=self.crafting.transmutation(source,self.transmute_quantity)
                c.create_rectangle(12,y,w-14,y+262,fill=LIGHT,outline=GOLD)
                self.text(c,26,y+15,RESOURCES[source]+" → "+RESOURCES[source-1],17,BURGUNDY,"Georgia")
                self.text(c,26,y+53,"Cost: "+recipe_text(cost) if count else "Own the source station and gather ingredients.",11,MUTED,width=w-52)
                self.text(c,26,y+104,"Receive: "+recipe_text(output) if count else "No affordable batch selected.",11,TEAL,width=w-52)
                if count:
                    self.recipe_lines(c,26,y+146,cost)
                self.button(c,w-216,y+217,187,29,f"Transmute {count} batches",lambda target=source:self.crafting_action("transmute",target),enabled=count>0 and can_pay(s,cost),primary=True)
            return
        restoration=section=="Restoration"
        if restoration:
            self.text(c,24,108,"Five levels per project: 5 / 10 / 15 / 20 / 25%. Shard costs ×6 per level; Mana fees ×2. Resets at Reawakening.",10,MUTED,width=w-48)
            for i,name in enumerate(RESTORATION_NAMES):
                y=170+i*240
                level=self.economy.construction_level(i)
                maximum=level>=CONSTRUCTION_MAX_LEVEL
                recipe=self.crafting.restoration_price(i)
                c.create_rectangle(12,y,w-14,y+225,fill=LIGHT,outline=GOLD,width=2 if maximum else 1)
                self.text(c,26,y+12,name,17,BURGUNDY,"Georgia")
                self.text(c,26,y+45,f"Level {level}/5 · +{self.economy.construction_bonus(i)*100:g}% {RESOURCES[i]}",11,TEAL)
                if maximum:
                    self.text(c,26,y+96,"Masterwork complete. Its light fills the sanctuary.",11,TEAL,width=w-52)
                else:
                    self.text(c,26,y+73,f"Next: level {level+1} · +{self.economy.construction_bonus(i,level+1)*100:g}% production",10,BURGUNDY)
                    self.recipe_lines(c,26,y+103,recipe)
                    self.button(c,26,y+181,w-52,29,"Build level I" if not level else f"Upgrade to level {level+1}",lambda target=i:self.crafting_action("restore",target),enabled=bool(any(s.research) and s.owned[i] and can_pay(s,recipe)),primary=True)
            return
        self.text(c,24,108,f"Construction: +{5+s.spell_ranks['Sanctuary'][1]}% for this run. Lost at Reawakening." if restoration else "All owned talismans grant +20%. Retain up to three at rebirth.",10,MUTED,width=w-48)
        for i,name in enumerate(RESTORATION_NAMES if restoration else TALISMAN_NAMES):
            y=158+i*240
            owned=i in (s.restorations if restoration else s.talismans)
            recipe=self.crafting.restoration_price(i) if restoration else TALISMAN_COSTS[i]
            c.create_rectangle(12,y,w-14,y+225,fill="#e6d7b7" if owned else LIGHT,outline=GOLD)
            self.text(c,26,y+13,name,17,BURGUNDY,"Georgia")
            self.text(c,26,y+44,f"+{5+s.spell_ranks['Sanctuary'][1] if restoration else 20}% {RESOURCES[i]}"+(" · ACTIVE" if owned else ""),11,TEAL)
            if owned:
                self.text(c,26,y+87,"A little more wonder in your sanctuary.",11,MUTED)
            else:
                self.recipe_lines(c,26,y+72,recipe)
                enabled=bool(s.owned[i]) and can_pay(s,recipe) if restoration else self.crafting.can_talisman(i)
                self.button(c,w-216,y+187,187,27,"Restore this project" if restoration else "Trace constellation",lambda target=i:self.crafting_action("restore",target) if restoration else self.open_puzzle(target),enabled=enabled,primary=True)

    def set_transmute_quantity(self,quantity):
        self.transmute_quantity=quantity
        self.draw_ui()

    def open_puzzle(self, target):
        self.sync_time()
        if not self.crafting.can_talisman(target):
            return
        self.puzzle=Constellation(target)
        self.puzzle_message="Start at star 1 in the reference, then follow its numbered path."
        self.puzzle_hint=None
        self.dialog("", "", "", cancel="Cancel")
        self.modal.title("Trace a constellation · "+TALISMAN_NAMES[target])
        self.modal.geometry("780x610")
        self.modal_canvas.configure(width=780,height=610)
        self.frame_window(self.modal,"Trace a constellation",lambda:self.dismiss(force=True))
        self.draw_puzzle()

    def draw_puzzle(self):
        c=self.modal_canvas
        self.clear_page(c)
        c.paper_image=self.art.parchment(780,610)
        c.create_image(0,0,image=c.paper_image,anchor="nw")
        self.text(c,28,39,TALISMAN_NAMES[self.puzzle.target],25,BURGUNDY,"Georgia")
        self.text(c,28,68,f"Trace to bind +20% {RESOURCES[self.puzzle.target]} production. Materials are paid only on completion.",11,MUTED,width=720)
        for cx,title in ((208,"THE REFERENCE"),(568,"YOUR TRACE")):
            c.create_rectangle(cx-167,115,cx+167,421,fill="#242e47",outline=GOLD,width=2)
            self.text(c,cx,137,title,10,"#e3d1a8",anchor="center")
        self.puzzle_star_positions=[]
        for side,cx in enumerate((208,568)):
            coords=[(cx+x*123,278+y*116) for x,y in self.puzzle.points]
            path=self.puzzle.order if side==0 else self.puzzle.path
            for a,b in zip(path,path[1:]):
                c.create_line(*coords[a],*coords[b],fill="#b5dcd1" if side else "#cbb582",width=2)
            for i,(x,y) in enumerate(coords):
                highlighted=side==1 and (i in self.puzzle.path or i==self.puzzle_hint)
                tag=f"star-{i}" if side else "reference-star"
                c.create_oval(x-12,y-12,x+12,y+12,fill="#deb775" if highlighted else "#869cae",outline="#f8e6bd",tags=tag)
                label=str(self.puzzle.order.index(i)+1) if side==0 else chr(65+i)
                self.text(c,x,y,label,9,"#17253a",anchor="center",tags=tag)
                if side:
                    self.puzzle_star_positions.append((x,y))
                    binding=c.tag_bind(tag,"<Button-1>",lambda e,index=i:self.trace_star(index))
                    if not hasattr(c,"button_bindings"):
                        c.button_bindings=[]
                    c.button_bindings.append((tag,binding))
        self.text(c,28,444,self.puzzle_message,12,TEAL,width=720)
        self.button(c,28,518,90,31,"Undo",self.puzzle_undo)
        self.button(c,130,518,90,31,"Reset",self.puzzle_reset)
        self.button(c,232,518,90,31,"Hint",self.puzzle_show_hint)
        self.button(c,335,518,120,31,"Bind talisman",self.finish_puzzle,enabled=self.puzzle.complete,primary=True)
        self.button(c,621,518,128,31,"Cancel",self.dismiss)
        self.text(c,28,572,"No timer. No cost for mistakes. Each star belongs to the same position in both diagrams.",10,MUTED)

    def trace_star(self, index):
        accepted=self.puzzle.select(index)
        self.puzzle_hint=None
        self.puzzle_message=("The constellation is complete. Bind it to your collection." if self.puzzle.complete else f"{len(self.puzzle.path)}/{self.puzzle.count} stars traced. Follow the next connection.") if accepted else "That star comes later. Compare the reference, or ask for a hint."
        self.draw_puzzle()

    def puzzle_undo(self):
        self.puzzle.undo()
        self.puzzle_hint=None
        self.puzzle_message="The last star was lifted. Continue when you are ready."
        self.draw_puzzle()

    def puzzle_reset(self):
        self.puzzle.path=[]
        self.puzzle_hint=None
        self.puzzle_message="A fresh trace. Start at the first star in the reference."
        self.draw_puzzle()

    def puzzle_show_hint(self):
        self.puzzle_hint=self.puzzle.hint()
        self.puzzle_message="The next star glows gold." if self.puzzle_hint is not None else "The constellation is complete."
        self.draw_puzzle()

    def finish_puzzle(self):
        self.sync_time()
        if self.crafting.finish_talisman(self.puzzle):
            self.dismiss(force=True)
            self.save()
            self.draw_ui()
        else:
            self.puzzle_message="The trace is unfinished, the talisman is already owned, or its materials have been consumed. No payment was taken."
            self.draw_puzzle()

    def prestige_page(self):
        c, w, state = self.panel, self.panel_width, self.economy.state
        cx = w/2
        c.create_oval(cx-50, 26, cx+50, 126, outline=GOLD, width=2)
        c.create_oval(cx-43, 33, cx+43, 119, outline=GOLD)
        self.text(c, cx, 76, "☽", 45, BURGUNDY, "Georgia", anchor="center")
        self.text(c, cx, 151, "Nothing beautiful is truly lost.", 20, BURGUNDY, "Georgia", anchor="center", width=w-40)
        self.text(c, 29, 198, "When the circle fills with stardust, fold this chapter closed and begin again. The sanctuary will remember your work.", 12, INK, width=w-58)
        progress = min(1., state.run_dust / state.rebirth_goal)
        self.text(c, 29, 274, f"Run-earned Stardust: {number(state.run_dust)} / {number(state.rebirth_goal)}", 11, TEAL)
        c.create_rectangle(29, 305, w-29, 313, fill="#d6c19b", outline="")
        c.create_rectangle(29, 305, 29+(w-58)*progress, 313, fill=BURGUNDY, outline="")
        self.text(c, 29, 332, f"Production stages established: {sum(n > 0 for n in state.owned)}/5", 11, INK)
        reward = self.economy.reward()
        self.text(c, 29, 365, f"{state.seals} Moon Seals held · +{state.seals*10}% production", 12, BURGUNDY)
        self.text(c,29,401,"Resets: materials, stations, research, charms, construction, spells, deliveries and blessings. Keep up to 3 talismans, seals and records.",11,MUTED,width=w-58)
        self.button(c, 29, 466, w-58, 43, f"Reawaken · receive {reward} Moon Seals" if reward else "The circle is still gathering light", self.confirm_prestige, enabled=reward > 0, primary=True)
        self.text(c,29,534,f"Next run's goal: {number(rebirth_target(state.awakenings+1))} Stardust. Each reset adds one permanent legacy choice. Base seal reward increases every three Reawakenings; waiting longer still earns more.",10,MUTED,width=w-58)
        self.text(c,29,625,"YOUR PERMANENT LEGACY",17,BURGUNDY,"Georgia")
        for i,(name,unlock,targets,bonus,description) in enumerate(LEGACIES):
            y=674+i*62
            self.text(c,29,y,f"{name} · {state.legacies[i]} chosen",12,BURGUNDY)
            self.text(c,29,y+23,description+f" per choice · unlocks at Reawakening {unlock}",10,MUTED,width=w-58)
        if state.legacy_pending:
            self.button(c,29,1080,w-58,36,f"Choose {state.legacy_pending} unclaimed legacy bonus(es)",lambda:self.show_legacy_choice(False),primary=True)

    def confirm_prestige(self):
        self.retain=set(self.economy.state.talismans[:3])
        self.legacy_selection=None
        self.dialog("", "", "", cancel="Keep tending")
        self.modal.title("The talismans we carry")
        self.modal.geometry("700x620")
        self.modal_canvas.configure(width=700,height=620)
        self.frame_window(self.modal,"The talismans we carry",lambda:self.dismiss(force=True))
        self.draw_retention()

    def toggle_retain(self, target):
        if target in self.retain:
            self.retain.remove(target)
        elif len(self.retain)<3:
            self.retain.add(target)
        self.frame_window(self.modal,"The talismans we carry",lambda:self.dismiss(force=True))
        self.draw_retention()

    def draw_retention(self):
        c,s=self.modal_canvas,self.economy.state
        self.clear_page(c)
        c.paper_image=self.art.parchment(700,620)
        c.create_image(0,0,image=c.paper_image,anchor="nw")
        self.text(c,28,39,"The talismans we carry",22,BURGUNDY,"Georgia")
        self.text(c,28,72,f"Receive {self.economy.reward()} Moon Seals. Choose up to three talismans to keep.",12,INK,width=640)
        for i,name in enumerate(TALISMAN_NAMES):
            y=121+i*57
            owned=i in s.talismans
            selected=i in self.retain
            c.create_rectangle(27,y,671,y+48,fill=LIGHT,outline=GOLD)
            self.text(c,43,y+15,name+f" · +20% {RESOURCES[i]}",12,BURGUNDY)
            self.button(c,477,y+9,175,29,"KEEP" if selected else "Will be lost" if owned else "Not owned",lambda target=i:self.toggle_retain(target),enabled=owned and (selected or len(self.retain)<3),primary=selected)
        lost=[TALISMAN_NAMES[i] for i in s.talismans if i not in self.retain]
        self.text(c,28,424,"Will be lost: "+(", ".join(lost) if lost else "no talismans"),11,BURGUNDY,width=640)
        self.text(c,28,469,"Materials, stations, research, charms, construction, spell ranks, deliveries and blessings reset. Selected talismans, seals, tome and records remain.",11,MUTED,width=640)
        def accept():
            self.show_legacy_choice(True)
        self.button(c,28,549,324,36,f"Reawaken · keep {len(self.retain)}/3 talismans",accept,primary=True)
        self.button(c,470,549,201,36,"Keep tending",self.dismiss)

    def perform_prestige(self):
        self.sync_time()
        if self.economy.reawaken(sorted(self.retain),self.legacy_selection):
            self.save()
            self.set_tab("Production")

    def show_legacy_choice(self,reset=True):
        self.legacy_reset=reset
        self.legacy_selection=None
        self.dialog("","","",cancel="Keep tending")
        self.modal.geometry("760x680")
        self.modal_canvas.configure(width=760,height=680)
        self.frame_window(self.modal,"A memory carried through the stars",lambda:self.dismiss(force=True))
        self.draw_legacy_choice()

    def select_legacy(self,index):
        self.legacy_selection=index
        self.draw_legacy_choice()

    def draw_legacy_choice(self):
        c,s=self.modal_canvas,self.economy.state
        self.clear_page(c)
        c.paper_image=self.art.parchment(760,680)
        c.create_image(0,0,image=c.paper_image,anchor="nw")
        self.text(c,28,47,"Choose a permanent memory",24,BURGUNDY,"Georgia")
        self.text(c,28,93,"Bonuses stack across Reawakenings. Your choice is granted only when confirmed.",11,MUTED,width=700)
        available=s.awakenings+(1 if self.legacy_reset else 0)
        for i,(name,unlock,targets,bonus,description) in enumerate(LEGACIES):
            y=137+i*68
            c.create_rectangle(26,y,734,y+57,fill=LIGHT,outline=TEAL if self.legacy_selection==i else GOLD,width=2 if self.legacy_selection==i else 1)
            self.text(c,40,y+9,name,15,BURGUNDY,"Georgia")
            self.text(c,40,y+34,description+f" · currently chosen {s.legacies[i]} times",10,MUTED)
            self.button(c,536,y+13,181,30,"SELECTED" if self.legacy_selection==i else "Choose" if available>=unlock else f"After Reawakening {unlock}",lambda j=i:self.select_legacy(j),enabled=available>=unlock,primary=self.legacy_selection==i)
        self.text(c,28,555,(f"Receive {self.economy.reward()} Moon Seals · retain {len(self.retain)} talismans · next goal {number(rebirth_target(s.awakenings+1))} Stardust" if self.legacy_reset else f"{s.legacy_pending} unclaimed choice(s). No reset will occur."),11,TEAL,width=704)
        def accept():
            if self.legacy_selection is None:return
            if self.legacy_reset:
                self.dismiss(force=True)
                self.perform_prestige()
            elif self.economy.choose_legacy(self.legacy_selection):
                self.save()
                self.dismiss(force=True)
                self.draw_ui()
        self.button(c,28,610,455,37,"Reawaken with this memory" if self.legacy_reset else "Claim permanent memory",accept,enabled=self.legacy_selection is not None,primary=True)
        self.button(c,505,610,228,37,"Keep tending",lambda:self.dismiss(force=True))

    def select_building(self, i):
        self.selected = i
        if i==1:
            self.economy.state.garden_selected=True
            self.guide.update()
            self.save()
        self.set_tab("Production")
        self.panel.yview_moveto((54+i*190)/1012)

    def draw_scene(self):
        if self.in_menu or self.settings_open:
            return
        c = self.scene
        c.delete("all")
        w, h = self.scene_width, self.scene_height
        c.create_image(0, 0, image=self.art.sky(w, h), anchor="nw", tags="sky")
        sx, sy = w/1000, h/1000
        def line(points, **kw):
            return c.create_line(*[v*(sx if j%2 == 0 else sy) for j,v in enumerate(points)], **kw)
        def oval(box, **kw):
            return c.create_oval(box[0]*sx, box[1]*sy, box[2]*sx, box[3]*sy, **kw)
        def poly(points, **kw):
            return c.create_polygon(*[v*(sx if j%2 == 0 else sy) for j,v in enumerate(points)], **kw)
        t = 0 if self.reduced_motion else self.anim_time
        density={"Low":.5,"Standard":1,"High":1.5}[self.preferences.values["density"]]
        state = self.economy.state
        # Restoration adds suspended constellations and warm sanctuary lights.
        seals = len(state.discoveries)
        for k in range(seals):
            a = math.pi + k*math.pi/9
            x, y = 500+245*math.cos(a), 412+210*math.sin(a)
            oval((x-4,y-4,x+4,y+4), fill="#ddc992", outline="")
            if k:
                line((px,py,x,y), fill="#807765", width=1)
            px,py=x,y
        # The heart of the sanctuary.
        oval((436,564,564,617), fill="#343e51", outline="#ae9569", width=2)
        poly((455,568,455,527,500,505,545,527,545,568,500,590), fill="#77727d", outline="#b0a091")
        poly((500,407,531,483,500,537,469,483), fill="#b1a1e0", outline="#ebe0fa", width=2)
        poly((500,407,500,537,469,483), fill="#6e6ba4", outline="")
        if seals >= 5:
            oval((449,448,551,508), outline="#d1b778", width=2)
        # Run-limited restoration projects sit inside the terrace, behind stations.
        if 0 in state.restorations:
            for x,y in ((175,682),(825,682),(470,838),(530,838)):
                line((x,y,x,y-38),fill="#b79a64",width=3)
                oval((x-9,y-50,x+9,y-31),fill="#ead098",outline="#aa8150")
        if 1 in state.restorations:
            for x in (682,755,806):
                poly((x-17,657,x+17,657,x+13,675,x-13,675),fill="#826c66",outline="#b1a58a")
                line((x,655,x-8,630,x+8,641),fill="#87b29c",width=3)
        if 2 in state.restorations:
            line((337,714,432,714,432,735,337,735),fill="#b29168",width=3)
            for x in (350,374,398,422):
                oval((x-5,700,x+5,713),fill="#7dbabc",outline="#dfd9bd")
        if 3 in state.restorations:
            for dx in (-28,0,28):
                poly((610+dx,747,622+dx,753,610+dx,761,598+dx,753),fill="#b58367",outline="#d7be91")
        if 4 in state.restorations:
            oval((408,621,592,690),outline="#b7a777",width=2)
            for j in range(8):
                a=j*math.pi/4
                x,y=500+90*math.cos(a),655+32*math.sin(a)
                poly((x,y-5,x+4,y,x,y+5,x-4,y),fill="#d0bd82",outline="")
        # Higher construction levels add bounded, stationary terrace ornamentation.
        for level in range(2,CONSTRUCTION_MAX_LEVEL+1):
            if self.economy.construction_level(0)>=level:
                for x in (250+level*35,750-level*35):
                    yy=796+(level%2)*13
                    line((x,yy,x,yy-24),fill="#c4a067",width=2)
                    oval((x-6,yy-32,x+6,yy-19),fill="#f1d9a1",outline=GOLD)
            if self.economy.construction_level(1)>=level:
                xx=665+level*34
                poly((xx,636-level*4,xx+7,646,xx,658,xx-7,646),fill="#c5b1e6",outline="#efdefc")
            if self.economy.construction_level(2)>=level:
                yy=699-level*11
                line((336,yy,424,yy),fill="#c5ac7f",width=2)
                for xx in (349,374,399):oval((xx-3,yy-9,xx+3,yy-1),fill="#a2dcd2",outline="")
            if self.economy.construction_level(3)>=level:
                yy=767+level*9
                for xx in (590,610,630):poly((xx,yy-4,xx+8,yy,xx,yy+4,xx-8,yy),fill="#d3a487",outline="#ead2a4")
            if self.economy.construction_level(4)>=level:
                radius=62+level*10
                oval((500-radius,651-radius*.32,500+radius,651+radius*.32),outline="#d3bf88",width=1)
        positions = SCENE_ANCHORS
        for i,(x,y) in enumerate(positions):
            active = state.owned[i] > 0
            unlocked = self.economy.unlocked(i)
            tier=state.research[i]
            colour = BUILDINGS[i].colour if active else "#7a7b89"
            if active and tier==0:
                colour=("#829c97","#988eab","#749997","#ad9085","#a99e80")[i]
            tag = f"building-{i}"
            if active:
                glow_size=145 if tier==0 else 230 if tier==1 else 270
                c.create_image(x*sx,(y-40)*sy,image=self.art.glow(colour,int(glow_size*sx),int(glow_size*sy)),tags="aura")
            before = set(c.find_all())
            fw,fh=SCENE_FOOTPRINTS[i]
            oval((x-fw,y-fh/2,x+fw,y+fh), fill="#303d4a", outline=colour if unlocked else "#555864", width=2)
            if i == 0:
                poly((x-53,y-45,x+53,y-45,x+49,y+4,x-49,y+4), fill="#686c7a", outline="#b3a792")
                oval((x-55,y-64,x+55,y-29), fill="#304b60", outline=colour, width=3)
                oval((x-41,y-58,x+41,y-34), fill="#5eaaa9" if active else "#515b70", outline="")
                for j in range(1 if tier==0 else 3):
                    yy = y-65-((t*22+j*25)%80)
                    oval((x-5+j*10,yy-3,x+1+j*10,yy+3), fill=colour, outline="")
            elif i == 1:
                for j,(dx,dy,size) in enumerate(((-38,0,65),(0,-8,109),(36,3,74),(-5,15,47))):
                    poly((x+dx,y+dy-size,x+dx+20,y+dy-30,x+dx+10,y+dy,x+dx-19,y+dy-20), fill=colour, outline="#d6c5ec" if active else "#9494a2")
                    line((x+dx,y+dy-size,x+dx,y+dy-12), fill="#eee3ff" if active else "#9d9eae")
            elif i == 2:
                line((x-42,y-6,x-42,y-118,x+37,y-118,x+37,y-32), fill="#b99c70", width=4)
                poly((x-23,y-101,x-7,y-101,x-7,y-71,x+12,y-35,x-40,y-35,x-23,y-71), fill="#365b65", outline=colour, width=2)
                poly((x-27,y-61,x-5,y-61,x+7,y-39,x-35,y-39), fill=colour, outline="")
                oval((x+18,y-53,x+58,y-2), fill="#4a7b80" if active else "#515b70", outline=colour, width=2)
                for j in range(1 if tier==0 else 3):
                    yy=y-41-((t*17+j*17)%40)
                    oval((x-20,yy,x-14,yy+6), outline=colour)
            elif i == 3:
                for dx in (-30,30):
                    line((x+dx,y-20,x+dx*1.4,y+16), fill="#a39a91", width=5)
                oval((x-49,y-68,x+49,y+1), fill="#694c58", outline="#b19483", width=3)
                oval((x-51,y-78,x+51,y-46), fill=colour if active else "#59576c", outline="#dfbba1", width=2)
                if active:
                    for j in range(1 if tier==0 else 4):
                        xx=x+math.sin(t+j*2)*24
                        yy=y-80-((t*27+j*19)%63)
                        oval((xx-4,yy-5,xx+4,yy+5), outline="#e9c6a6")
            else:
                for r in (50,67):
                    oval((x-r,y-r,x+r,y+r), outline=colour, width=2)
                points=[]
                for j in range(5):
                    a=t*.12+j*4*math.pi/5-math.pi/2
                    points.extend((x+49*math.cos(a),y+49*math.sin(a)))
                line(points+points[:2], fill=colour, width=2)
                oval((x-12,y-12,x+12,y+12), fill=colour, outline="#f0dfb0")
            for j in range(state.research[i]):
                a=t*.25+j*2*math.pi/3
                xx,yy=x+71*math.cos(a),y-53+32*math.sin(a)
                poly((xx,yy-7,xx+5,yy,xx,yy+7,xx-5,yy), fill="#e5c67a", outline="")
            if active and tier==0:
                # Hairline cracks, oxidation, and uneven edges make the first stage used.
                line((x-22,y-28,x-10,y-19,x-16,y-9),fill="#4d555c",width=2)
                line((x+20,y-15,x+28,y-22,x+33,y-16),fill="#6b7260",width=2)
                for dx in (-35,-25,28):
                    oval((x+dx,y-4,x+dx+7,y+1),fill="#677667",outline="")
            elif active and tier>=2:
                for j in range(max(2,int((5 if tier==2 else 9)*density))):
                    phase=t*(.8 if i==0 else .5)+j
                    if i==0:
                        xx=x+math.sin(j*2)*25
                        yy=y-30-((t*36+j*17)%120)
                        line((xx,yy+13,xx,yy),fill="#b8efe2",width=2)
                    elif i==1:
                        xx=x+math.sin(phase)*55
                        yy=y-65+math.cos(phase*1.4)*45
                        line((xx-4,yy,xx+4,yy),fill="#eee0ff",width=1)
                        line((xx,yy-6,xx,yy+6),fill="#eee0ff",width=1)
                    elif i==2:
                        xx=x+37
                        yy=y-113+((t*42+j*13)%63)
                        oval((xx-3,yy-5,xx+3,yy+4),fill="#c1f6e8",outline="")
                    elif i==3:
                        xx=x+math.sin(phase)*23
                        yy=y-79-((t*26+j*14)%73)
                        oval((xx-8,yy-8,xx+8,yy+8),outline="#e4c8b5")
                    else:
                        xx=x+82*math.cos(phase*.45)
                        yy=y+55*math.sin(phase*.45)
                        poly((xx,yy-5,xx+5,yy,xx,yy+5,xx-5,yy),fill="#f0d994",outline="")
                if tier==3:
                    oval((x-55,y-16,x+55,y+11),outline="#e4c686",width=2)
            label = BUILDINGS[i].name if unlocked else "Unwritten"
            label_y = y+(94 if i == 4 else 53)
            label_x=x+(-20 if i==0 else 20 if i==1 else 0)
            label_item = c.create_text(label_x*sx,label_y*sy,text=label,fill="#e7dac0" if active else "#bab4b6",font=("Georgia",10),tags="scene-label")
            box = c.bbox(label_item)
            backing = c.create_rectangle(box[0]-5,box[1]-2,box[2]+5,box[3]+2,fill="#2b3647",outline="",tags="scene-label")
            c.tag_lower(backing,label_item)
            if active:
                c.create_text(label_x*sx,label_y*sy+16,text=f"{state.owned[i]} tended",fill="#b9ccc6",font=("Segoe UI",8),tags="scene-label")
            for item in set(c.find_all())-before:
                c.addtag_withtag(tag,item)
            if i==1 and not state.tutorial_skipped and state.tutorial_step==3:
                oval((x-90,y-130,x+90,y+35),outline="#e9bf57",width=3)
        for j in range(int(22*density)):
            x = 130+(j*137)%760 + math.sin(t*.3+j)*17
            y = 230+(j*79)%610 + math.cos(t*.4+j*3)*13
            r = 1.4+.7*math.sin(t*1.4+j)
            oval((x-r,y-r,x+r,y+r),fill="#c9d8bc",outline="")
        for j in range(min(4, 1+sum(state.owned)//12)):
            x=500+math.sin(t*.22+j*2)*270
            y=495+math.cos(t*.29+j*3)*140
            oval((x-10,y-8,x+10,y+8), fill="#385a69",outline="")
            oval((x-4,y-4,x+4,y+4), fill="#bfe9df",outline="")
        c.create_rectangle(12,12,w-12,h-12,outline="#8f8065")
        if not state.spirit_remaining:
            c.create_text(w/2,25,text="THE MOON KEEPS ITS OWN TIME",fill="#d1bd94",font=("Georgia",9))
        c.tag_lower("aura")
        c.tag_lower("sky")
        c.tag_raise("scene-label")
        if state.blessing:
            b=state.blessing
            c.create_text(w/2,47,text=f"BLESSING  +{b['percent']}% {RESOURCES[b['target']]} · {duration(b['remaining'])}",fill="#9cdecf",font=("Segoe UI",10))
        if state.spirit_remaining>0:
            progress=1-state.spirit_remaining/15
            xx=w*.5 if self.reduced_motion else 84+(w-168)*progress
            yy=h*.24 if self.reduced_motion else h*(.22+.035*math.sin(progress*math.pi*4))
            count={"Low":4,"Standard":9,"High":15}[self.preferences.values["density"]]
            for j in range(count):
                phase=j/count
                px=xx-55-phase*85
                py=yy+math.sin(phase*8+(0 if self.reduced_motion else t))*12
                r=1.2+1.8*(1-phase)
                if px-r>14:
                    c.create_oval(px-r,py-r,px+r,py+r,fill="#baa7d1",outline="",tags="visitor")
            c.create_image(xx,yy,image=self.art.moth(0 if self.reduced_motion else int(t*13)%12),tags="visitor")
            c.create_rectangle(xx-75,yy-52,xx+75,yy+52,outline="",fill="",tags="visitor")
            c.create_text(max(100,min(w-100,xx)),max(22,yy-61),text="Celestial visitor · click",fill="#f3e7cf",font=("Segoe UI",10),tags="visitor")

    def dialog(self, title, body, confirm, callback=None, cancel=None, on_cancel=None):
        self.dismiss(force=True)
        self.tooltip.hide()
        dialog = tk.Toplevel(self.root)
        self.modal = dialog
        self.modal_cancel = on_cancel
        self.modal_accept = None
        dialog.title(title)
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.configure(bg=GOLD)
        canvas = tk.Canvas(dialog, width=550, height=450, highlightthickness=0, bg=PAPER)
        self.modal_canvas = canvas
        canvas.pack(padx=2,pady=2)
        canvas.paper_image = self.art.parchment(550,450)
        canvas.create_image(0,0,image=canvas.paper_image,anchor="nw")
        # The parchment title bar carries the journal heading.
        self.text(canvas,28,57,title,23,BURGUNDY,"Georgia",width=490)
        body_item=self.text(canvas,28,112,body,12,INK,width=490)
        if body and canvas.bbox(body_item)[3]>368:
            canvas.delete(body_item)
            text_area=tk.Text(dialog,font=("Segoe UI",12),bg=LIGHT,fg=INK,wrap="word",relief="flat",padx=8,pady=6)
            text_area.place(x=30,y=113,width=477,height=252)
            text_area.insert("1.0",body)
            text_area.configure(state="disabled")
            bar=tk.Scrollbar(dialog,command=text_area.yview)
            bar.place(x=508,y=113,width=16,height=252)
            text_area.configure(yscrollcommand=bar.set)
        def accept():
            if self.modal_accept:
                self.modal_accept()
                return
            self.dismiss(force=True)
            if callback:
                callback()
        self.button(canvas,28,391,290,36,confirm,accept,primary=True)
        if cancel:
            self.button(canvas,330,391,192,36,cancel,self.dismiss)
        dialog.protocol("WM_DELETE_WINDOW",lambda:self.dismiss(force=True))
        dialog.bind("<Escape>",lambda e:self.dismiss(force=True))
        dialog.bind("<F11>",lambda e:self.toggle_fullscreen())
        dialog.update_idletasks()
        x=self.root.winfo_rootx()+(self.root.winfo_width()-550)//2
        y=self.root.winfo_rooty()+(self.root.winfo_height()-450)//2
        dialog.geometry(f"+{max(0,x)}+{max(0,y)}")
        self.frame_window(dialog,title or "Starstruck Atelier",lambda:self.dismiss(force=True))
        dialog.grab_set()
        dialog.focus_set()

    def dismiss(self, force=False):
        if self.modal:
            modal,self.modal=self.modal,None
            cancel=getattr(self,"modal_cancel",None)
            modal.grab_release()
            self.destroy_window(modal)
            if cancel and not force:
                cancel()

    def sync_time(self):
        now=time.monotonic()
        if not self.in_menu:
            elapsed=now-self.last_time
            self.economy.advance(elapsed)
            visible=not self.settings_open and not self.modal and not self.tome_window and not self.tree_window and self.root.state()!="iconic" and self.preferences.values["spirits"]
            if self.encounters.advance(elapsed,visible):
                self.save()
            if Deliveries(self.economy).generate():
                self.save()
        self.last_time=now

    def save(self):
        try:
            self.store.save(self.economy.state)
            self.save_status="Journal saved · " + time.strftime("%H:%M")
            return True
        except (OSError, ValueError) as exc:
            self.save_status="Could not save — " + str(exc)[:80]
            return False

    def tick(self):
        self.sync_time()
        now=time.monotonic()
        self.anim_time=now
        self.music.poll()
        if now-self.last_save >= 30 and not self.in_menu and not self.store.blocked:
            self.save()
            self.last_save=now
        pressed=any(getattr(w,"controls",None) and w.controls.pressed for w in (self.background,self.panel))
        if now-self.last_ui >= .5 and not pressed:
            self.draw_ui()
            if self.tree_window:
                self.draw_tree_detail()
                if not self.tree_gesture and not getattr(getattr(self.tree_toolbar,"controls",None),"pressed",None):
                    self.draw_tree()
            self.last_ui=now
            if self.tome_window and self.tome_signature != (tuple(self.economy.state.chapters_unlocked),tuple(self.economy.state.chapters_read)):
                self.draw_tome()
        if not self.in_menu and not self.settings_open:
            self.draw_scene()
        self.timer=self.root.after(250 if self.in_menu or self.settings_open or self.reduced_motion else round(1000/self.preferences.values["fps"]),self.tick)

    def close(self):
        self.sync_time()
        if not self.in_menu and not self.store.blocked and not self.save():
            self.dialog("The journal could not be saved",self.save_status+"\n\nRetry after making the save location writable, or close without saving this session.","Retry saving",self.close,cancel="Close without saving",on_cancel=self.destroy)
            return
        if not self.root.attributes("-fullscreen"):
            self.preferences.values["width"]=self.root.winfo_width()
            self.preferences.values["height"]=self.root.winfo_height()
        self.save_preferences()
        self.destroy()

    def destroy(self):
        if self.timer:
            self.root.after_cancel(self.timer)
        if self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        self.tooltip.hide()
        self.dispose_controls(self.root)
        self.close_tome()
        self.close_tree()
        for frame in list(self.frames.values()):frame.dispose()
        self.frames.clear()
        self.music.close()
        self.root.destroy()


def main():
    if os.name == "nt":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StarstruckAtelier.Desktop")
    root=tk.Tk()
    AtelierApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
