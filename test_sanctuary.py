import copy
import json
import random
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from main import State, Economy, Crafting, SaveStore, CHAPTERS
from sanctuary import (legacy_points,total_legacy_points,cabinet_capacity,pedestal_ring,
                       StationEvents,TRANSMUTATION_BATCHES,MATERIAL_GUIDES)

class SanctuaryTests(unittest.TestCase):
    def ready(self):
        return Economy(State(resources=[1e9]*5,owned=[10]*5,research=[1]*5,run_mana=1e7,rebirth_dust=120,run_dust=120))

    def test_shelves_start_one_atomic_upgrades_and_reset(self):
        e=Economy();c=Crafting(e)
        self.assertEqual(c.rack_capacity(),1)
        self.assertFalse(c.expand_shelf())
        e=self.ready();c=Crafting(e)
        for i in range(3):self.assertTrue(c.craft(i))
        self.assertTrue(c.equip(0));self.assertFalse(c.equip(1))
        e.state.resources[1]=119;before=asdict(e.state)
        self.assertFalse(c.expand_shelf());self.assertEqual(asdict(e.state),before)
        e.state.resources[1]=10000
        for i in (1,2):
            cost=c.shelf_price();stock=e.state.resources[:]
            self.assertTrue(c.expand_shelf());self.assertTrue(c.equip(i))
            self.assertEqual(e.state.resources,[a-b for a,b in zip(stock,cost)])
        self.assertFalse(c.expand_shelf());self.assertEqual(c.rack_capacity(),3)
        e.state.legacies[6]=3;e.state.awakenings=3
        self.assertEqual(c.rack_capacity(),5)
        self.assertTrue(c.light_lantern())
        self.assertTrue(e.reawaken())
        self.assertEqual(e.state.shelf_level,0);self.assertEqual(c.rack_capacity(),3)
        self.assertEqual(e.state.legacies[6],3);self.assertEqual(e.state.lantern_remaining,0)
        self.assertFalse(c.expand_shelf())

    def test_reallocation_and_validation_use_actual_shelf_capacity(self):
        e=self.ready();e.state.awakenings=3;e.state.legacies[6]=2
        c=Crafting(e)
        for i in range(3):c.craft(i);c.equip(i)
        State.parse(asdict(e.state))
        self.assertFalse(e.reallocate_legacies([2,0,0,0,0,0,0]))
        bad=asdict(e.state);bad["legacies"][6]=0
        with self.assertRaises(ValueError):State.parse(bad)
        c.dismantle(1);c.dismantle(2)
        self.assertTrue(e.reallocate_legacies([2,0,0,0,0,0,0]))

    def test_shelf_discounts(self):
        e=self.ready();e.state.talismans=[1];e.state.spell_ranks["Sanctuary"][0]=3
        self.assertEqual(Crafting(e).shelf_price(),(510,87,0,0,0))

    def test_six_stones_twelve_points_and_continued_rewards(self):
        self.assertEqual([legacy_points(i) for i in range(1,9)],[1,1,2,2,3,3,3,3])
        e=self.ready();earned=0
        for awakening in range(1,9):
            e.state.owned=[1]*5;e.state.rebirth_dust=e.state.rebirth_goal
            self.assertTrue(e.reawaken())
            earned+=legacy_points(awakening)
            self.assertEqual(e.state.legacy_pending,earned)
        self.assertEqual(total_legacy_points(6),12)
        self.assertEqual(total_legacy_points(8),18)
        self.assertEqual(pedestal_ring(0),(0,0));self.assertEqual(pedestal_ring(6),(1,0))
        self.assertEqual(pedestal_ring(13),(2,1));self.assertEqual(pedestal_ring(600),(100,0))
        for index in range(6):self.assertTrue(e.choose_legacy(index))
        for _ in range(3):self.assertTrue(e.choose_legacy(6))
        self.assertEqual(e.state.legacy_pending,9)
        self.assertFalse(e.choose_legacy(6))

    def test_v9_migration_preserves_current_places_and_credits_points_once(self):
        e=self.ready();e.state.shelf_level=2;e.state.awakenings=6;e.state.legacies=[3,0,0,0,0,0,3]
        c=Crafting(e)
        for i in range(5):c.craft(i);c.equip(i)
        old=asdict(e.state)
        for field in ("shelf_level","station_event_wait","station_event"):old.pop(field)
        with tempfile.TemporaryDirectory() as directory:
            store=SaveStore(Path(directory)/"save.json")
            store.path.write_text(json.dumps(dict(version=9,state=old)))
            loaded=store.read(store.path)
            self.assertEqual(loaded.charms,e.state.charms)
            self.assertEqual(loaded.shelf_level,2)
            self.assertEqual(loaded.legacy_pending,6)
            self.assertEqual(cabinet_capacity(loaded),5)
            store.save(loaded);again=store.read(store.path)
            self.assertEqual(again,loaded)
            game=Economy(again);game.deposit_stardust("goal");self.assertTrue(game.reawaken())
            self.assertEqual(cabinet_capacity(game.state),3)

    def test_station_events_pause_expire_and_pay_only_once(self):
        e=self.ready();e.state.resources=[10000,1000,100,10,0];events=StationEvents(e,random.Random(8))
        before=e.state.station_event_wait
        events.advance(50000,False)
        self.assertEqual(e.state.station_event_wait,before)
        self.assertTrue(events.advance(before,True))
        offer=copy.deepcopy(e.state.station_event)
        self.assertEqual(offer["amount"],e.flows()[0][offer["target"]]*20)
        events.advance(50000,False);self.assertEqual(e.state.station_event,offer)
        restored=State.parse(asdict(e.state));self.assertEqual(restored.station_event,offer)
        counters=(e.state.run_mana,e.state.run_dust,e.state.lifetime_mana)
        stock=e.state.resources[:]
        self.assertEqual(events.claim((offer["target"]+1)%5),0)
        self.assertEqual(events.claim(offer["target"]),offer["amount"])
        self.assertEqual(events.claim(offer["target"]),0)
        self.assertEqual(e.state.resources[offer["target"]],stock[offer["target"]]+offer["amount"])
        self.assertEqual(counters,(e.state.run_mana,e.state.run_dust,e.state.lifetime_mana))
        events.advance(1000);self.assertIsNotNone(e.state.station_event)
        stock=e.state.resources[:];events.advance(61)
        self.assertIsNone(e.state.station_event);self.assertEqual(e.state.resources,stock)
        self.assertTrue(240<=e.state.station_event_wait<=420)
        e.state.station_event=dict(target=0,amount=10,remaining=60)
        e.state.rebirth_dust=e.state.rebirth_goal
        e.reawaken();self.assertIsNone(e.state.station_event)

    def test_large_transmutation_batches_keep_costs_and_ratios(self):
        self.assertEqual(TRANSMUTATION_BATCHES,(1,100,1000,10000,"max"))
        for source,fee,output in ((2,25,2),(3,100,2),(4,500,3)):
            e=self.ready();c=Crafting(e)
            e.state.storage_levels=[0,0,2,7,0];e.state.resources[source-1]=0
            cost,reward,count=c.transmutation(source,10000)
            self.assertEqual(cost[0],fee*10000)
            self.assertEqual(cost[source],10000)
            self.assertEqual(reward[source-1],output*10000)
            before=e.state.run_dust
            self.assertTrue(c.transmute(source,10000));self.assertEqual(e.state.run_dust,before)
            e.state.resources[0]=fee*123+.5;e.state.resources[source]=200
            self.assertEqual(c.transmutation(source,"max")[2],123)

    def test_six_run_progression_spends_every_point_without_puzzles(self):
        from test_game import simulated_run
        from main import LEGACIES
        e=Economy();minutes=[]
        for awakening in range(1,7):
            minutes.append(simulated_run(e)[0]/60)
            self.assertTrue(e.reawaken())
            while e.state.legacy_pending:
                # Collect every unique benefit, then sprinkle spare production ranks.
                choices=[i for i in range(7) if awakening>=LEGACIES[i][1]
                         and e.state.legacies[i]<(3 if i==6 else 1)]
                choice=choices[0] if choices else (awakening-1)%3
                self.assertTrue(e.choose_legacy(choice))
        self.assertEqual(sum(e.state.legacies),12)
        self.assertTrue(all(e.state.legacies[i]>=1 for i in range(6)))
        self.assertEqual(e.state.legacies[6],3)
        self.assertEqual(e.state.legacy_pending,0)
        self.assertEqual(e.state.talismans,[])
        self.assertTrue(all(0<duration<12*60 for duration in minutes))
        print("Fully spent legacy progression (minutes):",minutes)

    def test_material_information_is_purpose_led(self):
        for purpose,production,uses,diagram in MATERIAL_GUIDES:
            self.assertEqual(len(diagram),3)
            self.assertTrue(purpose and production and uses)
            for statistic in ("Stock:","Gross output:","Net inventory:"):
                self.assertNotIn(statistic,purpose+production+uses)

if __name__=="__main__":unittest.main()
