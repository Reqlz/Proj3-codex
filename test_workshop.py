"""Workshop, migration, encounters, preferences and audio regression tests."""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import Mock, patch

from main import (State, Economy, Crafting, SpellTree, Deliveries, Encounters,
                  SaveStore, Preferences, MusicPlayer, TREE, RECHARGE_COSTS, INFUSION_COSTS,
                  RESTORATION_COSTS, SPIRIT_PERCENTAGES, can_pay)


class WorkshopTests(unittest.TestCase):
    def ready(self):
        return Economy(State(shelf_level=2,resources=[1e7]*5,owned=[35,100,15,4,1],research=[2]*5,run_mana=500000))

    def test_roles_and_atomic_payment_every_variant(self):
        for tier in range(1,5):
            for target in range(5):
                for mode in ("online","offline","both"):
                    e=self.ready()
                    c=Crafting(e)
                    recipe=c.price(target,False,mode,tier,True)
                    self.assertEqual(recipe[4],0)
                    self.assertEqual(recipe[3],INFUSION_COSTS[tier-1])
                    self.assertEqual(recipe,c.price(target,True,mode,tier,True))
                    if target<2 and mode=="online":
                        self.assertEqual(recipe[2],0)
                    for missing in [i for i,n in enumerate(recipe) if n]:
                        e.state.resources=[1e7]*5
                        e.state.resources[missing]=recipe[missing]-.1
                        before=e.state.resources[:]
                        self.assertFalse(c.craft(target,False,mode,tier,True))
                        self.assertEqual(e.state.resources,before)
                    e.state.resources=list(recipe)
                    self.assertTrue(c.craft(target,False,mode,tier,True))
                    self.assertEqual(e.state.resources,[0]*5)
                    self.assertEqual(c.charm(target)["remaining"],1350)
                    self.assertFalse(c.craft(target))

    def test_gates_and_recharge(self):
        e=self.ready()
        c=Crafting(e)
        for tier in (2,3,4):
            owned=e.state.owned[tier]
            e.state.owned[tier]=0
            self.assertFalse(c.can_craft(0,tier=tier))
            e.state.owned[tier]=owned
        e.state.owned[3]=0
        self.assertFalse(c.craft(0,infused=True))
        self.assertFalse(c.craft(0,mode="both"))
        e.state.owned[3]=4
        c.craft(0,tier=2,infused=True)
        self.assertFalse(c.recharge(0))
        c.equip(0)
        self.assertFalse(c.recharge(0))
        e.advance(120)
        ch=c.charm(0)
        for expected in (25,50,100):
            self.assertEqual(c.recharge_price(ch),expected)
            self.assertTrue(c.recharge(0))
            self.assertEqual(ch["remaining"],1350)
            e.advance(1)
        e.state.spell_ranks["Charmcraft"][3]=1
        self.assertEqual(c.recharge_price(ch),103)
        e.advance(1350)
        self.assertIsNone(c.charm(0))
        self.assertFalse(c.recharge(0))
        c.craft(0,tier=2)
        self.assertEqual(c.recharge_price(c.charm(0)),25)

    def test_tree_every_node_and_fixed_stats(self):
        e=self.ready()
        tree=SpellTree(e)
        c=Crafting(e)
        c.craft(0)
        original=copy.deepcopy(c.charm(0))
        for branch in TREE:
            self.assertFalse(tree.buy(branch,1))
            self.assertFalse(tree.buy(branch,3))
            for price in (250,750,2250):
                self.assertEqual(tree.price(branch,0)[2],price)
                self.assertTrue(tree.buy(branch,0))
            for node in (1,2):
                for price in (1000,3000,9000):
                    self.assertEqual(tree.price(branch,node)[2],price)
                    self.assertTrue(tree.buy(branch,node))
            self.assertTrue(tree.buy(branch,4))
            self.assertTrue(tree.buy(branch,5))
            self.assertEqual(tree.price(branch,3)[2],25000)
            self.assertTrue(tree.buy(branch,3))
            self.assertFalse(tree.buy(branch,3))
            self.assertFalse(tree.buy(branch,0))
        self.assertEqual(original,c.charm(0))
        self.assertEqual(c.price(1),(255,28,0,0,0))
        self.assertTrue(c.craft(1,long=True,tier=4,infused=True))
        self.assertAlmostEqual(c.charm(1)["bonus"],.55)
        self.assertAlmostEqual(c.charm(1)["max_duration"],8190)
        self.assertEqual(State.parse(asdict(e.state)),e.state)
        self.assertEqual(c.restoration_price(0),(510,85,0,0,0))
        c.restore(0)
        self.assertAlmostEqual(e.bonus(0),1.20)
        self.assertAlmostEqual(c.transmutation(2)[0][0],17.5)

    def test_restore_transmute_and_reset(self):
        e=self.ready()
        c=Crafting(e)
        for i in range(5):
            self.assertEqual(RESTORATION_COSTS[i][2:],(0,0,0))
            self.assertTrue(c.restore(i))
            self.assertEqual(e.construction_level(i),1)
        e.state.resources=[100000,10000,1000,100,200]
        e.state.rebirth_dust=120
        before=(e.state.run_dust,e.state.run_mana,e.state.lifetime_mana)
        for i,ratio,fee in ((4,3,500),(3,2,100),(2,2,25)):
            stock=e.state.resources[:]
            self.assertTrue(c.transmute(i,10))
            self.assertEqual(e.state.resources[i],stock[i]-10)
            self.assertEqual(e.state.resources[i-1],stock[i-1]+ratio*10)
            self.assertEqual(e.state.resources[0],stock[0]-fee*10)
            self.assertLess(ratio,{2:3,3:4,4:5}[i])
        self.assertEqual(before,(e.state.run_dust,e.state.run_mana,e.state.lifetime_mana))
        e.state.spell_ranks["Sanctuary"][0]=2
        Deliveries(e).generate()
        e.state.blessing=dict(target=0,percent=20,remaining=50)
        e.reawaken()
        self.assertFalse(e.state.restorations or e.state.contracts or e.state.blessing)
        self.assertEqual(e.state.delivery_cooldown,0)
        self.assertTrue(all(not any(v) for v in e.state.spell_ranks.values()))

    def test_delivery_snapshots_cooldowns_and_income(self):
        e=self.ready()
        d=Deliveries(e,random.Random(12))
        base,net=d.baseline()
        self.assertTrue(d.generate())
        offer=copy.deepcopy(e.state.contracts[0])
        self.assertAlmostEqual(offer["reward"][0],net[0]*1200)
        for i,n in enumerate(offer["cost"]):
            if n:
                self.assertIn(i,(1,2,3))
                self.assertTrue(720*net[i]<=n<=1080*net[i]+1)
        e.state.owned[0]*=2
        e.state.blessing=dict(target=0,percent=50,remaining=120)
        self.assertFalse(d.generate())
        self.assertEqual(offer,e.state.contracts[0])
        e.state.resources=[0]*5
        self.assertFalse(d.finish(0))
        self.assertEqual(e.state.resources,[0]*5)
        e.state.resources=offer["cost"][:]
        self.assertTrue(d.finish(0))
        self.assertEqual(e.state.resources,offer["reward"])
        self.assertFalse(d.finish(0))
        self.assertFalse(d.generate())
        e.advance(899,offline=True)
        self.assertFalse(d.generate())
        e.advance(100000,offline=True)
        self.assertEqual(e.state.contracts,[])
        self.assertTrue(d.generate())
        self.assertEqual(len(e.state.contracts),1)
        self.assertTrue(d.finish())
        self.assertEqual(e.state.delivery_cooldown,900)

    def test_delivery_tree_gifts_and_bottlenecks(self):
        e=self.ready()
        e.state.spell_ranks["Deliveries"]=[3,3,3,1]
        d=Deliveries(e,random.Random(9))
        gross,net=d.baseline()
        self.assertTrue(d.generate())
        self.assertEqual(len(e.state.contracts),2)
        for offer in e.state.contracts:
            self.assertAlmostEqual(offer["reward"][0],net[0]*1200*1.3)
            for i in (1,2,3):
                self.assertEqual(offer["reward"][i],0 if offer["cost"][i] else gross[i]*180)
        d.finish()
        self.assertEqual(e.state.delivery_cooldown,720)
        e=self.ready()
        e.state.owned=[1,1,100,100,100]
        self.assertFalse(Deliveries(e).generate())

    def test_delivery_enabled_progression(self):
        from test_game import simulated_run
        baseline=Economy()
        base_time,base_unlocks,_=simulated_run(baseline)
        supplied=Economy()
        delivery_time,delivery_unlocks,_=simulated_run(supplied,deliveries=True)
        self.assertEqual(base_unlocks,delivery_unlocks)
        self.assertGreater(supplied.delivery_income,baseline.state.run_mana*.15)
        self.assertLessEqual(delivery_time,base_time)
        print(f"Delivery run: {delivery_time/60:g} minutes; courier income {supplied.delivery_income:,.0f} Mana")
        e=self.ready()
        e.state.research[3]=1
        self.assertFalse(Deliveries(e).generate())

    def test_continuous_partitioned_all_expiries_and_slots(self):
        e=self.ready()
        c=Crafting(e)
        for i,mode in enumerate(("online","offline","both")):
            c.craft(i,mode=mode,infused=True)
            c.equip(i)
        e.state.blessing=dict(target=1,percent=30,remaining=120)
        e.state.delivery_cooldown=900
        other=Economy(copy.deepcopy(e.state))
        for seconds,offline in ((1500,False),(5000,True),(50,False),(4*86400,True)):
            e.advance(seconds,offline)
            for _ in range(10):
                other.advance(seconds/10,offline)
        for a,b in zip(e.state.resources,other.state.resources):
            self.assertAlmostEqual(a,b,places=5)
        self.assertEqual(e.state.charms,other.state.charms)
        self.assertEqual(e.state.blessing,other.state.blessing)

    def test_encounter_saved_choices_and_one_reward(self):
        e=self.ready()
        encounter=Encounters(e,random.Random(31))
        e.state.spirit_wait=120
        encounter.advance(200,False)
        self.assertEqual(e.state.spirit_wait,120)
        encounter.advance(120)
        self.assertEqual(e.state.spirit_remaining,15)
        encounter.advance(14.99)
        self.assertTrue(encounter.capture())
        offers=copy.deepcopy(e.state.spirit_offer)
        self.assertNotEqual(offers[0]["target"],offers[1]["target"])
        self.assertTrue(all(o["percent"] in SPIRIT_PERCENTAGES for o in offers))
        self.assertFalse(encounter.capture())
        e.state=State.parse(asdict(e.state))
        self.assertEqual(e.state.spirit_offer,offers)
        self.assertTrue(encounter.choose(1))
        self.assertFalse(encounter.choose(0))
        e.advance(86400,True)
        self.assertEqual(e.state.blessing["remaining"],120)
        encounter.advance(120,False)
        e.advance(120)
        self.assertIsNone(e.state.blessing)
        encounter.advance(240)
        self.assertEqual(e.state.spirit_remaining,15)
        encounter.advance(15)
        self.assertFalse(e.state.spirit_offer)
        self.assertTrue(120<=e.state.spirit_wait<=240)

    def test_v2_v3_migration_and_workshop_roundtrip(self):
        with tempfile.TemporaryDirectory() as temp:
            store=SaveStore(Path(temp)/"slot.json")
            for version in (2,3):
                e=self.ready()
                c=Crafting(e)
                c.craft(0,long=True)
                ch=e.state.charms[0]
                ch["bonus"]=.2
                ch["remaining"]=123
                ch["tier"]=0
                data=asdict(e.state)
                for key in ("spell_ranks","contracts","delivery_cooldown"):
                    data.pop(key)
                for key in ("max_duration","recharges","infused"):
                    data["charms"][0].pop(key)
                if version==2:
                    for key in ("tier","bonus"):
                        data["charms"][0].pop(key)
                    for key in ("restorations","spirit_wait","spirit_remaining","spirit_offer","blessing"):
                        data.pop(key)
                store.path.write_text(json.dumps(dict(version=version,state=data)))
                loaded=store.read(store.path)
                self.assertEqual(loaded.resources,e.state.resources)
                self.assertEqual((loaded.charms[0]["tier"],loaded.charms[0]["remaining"],loaded.charms[0]["max_duration"],loaded.charms[0]["bonus"]),(2,123,3600,.2))
            e=self.ready()
            e.state.spell_ranks["Deliveries"]=[3,3,3,1]
            Deliveries(e).generate()
            Crafting(e).craft(0,infused=True)
            e.state.spirit_offer=[dict(target=0,percent=15),dict(target=2,percent=30)]
            store.save(e.state)
            loaded,_=store.load()
            self.assertEqual(e.state,loaded)


