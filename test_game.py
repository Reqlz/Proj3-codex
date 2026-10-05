"""Deterministic economy, save, and pacing checks; no GUI is launched."""
import copy
import json
import math
import random
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from main import (BUILDINGS, PRESTIGE_TARGET, Economy, SaveStore, State, SlotManager,
                  Crafting, Constellation, Guide, TALISMAN_COSTS, CHAPTERS, can_pay, Deliveries)


def simulated_run(game, limit=12*3600, crafting=False, deliveries=False, branch=None):
    """Return every five minutes; establish new stages, research, then invest.

    Split spare Mana between wells and material producers; reserve enough for
    the next unlocked stage before buying additional producers.
    """
    unlocks = {}
    first_owned = {}
    game.delivery_income=0
    game.capstone_time=None
    courier=Deliveries(game,random.Random(73))
    for seconds in range(0, limit+1, 300):
        if deliveries:
            courier.generate()
            if game.state.contracts and can_pay(game.state,game.state.contracts[0]["cost"]):
                game.delivery_income+=game.state.contracts[0]["reward"][0]
                courier.finish(0)
        for i in range(5):
            if game.unlocked(i):
                unlocks.setdefault(i, seconds)
        # Establish every newly available stage first.
        for i in reversed(range(5)):
            if game.unlocked(i) and not game.state.owned[i]:
                game.buy(i)
            if game.state.owned[i]:
                first_owned.setdefault(i, seconds)
        for i in reversed(range(5)):
            while game.study(i):
                pass
        if branch:
            from main import SpellTree
            tree=SpellTree(game)
            for node,target in ((0,1),(1,2),(2,2),(4,1),(5,1),(3,1),(0,3),(1,3),(2,3)):
                while tree.rank(branch,node)<target and tree.buy(branch,node):
                    pass
                if tree.rank(branch,node)<target:
                    break
            if tree.rank(branch,3) and game.capstone_time is None:
                game.capstone_time=seconds
        if crafting:
            crafter=Crafting(game)
            for i in range(5):
                if can_pay(game.state,tuple(v*10 for v in crafter.price(i))):
                    crafter.craft(i)
                    crafter.equip(i)
                if crafter.can_talisman(i) and can_pay(game.state,tuple(v*5 for v in TALISMAN_COSTS[i])):
                    puzzle=Constellation(i)
                    for star in puzzle.order:
                        puzzle.select(star)
                    crafter.finish_talisman(puzzle)
        # Allocate half to Mana growth, then round-robin resource capacity.
        budget = game.state.resources[0] * .5
        while game.cost(0) <= budget:
            budget -= game.cost(0)
            game.buy(0)
        for _ in range(100):
            bought = False
            for i in range(1, 5):
                if game.unlocked(i) and game.cost(i) <= game.state.resources[0] * .3:
                    bought = game.buy(i) or bought
            if not bought:
                break
        if game.reward():
            return seconds, unlocks, first_owned
        game.advance(300)
    raise AssertionError("Simulation did not reach Reawakening")


