import copy
import math
import tempfile
import json
import unittest
from dataclasses import asdict
from pathlib import Path
from main import State, Economy, Crafting, SaveStore, CelestialWorkbench, Deliveries
from storage import capacities, upgrade_price, grant, transaction_fits, seal_multiplier

class StorageTests(unittest.TestCase):
    def ready(self):
        return Economy(State(owned=[10]*5,research=[1]*5,resources=[1000.,1000.,1000.,100.,60.]))

    def test_capacities_upgrades_discounts_and_reset(self):
        e=self.ready();s=e.state
        self.assertEqual(capacities(s),[250000,100000,15000,500,120])
        s.awakenings=2;s.storage_levels=[1,0,0,0,3]
        self.assertEqual(capacities(s),[1000000,200000,30000,1000,960])
        s.storage_levels=[0]*5;s.talismans=[1];s.spell_ranks['Sanctuary'][0]=3
        self.assertEqual(upgrade_price(s,1),(0,14450,0,0,0))
        before=asdict(s);self.assertFalse(e.upgrade_storage(1));self.assertEqual(asdict(s),before)
        s.resources[1]=200000;self.assertTrue(e.upgrade_storage(1));self.assertEqual(s.storage_levels[1],1)
        s.resources[4]=120;e.deposit_stardust("goal");self.assertTrue(e.reawaken());self.assertEqual(e.state.storage_levels,[0]*5)
        self.assertEqual(capacities(e.state)[0],625000)

    def test_full_chain_pauses_without_wasting_ingredients(self):
        e=self.ready();s=e.state;s.resources=capacities(s)
        before=s.resources[:];dust=s.run_dust
        self.assertEqual(e.flows()[0],[0]*5)
        e.advance(86400,offline=True)
        self.assertEqual(s.resources,before);self.assertEqual(s.run_dust,dust)
        s.resources[4]-=1;e.advance(100)
        self.assertAlmostEqual(s.resources[4],120)
        self.assertTrue(all(a<=b+1e-7 for a,b in zip(s.resources,capacities(s))))

    def test_partitioned_time_and_offline_equivalence(self):
        for offline in (False,True):
            e=self.ready();s=e.state;s.resources=[4999990,999999,1000,1,119]
            self.assertTrue(Crafting(e).craft(0,mode='both'));self.assertTrue(Crafting(e).equip(0))
            s.charms[0]['remaining']=17
            other=Economy(copy.deepcopy(s))
            e.advance(86400,offline)
            for seconds in (7,13,29,51,86300):other.advance(seconds,offline)
            for a,b in zip(e.state.resources,other.state.resources):self.assertAlmostEqual(a,b,places=5)
            self.assertAlmostEqual(e.state.run_dust,other.state.run_dust,places=5)

    def test_surplus_preserved_and_banked_reward(self):
        e=self.ready();s=e.state;s.resources=[1e9]*5;s.run_dust=1e12
        e.advance(7*86400,True)
        self.assertEqual(s.resources[0],1e9)
        self.assertEqual(e.reward(),0)
        e.deposit_stardust("goal");self.assertEqual(e.reward(),3)
        s.storage_levels[4]=3;self.assertEqual(e.reward(),3)
        s.rebirth_dust=119;self.assertEqual(e.reward(),0)
        s.rebirth_dust=480;self.assertEqual(e.reward(),6)
        s.rebirth_dust=120;self.assertEqual(e.reward(),3)

    def test_grants_transactions_and_max_batch(self):
        e=self.ready();s=e.state;s.resources[4]=119
        accepted,overflow=grant(s,(0,0,0,0,10))
        self.assertEqual((accepted[4],overflow[4],s.resources[4]),(1,9,120))
        s.resources[2]=capacities(s)[2];s.resources[3]=100
        before=asdict(s);self.assertFalse(Crafting(e).transmute(3,1));self.assertEqual(asdict(s),before)
        s.resources[2]-=5
        self.assertEqual(Crafting(e).transmutation(3,'max')[2],2)
        self.assertTrue(Crafting(e).transmute(3,'max'))
        self.assertTrue(transaction_fits(s,(0,0,1,0,0),(0,0,1,0,0)))

    def test_paid_payouts_reject_overflow_without_costs_or_cooldowns(self):
        e=self.ready();s=e.state;s.resources[0]=capacities(s)[0]
        s.contracts=[dict(cost=[0,10,10,0,0],reward=[100,0,0,0,0])]
        before=asdict(s)
        self.assertFalse(Deliveries(e).finish(0));self.assertEqual(asdict(s),before)
        self.assertFalse(CelestialWorkbench(e).trade('exchange'));self.assertEqual(asdict(s),before)
        s.resources[0]-=100
        self.assertTrue(Deliveries(e).finish(0));self.assertEqual(s.resources[0],capacities(s)[0])
        # Space released by payment counts toward the payout capacity.
        from storage import transact
        self.assertTrue(transact(s,(200,0,0,0,0),(100,0,0,0,0)))
        self.assertEqual(s.resources[0],capacities(s)[0]-100)

    def test_offline_absence_cannot_escape_stardust_limit(self):
        for level in range(4):
            for days in (1,7):
                e=self.ready();s=e.state;s.storage_levels[4]=level
                s.owned=[100]*5;s.research=[3]*5;s.resources=[0]*5
                e.advance(days*86400,True)
                self.assertAlmostEqual(s.resources[4],120*2**level)
                self.assertEqual(e.reward(),0)
                e.deposit_stardust("all")
                self.assertEqual(e.reward(),int(3*math.sqrt(2**level)))
                self.assertLess(e.reward(),100)
                self.assertTrue(all(stock<=limit+1e-7 for stock,limit in zip(s.resources,capacities(s))))

    def test_seeded_partitioning_through_full_and_empty_buffers(self):
        import random
        rng=random.Random(231)
        for _ in range(80):
            s=State(owned=[rng.randrange(1,50) for i in range(5)],research=[rng.randrange(4) for i in range(5)])
            s.talismans=[2];s.storage_levels=[rng.randrange(3) for i in range(5)]
            s.resources=[limit*rng.choice((0,.00001,.5,.99999,1,1.5)) for limit in capacities(s)]
            once=Economy(copy.deepcopy(s));parts=Economy(copy.deepcopy(s));online=Economy(copy.deepcopy(s))
            once.advance(86400,True);online.advance(86400)
            for i in range(96):parts.advance(900,True)
            for a,b,c in zip(once.state.resources,parts.state.resources,online.state.resources):
                self.assertAlmostEqual(a,b,delta=1e-5)
                self.assertAlmostEqual(a,c,delta=1e-5)
            self.assertAlmostEqual(once.state.run_dust,parts.state.run_dust,delta=1e-5)

    def test_every_storage_upgrade_is_affordable_within_previous_capacity(self):
        for target in range(5):
            e=self.ready();s=e.state
            maximum=3 if target==4 else 10
            for level in range(maximum):
                s.resources=capacities(s)
                self.assertTrue(e.upgrade_storage(target))
                self.assertEqual(s.storage_levels[target],level+1)
            self.assertFalse(e.upgrade_storage(target))
        # Largest fixed spell and construction costs fit expanded ordinary stores.
        from main import SpellTree
        s.awakenings=3;s.storage_levels=[10,10,10,10,3]
        for branch in ('Charmcraft','Sanctuary','Deliveries'):
            self.assertTrue(all(cost<=limit for cost,limit in zip(SpellTree(e).price(branch,8),capacities(s))))
        for target in range(5):
            s.restoration_levels[target]=4
            self.assertTrue(all(cost<=limit for cost,limit in zip(Crafting(e).restoration_price(target),capacities(s))))

    def test_guide_storage_update_full_and_banked_progress(self):
        from main import Guide
        e=self.ready();s=e.state;s.tutorial_skipped=True;s.storage_update=True
        guide=Guide(e);self.assertEqual(guide.pending_lesson(),'storage_update')
        s.lessons_seen.append('storage_update');s.storage_update=False;s.resources[4]=120
        self.assertEqual(guide.pending_lesson(),'storage_full')
        self.assertIn('Stardust storage is full',guide.suggested())
        s.resources[4]=0;s.run_dust=1e9
        self.assertFalse(e.reward())

    def test_seal_curve(self):
        self.assertEqual(seal_multiplier(0),1)
        self.assertEqual(seal_multiplier(250),26)
        self.assertAlmostEqual(seal_multiplier(500),46.710678118654755)
        self.assertEqual(seal_multiplier(1000),76)
        self.assertEqual(seal_multiplier(105063),1001)
        self.assertEqual(seal_multiplier(1e12),1001)
        self.assertTrue(all(seal_multiplier(n+1)>=seal_multiplier(n) for n in range(2000)))

    def test_backup_recovery_and_slot_isolation_include_storage(self):
        with tempfile.TemporaryDirectory() as tmp:
            stores=[SaveStore(Path(tmp)/f'slot-{i}.json') for i in range(2)]
            first=self.ready().state;first.storage_levels=[1,2,3,4,3]
            second=self.ready().state;second.storage_levels=[0]*5
            stores[0].save(first);stores[0].save(first);stores[1].save(second)
            stores[0].path.write_text('broken')
            recovered,warning=stores[0].load()
            self.assertIn('backup',warning)
            self.assertEqual(recovered.storage_levels,first.storage_levels)
            self.assertEqual(stores[1].load()[0].storage_levels,[0]*5)

    def test_v10_surplus_migration_and_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            store=SaveStore(Path(temp)/'slot.json');old=asdict(self.ready().state)
            old.pop('storage_levels');old.pop('storage_update',None);old['resources']=[1e9]*5
            store.path.write_text(json.dumps(dict(version=10,state=old)))
            s=store.read(store.path);self.assertEqual(s.resources,[1e9]*5)
            self.assertEqual(s.storage_levels,[0]*5);self.assertTrue(s.storage_update)
            store.save(s);self.assertEqual(store.read(store.path),s)
            for levels in ([0]*4,[0,0,0,0,4],[11,0,0,0,0],[True,0,0,0,0]):
                bad=asdict(s);bad['storage_levels']=levels
                with self.assertRaises(ValueError):State.parse(bad)

if __name__=='__main__':unittest.main()
