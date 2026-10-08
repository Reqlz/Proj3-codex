"""Late workshop regression checks and pacing, with no live player saves."""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import random
import tempfile
import unittest

from main import (State,Economy,Crafting,SpellTree,Deliveries,CelestialWorkbench,
                  SaveStore,Guide,TREE,INFUSION_COSTS,LEGACIES)
from test_game import simulated_run


class FutureTests(unittest.TestCase):
    def ready(self):
        return Economy(State(shelf_level=2,resources=[1e8]*5,owned=[35,100,15,4,1],research=[3]*5,
                             run_mana=1e6,awakenings=3,seals=12))

    def test_extended_tree_prerequisites_atomicity_and_snapshots(self):
        e=self.ready();t=SpellTree(e);c=Crafting(e)
        c.craft(0,True,"both",4,True)
        original=copy.deepcopy(e.state.charms)
        Deliveries(e,random.Random(8)).generate()
        contracts=copy.deepcopy(e.state.contracts)
        for branch in TREE:
            self.assertFalse(t.buy(branch,6))
            e.state.spell_ranks[branch][3]=1
            for node in (6,7):
                cost=t.price(branch,node)
                saved=e.state.resources[:]
                e.state.resources[4]=cost[4]-.1
                before=e.state.resources[:]
                self.assertFalse(t.buy(branch,node))
                self.assertEqual(e.state.resources,before)
                e.state.resources=saved
                self.assertTrue(t.buy(branch,node))
            e.state.awakenings=2
            self.assertFalse(t.buy(branch,8))
            e.state.awakenings=3
            self.assertTrue(t.buy(branch,8))
            self.assertFalse(t.buy(branch,8))
        self.assertEqual(e.state.charms,original)
        self.assertEqual(e.state.contracts,contracts)
        stats=c.crafted_stats(True,4,True)
        self.assertAlmostEqual(stats[0],.85)
        self.assertAlmostEqual(stats[1],8100)
        self.assertAlmostEqual(e.bonus(1),1.75)
        c.restore(1)
        self.assertAlmostEqual(e.construction_bonus(1),.10)
        self.assertEqual(State.parse(asdict(e.state)),e.state)

    def test_cabinet_lantern_expiry_modes_and_legacy_reallocation(self):
        e=self.ready();c=Crafting(e)
        for i in range(5):c.craft(i)
        for i in range(3):self.assertTrue(c.equip(i))
        self.assertFalse(c.equip(3))
        e.state.legacy_pending=3
        for i in range(3):self.assertTrue(e.choose_legacy(6))
        self.assertFalse(e.choose_legacy(6))
        self.assertEqual(c.rack_capacity(),5)
        self.assertTrue(c.equip(3));self.assertTrue(c.equip(4))
        self.assertTrue(c.light_lantern());self.assertFalse(c.light_lantern())
        a=Economy(copy.deepcopy(e.state));b=Economy(copy.deepcopy(e.state))
        a.advance(5000,True)
        for n in (350,850,1200,2600):b.advance(n,True)
        for x,y in zip(a.state.resources,b.state.resources):self.assertAlmostEqual(x,y,places=5)
        self.assertEqual(a.state.lantern_remaining,0)
        self.assertFalse(e.reallocate_legacies([3,0,0,0,0,0,0]))
        e.advance(1200)
        for i in (3,4):c.dismantle(i)
        counters=(e.state.run_dust,e.state.run_mana,e.state.lifetime_mana)
        price=e.legacy_reallocation_price();before=e.state.resources[4]
        self.assertTrue(e.reallocate_legacies([3,0,0,0,0,0,0]))
        self.assertEqual(e.state.resources[4],before-price)
        self.assertEqual(counters,(e.state.run_dust,e.state.run_mana,e.state.lifetime_mana))
        self.assertFalse(e.reallocate_legacies([3,0,0,0,0,0,0]))

    def test_trades_cooldowns_atomic_payment_and_no_counter_inflation(self):
        e=self.ready();e.state.storage_levels=[4,4,4,4,3];bench=CelestialWorkbench(e)
        for kind in ("exchange","quarry"):
            cost,reward=bench.quote(kind)
            e.state.resources=[1e5,1e5,1e4,1000,1000]
            ingredient=next(i for i,n in enumerate(cost) if n)
            e.state.resources[ingredient]=cost[ingredient]-.1
            before=e.state.resources[:]
            self.assertFalse(bench.trade(kind));self.assertEqual(e.state.resources,before)
            e.state.resources=[1e5,1e5,1e4,1000,1000]
            counters=(e.state.run_dust,e.state.run_mana,e.state.lifetime_mana)
            self.assertTrue(bench.trade(kind));self.assertFalse(bench.trade(kind))
            self.assertEqual(counters,(e.state.run_dust,e.state.run_mana,e.state.lifetime_mana))
            self.assertEqual(getattr(e.state,kind+"_cooldown"),1200)
        e.advance(1200,True)
        self.assertTrue(bench.trade("exchange"));self.assertTrue(bench.trade("quarry"))
        e.state.owned[4]=0;e.advance(1200)
        self.assertFalse(bench.trade("exchange"))

    def test_reallocation_locked_nodes_shortfalls_and_pending_choices(self):
        e=self.ready();s=e.state;s.legacies[0]=3;s.legacy_pending=2
        cost=e.legacy_reallocation_price()
        s.resources[4]=cost-.1
        before=copy.deepcopy(s)
        self.assertFalse(e.reallocate_legacies([0,3,0,0,0,0,0]))
        self.assertEqual(s,before)
        s.resources[4]=cost
        self.assertFalse(e.reallocate_legacies([0,0,0,0,0,3,0]))
        self.assertFalse(e.reallocate_legacies([0,4,0,0,0,0,0]))
        self.assertTrue(e.reallocate_legacies([0,3,0,0,0,0,0]))
        self.assertEqual(s.resources[4],0);self.assertEqual(s.legacy_pending,2)

    def test_v7_migration_preserves_every_old_stat_and_current_quotes(self):
        e=self.ready();Crafting(e).craft(2,True,"both",2,True)
        e.state.legacies=[2,1,0,0,0,0,0]
        Deliveries(e).generate()
        original=asdict(e.state)
        old=copy.deepcopy(original)
        for name in ("spell_late","exchange_cooldown","quarry_cooldown","materials_tutorial","lantern_remaining"):old.pop(name)
        old["legacies"]=old["legacies"][:6]
        with tempfile.TemporaryDirectory() as tmp:
            store=SaveStore(Path(tmp)/"slot.json")
            store.path.write_text(json.dumps(dict(version=7,state=old)))
            loaded=store.read(store.path)
            original["update_tour"]=True
            original["storage_update"]=True
            original["legacy_pending"]+=1
            self.assertEqual(asdict(loaded),original)
            loaded.exchange_cooldown=1200;loaded.materials_tutorial=4
            store.save(loaded)
            self.assertEqual(store.load()[0],loaded)

    def test_reset_retains_cabinet_and_tutorial_resets_late_systems(self):
        e=self.ready();e.state.legacies[6]=3;e.state.materials_tutorial=4
        Crafting(e).light_lantern();CelestialWorkbench(e).trade("quarry")
        e.state.spell_late["Sanctuary"]=[1,1,1]
        e.state.rebirth_dust=e.state.rebirth_goal
        self.assertTrue(e.reawaken())
        self.assertEqual(e.state.legacies[6],3);self.assertEqual(e.state.materials_tutorial,4)
        self.assertFalse(e.state.lantern_remaining or e.state.quarry_cooldown)
        self.assertTrue(all(not any(v) for v in e.state.spell_late.values()))
        Guide(e).update();self.assertIn("materials",e.state.chapters_unlocked)

    def test_late_trades_and_new_ceiling_reference_pacing(self):
        baseline=Economy();minutes=simulated_run(baseline)[0]/60
        accelerated=Economy();bench=CelestialWorkbench(accelerated)
        # Same five-minute strategy; the optional trades are tried between visits.
        original_advance=accelerated.advance
        commissions=[]
        def advance(seconds,offline=False):
            original_advance(seconds,offline)
            if bench.unlocked():
                for kind in ("exchange","quarry"):
                    if bench.trade(kind):commissions.append(kind)
        accelerated.advance=advance
        faster=simulated_run(accelerated)[0]/60
        self.assertLessEqual(faster,minutes)
        self.assertIn("quarry",commissions)
        # Stay in a third-awakening run beyond the usual milestone to invest.
        late=Economy(State(awakenings=3,seals=12,rebirth_goal=1e9))
        try:simulated_run(late,limit=24*3600,branch="Sanctuary",deliveries=True)
        except AssertionError:pass
        t=SpellTree(late)
        self.assertTrue(t.rank("Sanctuary",3))
        # A late converter consumes its Elixirs; reverse transmutation recovers
        # some for investment without minting new earned-resource counters.
        c=Crafting(late)
        self.assertTrue(c.transmute(4,200))
        self.assertTrue(t.buy("Sanctuary",6))
        self.assertFalse(t.buy("Sanctuary",8))
        print(f"New trades: {faster:g}m vs baseline {minutes:g}m; first post-milestone spell affordable in a 24-hour extended run; final capstone remains a longer-term goal.")


if __name__=="__main__":unittest.main()