class EconomyTests(unittest.TestCase):
    def test_geometric_prices_and_buy_max(self):
        game = Economy()
        for i, building in enumerate(BUILDINGS):
            self.assertAlmostEqual(game.cost(i, 10), sum(building.cost*building.growth**n for n in range(10)))
        game.state.resources[0] = game.cost(0, 17)
        self.assertEqual(game.affordable(0), 17)
        self.assertTrue(game.buy(0, "max"))
        self.assertEqual(game.state.owned[0], 17)
        self.assertAlmostEqual(game.state.resources[0], 0, places=6)
        self.assertFalse(game.buy(0))
        self.assertFalse(game.buy(1, -1))

    def test_unlocks_and_research(self):
        game = Economy()
        game.state.resources = [1e7]*5
        self.assertFalse(game.buy(2))
        game.state.run_mana = BUILDINGS[2].unlock
        self.assertTrue(game.buy(2))
        old_capacity = game.capacities()[2]
        self.assertTrue(game.study(2))
        self.assertEqual(game.capacities()[2], old_capacity*2)
        self.assertIn("study-2", game.state.discoveries)
        game.study(2)
        game.study(2)
        self.assertFalse(game.study(2))
        self.assertFalse(game.study(3))

    def test_supply_and_depletion(self):
        game = Economy(State(owned=[1, 1, 100, 100, 100]))
        flow, net = game.flows()
        self.assertAlmostEqual(flow[2], .1)
        self.assertAlmostEqual(flow[3], .025)
        self.assertAlmostEqual(flow[4], .005)
        game.advance(1000)
        self.assertTrue(all(v >= 0 for v in game.state.resources))
        self.assertAlmostEqual(game.state.resources[4], 5)

    def test_online_offline_equivalence(self):
        state = State(owned=[4, 3, 9, 12, 10], research=[1, 1, 1, 1, 1],
                      resources=[100, 231, 46, 7, 0], saved_at=1000)
        online, offline = Economy(copy.deepcopy(state)), Economy(copy.deepcopy(state))
        for _ in range(7200):
            online.advance(.5)
        elapsed, _ = offline.offline(4600)
        self.assertEqual(elapsed, 3600)
        for a, b in zip(online.state.resources, offline.state.resources):
            self.assertAlmostEqual(a, b, places=6)
        self.assertAlmostEqual(online.state.run_dust, offline.state.run_dust, places=6)
        before = offline.state.resources[:]
        offline.offline(4500)
        self.assertEqual(offline.state.resources, before)

    def test_long_absence_composition(self):
        initial = State(owned=[10, 3, 5, 8, 9], resources=[0, 400, 50, 3, 0])
        one, many = Economy(copy.deepcopy(initial)), Economy(copy.deepcopy(initial))
        one.advance(60*86400)
        for _ in range(60):
            many.advance(86400)
        for a, b in zip(one.state.resources, many.state.resources):
            self.assertAlmostEqual(a, b, places=5)

    def test_prestige_boundaries(self):
        game = Economy(State(owned=[1]*5, research=[2]*5, run_dust=PRESTIGE_TARGET-1))
        self.assertEqual(game.reward(), 0)
        game.state.run_dust = PRESTIGE_TARGET
        self.assertEqual(game.reward(), 3)
        game.state.run_dust = PRESTIGE_TARGET*4
        self.assertEqual(game.reward(), 6)
        game.state.discoveries = ["unlock-4"]
        game.state.reduced_motion = True
        self.assertTrue(game.reawaken())
        self.assertEqual(game.state.owned, [0]*5)
        self.assertEqual(game.state.research, [0]*5)
        self.assertEqual(game.state.resources, [60, 0, 0, 0, 0])
        self.assertEqual(game.state.seals, 6)
        self.assertEqual(game.state.discoveries, ["unlock-4"])
        self.assertTrue(game.state.reduced_motion)

    def test_balanced_first_and_second_run(self):
        game = Economy()
        first, unlocks, owned = simulated_run(game)
        print("First run:", first/60, "minutes; unlocks:", unlocks, "first buildings:", owned)
        self.assertTrue(7200 <= first <= 10800)
        self.assertLessEqual(owned[1], 60)
        self.assertTrue(300 <= unlocks[2] <= 900)
        self.assertTrue(1200 <= unlocks[3] <= 2400)
        self.assertTrue(3600 <= unlocks[4] <= 5400)
        game.reawaken(legacy_choice=0)
        second, _, _ = simulated_run(game)
        print("Second run:", second/60, "minutes")
        self.assertGreater(second, first)
        self.assertLessEqual(second-first,30*60)


class SaveTests(unittest.TestCase):
    def test_roundtrip_and_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            store = SaveStore(Path(temp)/"save.json")
            state = State(owned=[1, 2, 3, 4, 5])
            store.save(state)
            loaded, warning = store.load()
            self.assertEqual(state, loaded)
            self.assertFalse(warning)
            state.seals = 3
            store.save(state)
            store.path.write_text("broken")
            loaded, warning = store.load()
            self.assertEqual(loaded.seals, 0)
            self.assertIn("backup", warning)
            store.save(loaded)
            self.assertEqual(store.read(store.backup).seals, 0)

    def test_invalid_saves_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            store = SaveStore(Path(temp)/"save.json")
            store.path.write_text("broken")
            store.backup.write_text("also broken")
            _, warning = store.load()
            self.assertTrue(warning)
            self.assertTrue(store.blocked)
            with self.assertRaises(OSError):
                store.save(State())
            store.preserve_invalid()
            store.save(State())
            copies = list(Path(temp).glob("*.unreadable-*.json"))
            self.assertEqual(len(copies), 2)
            self.assertEqual({p.read_text() for p in copies}, {"broken", "also broken"})

    def test_malformed_state(self):
        from dataclasses import asdict
        for name, value in (("resources", [float("nan")]*5), ("owned", [-1]*5),
                            ("research", [4]*5), ("played", math.inf), ("seals", 1.5)):
            data = asdict(State())
            data[name] = value
            with self.assertRaises(ValueError):
                State.parse(data)