class AudioSettingsTests(unittest.TestCase):
    def test_preferences_roundtrip_and_invalid_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"prefs.json"
            p=Preferences(path,reduced_motion=True)
            self.assertTrue(p.values["fullscreen"] and p.values["reduced_motion"])
            p.values.update(fullscreen=False,volume=65,fps=60)
            p.save()
            self.assertEqual(Preferences(path).values,p.values)
            path.write_text('{"volume":-1}')
            self.assertTrue(Preferences(path).notice)

    def test_audio_order_errors_pause_volume_and_shuffle(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)
            for name in ("one.ogg","two.mp3"):
                (path/name).touch()
            config=path/"playlist.json"
            config.write_text(json.dumps(dict(tracks=["one.ogg","missing.wav","two.mp3"])))
            prefs=Preferences(path/"prefs.json")
            backend=Mock()
            player=MusicPlayer(path,prefs,backend)
            self.assertTrue(player.playing)
            self.assertIn("missing.wav",player.warning)
            self.assertEqual(player.tracks[player.index].name,"one.ogg")
            player.next()
            self.assertEqual(player.tracks[player.index].name,"two.mp3")
            player.next()
            self.assertEqual(player.tracks[player.index].name,"one.ogg")
            player.pause()
            self.assertTrue(player.paused)
            player.pause()
            self.assertFalse(player.paused)
            prefs.values["volume"]=75
            player.apply()
            backend.music.set_volume.assert_called_with(.75)
            prefs.values["shuffle"]=True
            with patch("main.random.shuffle") as shuffle:
                player.reload()
                shuffle.assert_called_once()
            config.write_text('{bad')
            player.reload()
            self.assertIn("could not be read",player.status)
            self.assertFalse(player.playing)
            config.write_text('{"tracks":["one.ogg"]}')
            failed=Mock()
            failed.init.side_effect=RuntimeError("no device")
            broken=MusicPlayer(path,prefs,failed)
            self.assertIn("Audio unavailable",broken.status)
            self.assertFalse(broken.playing)
            player.close()


if __name__=="__main__":
    unittest.main(verbosity=2)
