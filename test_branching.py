import copy
from dataclasses import asdict
import json
from pathlib import Path
import random
import struct
import tempfile
import unittest

from main import Economy,State,SpellTree,TREE,Crafting,Deliveries,SaveStore
from presentation import CursorSet
from test_game import simulated_run


class BranchingTests(unittest.TestCase):
    def ready(self):
        return Economy(State(resources=[1e7]*5,owned=[35,100,15,4,1],research=[2]*5))

    def test_every_node_atomic_costs_and_prerequisites(self):
        for branch in TREE:
            e=self.ready();tree=SpellTree(e)
            for node in (1,2,3,4,5):self.assertFalse(tree.available(branch,node))
            for node in (0,1,2,4,5,3):
                for rank in range(tree.maximum(node)):
                    price=tree.price(branch,node)
                    self.assertTrue(tree.available(branch,node))
                    for index,need in enumerate(price):
                        if need:
                            e.state.resources=[1e7]*5
                            e.state.resources[index]=need-.01
                            before=e.state.resources[:]
                            self.assertFalse(tree.buy(branch,node))
                            self.assertEqual(before,e.state.resources)
                    e.state.resources=list(price)
                    self.assertTrue(tree.buy(branch,node))
                    self.assertEqual(e.state.resources,[0]*5)
                self.assertFalse(tree.available(branch,node))
                self.assertFalse(tree.buy(branch,node))

    def test_activity_gates_at_transaction_boundary(self):
        e=self.ready();tree=SpellTree(e)
        e.state.research[3]=1
        e.state.spell_ranks["Deliveries"]=[1,2,2,0]
        e.state.spell_advanced["Deliveries"]=[1,1]
        before=e.state.resources[:]
        for node in range(6):
            self.assertFalse(tree.available("Deliveries",node))
            self.assertFalse(tree.buy("Deliveries",node))
            self.assertIn("second inscription",tree.unlock_reason("Deliveries",node))
        self.assertEqual(before,e.state.resources)
        e.state.research[3]=2
        self.assertTrue(tree.buy("Deliveries",3))
        e.state.owned[3]=0
        e.state.spell_ranks["Charmcraft"][1]=2
        self.assertFalse(tree.buy("Charmcraft",4))
        self.assertIn("infusion",tree.unlock_reason("Charmcraft",4))
        e.state.research=[0]*5
        for branch in ("Sanctuary","Charmcraft"):
            self.assertFalse(tree.buy(branch,0))

    def test_new_effects_and_frozen_charms_contracts(self):
        e=self.ready();c=Crafting(e)
        c.craft(0,long=True,infused=True)
        before=copy.deepcopy(e.state.charms)
        e.state.spell_advanced["Charmcraft"]=[1,1]
        e.state.spell_ranks["Charmcraft"][0]=3
        self.assertEqual(c.price(1),(255,28,0,0,0))
        c.craft(1,long=True,infused=True)
        self.assertEqual(c.charm(1)["max_duration"],6300)
        self.assertEqual(e.state.charms[0],before[0])
        e.state.spell_advanced["Sanctuary"]=[1,1]
        c.restore(0)
        self.assertAlmostEqual(e.bonus(0),1.07)
        for source,normal in ((2,2),(3,2),(4,3)):
            self.assertAlmostEqual(c.transmutation(source,10)[1][source-1],normal*12)
            self.assertLess(normal*1.2,{2:3,3:4,4:5}[source])
        e.state.spell_ranks["Deliveries"][1]=2
        d=Deliveries(e,random.Random(7));d.generate()
        snapshot=copy.deepcopy(e.state.contracts)
        e.state.spell_advanced["Deliveries"]=[1,1]
        self.assertFalse(d.generate())
        self.assertEqual(snapshot,e.state.contracts)
        e.state.contracts=[]
        d=Deliveries(e,random.Random(7));d.generate()
        for i,n in enumerate(snapshot[0]["cost"]):
            if n:self.assertAlmostEqual(e.state.contracts[0]["cost"][i],n*.9,delta=1)
        for i in range(1,4):self.assertAlmostEqual(e.state.contracts[0]["reward"][i],snapshot[0]["reward"][i]*1.5)

    def test_migration_capstones_and_rebirth(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=SaveStore(Path(tmp)/"test.json")
            e=self.ready()
            e.state.spell_ranks["Charmcraft"]=[1,2,2,1]
            data=asdict(e.state);data.pop("spell_advanced")
            store.path.write_text(json.dumps(dict(version=4,state=data)))
            loaded=store.read(store.path)
            self.assertEqual(loaded.spell_ranks,e.state.spell_ranks)
            e=Economy(loaded)
            c=Crafting(e);c.craft(0);ch=c.charm(0);ch["recharges"]=2
            self.assertEqual(c.recharge_price(ch),26)
            e.state.spell_advanced["Sanctuary"]=[1,1]
            store.save(e.state)
            self.assertEqual(store.load()[0],e.state)
            e.state.rebirth_dust=120
            e.reawaken()
            self.assertTrue(all(not any(r) for r in e.state.spell_advanced.values()))

    def test_focused_first_run_capstones(self):
        for branch in TREE:
            e=Economy()
            finish,_,_=simulated_run(e,branch=branch)
            self.assertIsNotNone(e.capstone_time)
            self.assertLessEqual(e.capstone_time,finish)
            self.assertGreaterEqual(e.capstone_time,120*60)
            self.assertLessEqual(e.capstone_time,180*60)
            self.assertGreaterEqual(sum(e.state.spell_ranks[branch]),8)
            self.assertEqual(sum(sum(v) for b,v in e.state.spell_ranks.items() if b!=branch),0)
            print(f"{branch}: capstone {e.capstone_time/60:g}m, rebirth {finish/60:g}m, ranks {e.state.spell_ranks[branch]}")

    def test_cursor_format_and_consistent_hotspots(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind in range(6):
                path=Path(tmp)/f"{kind}.cur"
                CursorSet.generate(path,kind)
                data=path.read_bytes()
                self.assertEqual(struct.unpack_from("<HHH",data), (0,2,1))
                self.assertEqual(struct.unpack_from("<HH",data,10),(2,2))

    def test_construction_levels_prices_and_reset(self):
        e=self.ready();e.state.resources=[1e10]*5;c=Crafting(e)
        for target in range(5):
            first=c.restoration_price(target)
            for level in range(5):
                price=c.restoration_price(target)
                self.assertEqual(price[0],first[0]*2**level)
                self.assertEqual(price[1],first[1]*6**level)
                self.assertTrue(c.restore(target))
                self.assertEqual(e.construction_level(target),level+1)
                self.assertAlmostEqual(e.construction_bonus(target),.05*(level+1))
            self.assertFalse(c.restore(target))
        self.assertEqual(len(e.state.restorations),5)
        e.state.rebirth_dust=120
        self.assertEqual(State.parse(asdict(e.state)),e.state)
        e.reawaken()
        self.assertEqual(e.state.restoration_levels,[0]*5)
        self.assertFalse(e.state.restorations)

    def test_construction_legacy_and_atomic_upgrades(self):
        e=self.ready();c=Crafting(e)
        c.restore(1)
        before=e.state.resources[:]
        price=c.restoration_price(1)
        e.state.resources[1]=price[1]-.1
        before=e.state.resources[:]
        self.assertFalse(c.restore(1))
        self.assertEqual(before,e.state.resources)
        self.assertEqual(e.construction_level(1),1)
        with tempfile.TemporaryDirectory() as tmp:
            store=SaveStore(Path(tmp)/"legacy.json")
            data=asdict(e.state);data.pop("restoration_levels")
            store.path.write_text(json.dumps(dict(version=5,state=data)))
            loaded=store.read(store.path)
            self.assertEqual(loaded.restoration_levels,[0,1,0,0,0])
            self.assertEqual(loaded.resources,e.state.resources)


if __name__=="__main__":unittest.main(verbosity=2)