class CraftingTests(unittest.TestCase):
    def ready(self):
        return Economy(State(resources=[10000]*5, owned=[3]*5, research=[1]*5, run_mana=300000))

    def test_recipe_prices_unlocks_and_duplicate_types(self):
        game=self.ready()
        craft=Crafting(game)
        self.assertEqual(craft.price(3,True,"offline"),(300,40,30,0,0))
        self.assertEqual(craft.price(0,False,"both"),(300,40,25,0,0))
        self.assertTrue(craft.craft(0))
        self.assertFalse(craft.craft(0,True,"both"))
        self.assertTrue(craft.equip(0))
        self.assertFalse(craft.craft(0,True,"offline"))
        self.assertTrue(craft.dismantle(0))
        self.assertTrue(craft.craft(0,True,"both"))
        game.state.owned[2]=0
        self.assertFalse(craft.craft(1,False,"offline"))
        game.state.research=[0]*5
        self.assertFalse(craft.craft(2))

    def test_rack_and_inventory(self):
        game=self.ready()
        craft=Crafting(game)
        for i in range(5):
            self.assertTrue(craft.craft(i))
        for i in range(3):
            self.assertTrue(craft.equip(i))
        self.assertFalse(craft.equip(3))
        game.advance(900)
        self.assertEqual([c["target"] for c in game.state.charms],[3,4])
        self.assertEqual(craft.charm(3)["remaining"],900)
        self.assertTrue(craft.equip(3))

    def test_modes_and_expiry(self):
        for mode in ("online","offline","both"):
            for offline in (False,True):
                with self.subTest(mode=mode,offline=offline):
                    game=self.ready()
                    craft=Crafting(game)
                    craft.craft(0,False,mode)
                    craft.equip(0)
                    start=game.state.resources[0]
                    base=1+3*.65*2
                    active=mode=="both" or mode==("offline" if offline else "online")
                    game.advance(1000,offline=offline)
                    expected=base*(1000+(900*.25 if active else 0))
                    self.assertAlmostEqual(game.state.resources[0]-start,expected)
                    self.assertEqual(len(game.state.charms),0 if active else 1)
                    if not active:
                        self.assertEqual(craft.charm(0)["remaining"],900)

    def test_expiry_partition_equivalence(self):
        game=self.ready()
        craft=Crafting(game)
        for i,mode,long in ((0,"both",False),(1,"offline",True),(2,"online",False)):
            craft.craft(i,long,mode)
            craft.equip(i)
        a,b=Economy(copy.deepcopy(game.state)),Economy(copy.deepcopy(game.state))
        a.advance(10*86400,offline=True)
        for seconds in (123,777,1,2699,86400,774000):
            b.advance(seconds,offline=True)
        for x,y in zip(b.state.resources,a.state.resources):
            self.assertAlmostEqual(x,y,places=6)
        self.assertEqual([ch["target"] for ch in a.state.charms],[2])
        self.assertEqual(a.state.charms[0]["remaining"],900)

    def test_talisman_bonus_and_spark(self):
        game=Economy(State(talismans=[0],seals=3))
        self.assertAlmostEqual(game.flows()[0][0],1.2*1.3)
        game.state.charms=[dict(target=0,mode="online",long=False,remaining=900.,equipped=True,tier=2,bonus=.4,max_duration=900.,infused=False,recharges=0)]
        self.assertAlmostEqual(game.flows()[0][0],1.6*1.3)
        self.assertAlmostEqual(game.flows(True)[0][0],1.2*1.3)

    def test_puzzle_mistakes_hints_and_transaction(self):
        game=self.ready()
        craft=Crafting(game)
        puzzle=Constellation(0)
        stock=game.state.resources[:]
        self.assertFalse(puzzle.select((puzzle.hint()+1)%puzzle.count))
        self.assertEqual(puzzle.path,[])
        self.assertFalse(craft.finish_talisman(puzzle))
        self.assertEqual(game.state.resources,stock)
        puzzle.select(puzzle.hint())
        puzzle.undo()
        self.assertEqual(puzzle.path,[])
        for star in puzzle.order:
            self.assertTrue(puzzle.select(star))
        game.state.resources[1]=0
        self.assertFalse(craft.finish_talisman(puzzle))
        game.state.resources[1]=600
        self.assertTrue(craft.finish_talisman(puzzle))
        self.assertEqual(game.state.resources[1],0)
        self.assertFalse(craft.finish_talisman(puzzle))

    def test_retention_zero_through_three(self):
        for count in range(4):
            game=self.ready()
            game.state.talismans=list(range(5))
            game.state.run_dust=120
            game.state.chapters_read=["charms"]
            game.state.chapters_unlocked.append("charms")
            game.state.discoveries=[f"study-{i}" for i in range(5)]
            Crafting(game).craft(0)
            self.assertTrue(game.reawaken(list(range(count))))
            self.assertEqual(game.state.talismans,list(range(count)))
            self.assertEqual(game.state.charms,[])
            self.assertIn("charms",game.state.chapters_read)
            self.assertTrue(Crafting(game).talisman_unlocked(4))
        game=self.ready()
        game.state.talismans=list(range(5))
        game.state.run_dust=120
        self.assertFalse(game.reawaken([0,1,2,3]))
        self.assertFalse(game.reawaken([0,0]))

    def test_crafting_accelerates_baseline(self):
        baseline,_,_=simulated_run(Economy())
        accelerated,_,_=simulated_run(Economy(),crafting=True)
        print("Crafting run:",accelerated/60,"minutes")
        self.assertLess(accelerated,baseline)


