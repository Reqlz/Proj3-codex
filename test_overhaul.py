import copy
import json
import math
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from main import Economy, State, Crafting, Guide, Constellation, SaveStore, TALISMAN_COSTS, CHAPTERS
from learning import LESSONS

class OverhaulTests(unittest.TestCase):
    def ready(self):
        return Economy(State(shelf_level=2,resources=[1e9]*5,owned=[10]*5,research=[1]*5,run_mana=1e7,rebirth_dust=120,run_dust=120))

    def charm(self,e,target,pattern="standard",mode="both"):
        c=Crafting(e);self.assertTrue(c.craft(target,mode=mode,pattern=pattern));self.assertTrue(c.equip(target));return c.charm(target)

    def test_five_distinct_abilities(self):
        e=self.ready();c=Crafting(e)
        base=e.cost(0,10);e.state.talismans=[0]
        self.assertEqual(e.cost(0,10),math.ceil(base*.9-1e-9))
        self.charm(e,0);self.assertAlmostEqual(e.synergy_bonuses()[1],.1)
        e.state.talismans=[];before=c.restoration_price(0);e.state.talismans=[1]
        self.assertEqual(c.restoration_price(0)[1],math.ceil(before[1]*.85-1e-9))
        e.state.restoration_levels[0]=3
        self.assertAlmostEqual(e.synergy_bonuses()[0],.27)
        e.state.talismans=[2];self.assertAlmostEqual(e.ingredient_ratio(2),2.7)
        self.charm(e,1);self.assertAlmostEqual(e.synergy_bonuses()[2],.1)
        e.state.talismans=[];duration=c.crafted_stats(True,1)[1]
        e.state.talismans=[3];self.assertEqual(c.crafted_stats(True,1)[1],duration+720)
        self.assertEqual(c.recharge_price(c.charm(0)),9)
        self.charm(e,2);self.assertAlmostEqual(e.synergy_bonuses()[3],.1)
        e.state.talismans=[4];self.assertAlmostEqual(e.synergy_bonuses()[4],.1)
        e.state.charms.pop(0);self.charm(e,3)
        self.assertAlmostEqual(e.synergy_bonuses()[4],.2)

    def test_patterns_links_do_not_recurse(self):
        e=self.ready();e.state.talismans=list(range(5))
        self.charm(e,0,"relay")
        bonuses=e.synergy_bonuses()
        self.assertAlmostEqual(bonuses[0],.1875)
        self.assertAlmostEqual(bonuses[1],.0625+.1)
        self.assertEqual(bonuses[2],0) # Relay's secondary Shards cannot activate Tideglass.
        self.charm(e,1,"chorus");self.charm(e,2,"chorus")
        bonuses=e.synergy_bonuses()
        self.assertAlmostEqual(bonuses[0],.1875+.05+.1)
        self.assertAlmostEqual(bonuses[3],.1+.1)
        self.assertFalse(Crafting(e).craft(4,pattern="relay"))
        self.assertFalse(Crafting(Economy()).pattern_unlocked("chorus"))

    def test_modes_expiration_and_partition_equivalence(self):
        for offline in (False,True):
            a=self.ready();a.state.resources=[0.]*5;a.state.resources[0]=1e9;a.state.resources[1:]=[1e8]*4
            a.state.talismans=list(range(5));a.state.attunements=[3]*5
            for i,mode in enumerate(("online","offline","both")):
                ch=self.charm(a,i,"relay" if i==0 else "chorus",mode);ch["remaining"]=10+5*i
            a.state.resources=[10.,2.,2.,2.,0.]
            b=Economy(copy.deepcopy(a.state))
            a.advance(120,offline)
            for _ in range(120):b.advance(1,offline)
            for x,y in zip(a.state.resources,b.state.resources):self.assertAlmostEqual(x,y,places=6)
            self.assertEqual(a.state.charms,b.state.charms)
            self.assertTrue(all(v>=0 for v in a.state.resources))

    def test_discount_rounding_and_fixed_charm_stats(self):
        e=self.ready();e.state.talismans=[1,3];e.state.spell_ranks["Sanctuary"][0]=3
        self.assertEqual(Crafting(e).restoration_price(0),(510,73,0,0,0))
        ch=self.charm(e,0);before=copy.deepcopy(ch)
        e.state.talismans=[];e.state.spell_late["Charmcraft"]=[1,1,1]
        self.assertEqual(ch,before)
        e.state.talismans=[3];e.state.spell_ranks["Charmcraft"][1]=3;e.state.spell_advanced["Charmcraft"][0]=1
        Crafting(e).dismantle(0);Crafting(e).craft(0,True,"both",4,True)
        self.assertEqual(Crafting(e).charm(0)["max_duration"],12600)
        State.parse(asdict(e.state))

    def test_attunement_payment_practice_and_rebirth(self):
        e=self.ready();c=Crafting(e)
        for rank in range(4):
            p=Constellation(0,rank,seed=102+rank)
            before=e.state.resources[:]
            self.assertFalse(c.finish_talisman(p))
            for star in p.order:self.assertTrue(p.select(star))
            e.state.resources=[0]*5
            self.assertFalse(c.finish_talisman(p))
            e.state.resources=before
            self.assertTrue(c.finish_talisman(p))
            self.assertFalse(c.finish_talisman(p))
            self.assertEqual(e.state.attunements[0],rank)
            self.assertEqual(e.state.resources,[a-b for a,b in zip(before,c.challenge_price(0,rank))])
        p=Constellation(0,3,seed=2,practice=True)
        for star in p.order:p.select(star)
        self.assertFalse(c.finish_talisman(p))
        e.state.talismans=[0,1,2,3,4];e.state.attunements=[3,2,1,0,3]
        e.state.astral_challenge=p.snapshot()
        self.assertFalse(e.reawaken([0,1]));self.assertTrue(e.reawaken([1]))
        self.assertEqual(e.state.talismans,[1]);self.assertEqual(e.state.attunements,[2,2,0,0,2])
        self.assertIsNone(e.state.astral_challenge)
        self.assertTrue(e.reawaken([]) is False) # No new prestige reward is ready.

    def test_seeded_boards_hints_and_alternative_routes(self):
        alternative=False;backtrack=False
        for target in range(5):
            for rank in range(4):
                for seed in range(25):
                    p=Constellation(target,rank,seed)
                    self.assertEqual(p.snapshot(),Constellation(target,rank,seed).snapshot())
                    solution=p.solution();self.assertIsNotNone(solution)
                    alternative |= solution!=p.order
                    for star in p.order:self.assertTrue(p.select(star),p.message)
                    self.assertTrue(p.complete)
                    self.assertTrue(Constellation.restore(p.snapshot()).complete)
                    p.path=[]
                    while not p.complete:
                        hint=p.hint();self.assertIsNotNone(hint);self.assertTrue(p.select(hint))
                    p.path=[p.start]
                    for star in range(p.count):
                        if not p.reason(star) and p.solution(p.path+[star]) is None:
                            p.select(star);self.assertIsNone(p.hint());self.assertIn("Undo",p.message);backtrack=True;break
        self.assertTrue(alternative);self.assertTrue(backtrack)

    def test_invalid_routes_and_snapshots(self):
        p=Constellation(0,3,seed=4)
        self.assertFalse(p.select(p.end));p.select(p.start)
        self.assertFalse(p.select(p.start))
        data=p.snapshot();data["path"]=[p.end]
        with self.assertRaises(ValueError):Constellation.restore(data)
        data=p.snapshot();data["seed"]=True
        with self.assertRaises(ValueError):Constellation.restore(data)
        p.path=p.order[:];p.path.insert(1,p.start)
        self.assertFalse(p.complete)

    def test_v8_migration_and_slot_resume(self):
        e=self.ready();self.charm(e,0);e.state.talismans=[0,1,2];e.state.tutorial_step=5
        old=asdict(e.state)
        for key in ("attunements","astral_challenge","lessons_seen","guide_step","update_tour"):old.pop(key)
        old["charms"][0].pop("pattern")
        with tempfile.TemporaryDirectory() as tmp:
            store=SaveStore(Path(tmp)/"one.json")
            store.path.write_text(json.dumps(dict(version=8,state=old)),encoding="utf8")
            state=store.read(store.path)
            self.assertEqual(state.talismans,[0,1,2]);self.assertEqual(state.charms[0]["pattern"],"standard")
            self.assertEqual(state.guide_step,10);self.assertTrue(state.update_tour)
            p=Constellation(1,1,seed=123);p.select(p.start);state.astral_challenge=p.snapshot()
            state.attunements=[1,0,0,0,0];state.lessons_seen=["research"]
            store.save(state);loaded=store.read(store.path)
            self.assertEqual(asdict(state),asdict(loaded))
            other=SaveStore(Path(tmp)/"two.json");other.save(State())
            self.assertIsNone(other.read(other.path).astral_challenge)

    def test_learning_progress_queue_and_suggestions(self):
        e=Economy();g=Guide(e)
        self.assertIn("Well",g.suggested());e.buy(0);g.update();self.assertEqual(e.state.guide_step,1)
        g.acknowledge();self.assertEqual(e.state.guide_step,2)
        e.state.guide_step=10;e.state.tutorial_skipped=True;e.state.research[0]=1
        self.assertEqual(g.pending_lesson(),"research")
        e.state.lessons_seen.append("research");self.assertIsNone(g.pending_lesson())
        e.state.owned=[1,1,100,0,0];e.state.resources[1]=0
        self.assertIn("Gardens",g.suggested())
        self.assertEqual(g.pending_lesson(),"converter")
        e.state.lessons_seen.append("converter");self.assertEqual(g.pending_lesson(),"shortage")
        g.restart();self.assertEqual(e.state.guide_step,1)

    def test_progression_strategies_and_retained_choices(self):
        from test_game import simulated_run
        times={}
        for name,temporary,talismans in (("baseline",False,False),("temporary",True,False),("talismans",False,True),("combined",True,True)):
            e=Economy()
            times[name]=simulated_run(e,crafting=temporary or talismans,temporary_charms=temporary,talismans=talismans)[0]/60
            self.assertGreater(e.reward(),0)
        self.assertLess(times["combined"],times["baseline"])
        retained=[]
        for target in range(5):
            e=Economy(State(talismans=[target],attunements=[2]*5))
            retained.append(simulated_run(e)[0]/60)
            baseline=self.ready();chosen=Economy(copy.deepcopy(baseline.state))
            chosen.state.talismans=[target];chosen.state.attunements[target]=2
            self.assertGreater(chosen.capacities()[target],baseline.capacities()[target])
        print("Overhaul strategies (minutes):",times,"retained talismans:",retained)

    def test_tome_uses_shared_current_rules(self):
        chapters={key:body for key,title,body in CHAPTERS}
        self.assertIn("Chorus",chapters["charms"])
        self.assertIn("Keep one",chapters["talismans"])
        self.assertNotIn("Keep up to three",chapters["reawakening"])

if __name__=="__main__":unittest.main()