class GuideTests(unittest.TestCase):
    def test_steps_skip_resume_and_replay(self):
        game=Economy()
        guide=Guide(game)
        game.buy(0)
        guide.update()
        self.assertEqual(game.state.tutorial_step,1)
        game.advance(20)
        self.assertEqual(game.state.tutorial_step,2)
        game.buy(1)
        guide.update()
        self.assertEqual(game.state.tutorial_step,3)
        game.state.garden_selected=True
        guide.update()
        self.assertEqual(game.state.tutorial_step,4)
        game.state.tome_opened=True
        guide.update()
        self.assertEqual(game.state.tutorial_step,5)
        guide.restart()
        self.assertEqual(game.state.tutorial_step,1)
        game.state.tutorial_skipped=True
        game.advance(20)
        self.assertEqual(game.state.tutorial_step,1)
        from dataclasses import asdict
        restored=State.parse(asdict(game.state))
        self.assertTrue(restored.tutorial_skipped)
        self.assertEqual(restored.owned,[1,1,0,0,0])

    def test_chapter_unlocks_and_preview(self):
        game=Economy()
        guide=Guide(game)
        guide.read("astral")
        self.assertNotIn("astral",game.state.chapters_unlocked)
        game.state.run_mana=200000
        game.state.owned=[1]*5
        game.state.research[0]=1
        game.state.research[3]=2
        game.state.run_dust=96
        guide.update()
        self.assertEqual(set(game.state.chapters_unlocked),{ch[0] for ch in CHAPTERS})
        unread=set(game.state.chapters_unlocked)-set(game.state.chapters_read)
        self.assertNotIn("astral",unread)
        self.assertIn("reawakening",unread)


class SlotTests(unittest.TestCase):
    def manager(self, directory):
        return SlotManager(Path(directory)/"new",Path(directory)/"old"/"save.json")

    def test_slot_isolation_and_repeat_offline_load(self):
        with tempfile.TemporaryDirectory() as temp:
            slots=self.manager(temp)
            for i in (1,2,3):
                slots.create(i,f"Sky {i}")
                state,_=slots.store(i).load()
                state.saved_at=1000
                state.seals=i
                slots.store(i).save(state,touch=False)
            _,game,elapsed,_,_=slots.open(1,1100)
            self.assertEqual(elapsed,100)
            self.assertAlmostEqual(game.state.resources[0],170)
            _,repeat,elapsed,_,_=slots.open(1,1100)
            self.assertEqual(elapsed,0)
            self.assertEqual(game.state.resources,repeat.state.resources)
            self.assertEqual(slots.store(2).load()[0].resources[0],60)
            self.assertEqual(slots.store(2).load()[0].saved_at,1000)
            with self.assertRaises(ValueError):
                slots.create(1,"Overwrite")
            with self.assertRaises(ValueError):
                slots.store(4)

    def test_rename_preserves_offline_clock_and_delete_isolated(self):
        with tempfile.TemporaryDirectory() as temp:
            slots=self.manager(temp)
            slots.create(1,"One")
            slots.create(2,"Two")
            before=slots.store(1).load()[0].saved_at
            slots.rename(1,"New One")
            self.assertEqual(slots.store(1).load()[0].saved_at,before)
            self.assertTrue(slots.store(1).backup.exists())
            slots.delete(1)
            self.assertFalse(slots.occupied(1))
            self.assertTrue(slots.occupied(2))

    def write_legacy(self, slots):
        from dataclasses import asdict
        old_fields=("resources","owned","research","run_mana","run_dust","lifetime_mana","played","seals","awakenings","discoveries","journal","reduced_motion","saved_at")
        state=asdict(State(seals=7,saved_at=1000))
        slots.legacy.parent.mkdir(parents=True)
        data=json.dumps({"version":1,"state":{key:state[key] for key in old_fields}})
        slots.legacy.write_text(data,encoding="utf-8")
        return data

    def test_legacy_migration_without_overwrite_or_reimport(self):
        with tempfile.TemporaryDirectory() as temp:
            slots=self.manager(temp)
            original=self.write_legacy(slots)
            slots.create(1,"Occupied")
            self.assertIn("slot 2",slots.migrate())
            migrated,_=slots.store(2).load()
            self.assertEqual(migrated.seals,7)
            self.assertEqual(migrated.saved_at,1000)
            self.assertTrue(migrated.tutorial_invite)
            self.assertEqual(slots.legacy.read_text(encoding="utf-8"),original)
            slots.delete(2)
            self.assertEqual(slots.migrate(),"")
            self.assertFalse(slots.occupied(2))

    def test_legacy_backup_and_interrupted_migration(self):
        with tempfile.TemporaryDirectory() as temp:
            slots=self.manager(temp)
            data=self.write_legacy(slots)
            SaveStore(slots.legacy).backup.write_text(data,encoding="utf-8")
            slots.legacy.write_text("bad")
            with patch.object(slots,"mark_migrated",side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    slots.migrate()
            self.assertTrue(slots.occupied(1))
            slots.migrate()
            self.assertTrue(slots.marker.exists())
            self.assertFalse(slots.occupied(2))
            self.assertEqual(slots.store(1).load()[0].seals,7)

    def test_atomic_failure_keeps_original_and_clock(self):
        with tempfile.TemporaryDirectory() as temp:
            store=SaveStore(Path(temp)/"save.json")
            state=State()
            store.save(state)
            original=store.path.read_bytes()
            stamp=state.saved_at
            state.seals=9
            with patch("main.os.replace",side_effect=OSError("disk unavailable")):
                with self.assertRaises(OSError):
                    store.save(state)
            self.assertEqual(store.path.read_bytes(),original)
            self.assertEqual(state.saved_at,stamp)

    def test_extended_state_roundtrip_and_validation(self):
        from dataclasses import asdict
        state=State(talismans=[0,2],charms=[dict(target=0,mode="both",long=True,remaining=100.,equipped=True,tier=2,bonus=.2,max_duration=3600.,infused=False,recharges=0)],chapters_read=["first"])
        self.assertEqual(State.parse(asdict(state)),state)
        data=asdict(state)
        data["charms"]*=2
        with self.assertRaises(ValueError):
            State.parse(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
