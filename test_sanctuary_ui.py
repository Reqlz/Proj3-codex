import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from main import AtelierApp,Preferences
import test_overhaul_ui as guide_tests
from astral_systems import Constellation

class SanctuaryUIBehaviorTests(unittest.TestCase):
    def app(self):
        a=guide_tests.OverhaulUIBehaviorTests().app()
        a.preferences=SimpleNamespace(values=dict(Preferences.DEFAULTS))
        a.preferences.values["reduced_motion"]=True
        return a

    def test_cabinet_distinguishes_run_shelves_and_permanent_slots(self):
        a=self.app();s=a.economy.state;s.legacies[6]=2
        a.draw_cabinet(a.panel,(28,109,422,329))
        labels=[kw.get("text","") for coords,kw in a.panel.items]
        self.assertIn("Shelf upgrade 1",labels);self.assertIn("Shelf upgrade 2",labels)
        self.assertEqual(labels.count("Empty place"),3)
        self.assertEqual(a.crafting.rack_capacity(),3)
        self.assertEqual(s.shelf_level,0)

    def test_physical_cabinet_has_depth_feet_and_six_slots(self):
        a=self.app();a.draw_physical_cabinet(a.scene,(855,640,978,830))
        tags=[kw.get('tags') for coords,kw in a.scene.items]
        self.assertGreaterEqual(tags.count('cabinet'),20)
        self.assertTrue(any(kw.get('fill')=='#263d36' for coords,kw in a.scene.items))
        self.assertTrue(any(len(coords)>=6 for coords,kw in a.scene.items))
        icons=[kw.get('text') for coords,kw in a.scene.items if kw.get('text') in ('·','×','✧')]
        self.assertEqual(len(icons),6)

    def test_storage_cards_show_limits_prices_and_blockers(self):
        a=self.app();a.draw_storage_upgrades()
        labels=' '.join(str(kw.get('text','')) for coords,kw in a.panel.items)
        self.assertIn('Stardust storage',labels)
        self.assertIn('Next capacity',labels)
        self.assertEqual(sum('Expand ' in c['label'] for c in a.controls),5)

    def test_pedestal_has_six_empty_sockets_then_continues_in_bounded_space(self):
        a=self.app()
        for count in (0,6,7,12,600):
            a.scene.items=[];a.scene.deleted=[];a.economy.state.awakenings=count
            a.draw_pedestal_stones(a.scene,.5,.35)
            stones=[(coords,kw) for coords,kw in a.scene.items if kw.get("tags")=="pedestal" and len(coords)==4]
            self.assertEqual(len(stones),6 if count<=6 else 12)
            filled=sum(kw.get("fill")=="#c3b5e4" for coords,kw in stones)
            self.assertEqual(filled,0 if count==0 else 6 if count==6 else 7 if count==7 else 12)
            self.assertTrue(all(0<=v<=550 for coords,kw in stones for v in coords))

    def test_visitor_enters_offscreen_and_fades_in_reduced_motion(self):
        a=self.app();a.preferences.values["reduced_motion"]=False
        self.assertLess(a.visitor_position(0,540,350)[0],0)
        self.assertGreater(a.visitor_position(1,540,350)[0],540)
        self.assertEqual(a.visitor_position(0,540,350)[2],0)
        self.assertEqual(a.visitor_position(.5,540,350)[2],1)
        a.preferences.values["reduced_motion"]=True
        self.assertEqual(a.visitor_position(.1,540,350)[0],270)
        self.assertEqual(a.visitor_position(.9,540,350)[0],270)

    def test_material_info_uses_diagram_and_does_not_embed_production_statistics(self):
        a=self.app();a.dialog=MagicMock();a.dismiss=MagicMock()
        for target in range(5):
            a.modal_canvas.items=[];a.modal_canvas.deleted=[]
            a.material_information(target)
            text=" ".join(kw.get("text","") for coords,kw in a.modal_canvas.items)
            self.assertIn("PRODUCED BY",text);self.assertIn("USED FOR",text)
            self.assertNotIn("Stock:",text);self.assertNotIn("gross output:",text)
            self.assertTrue(any(control["label"]=="View production details" for control in a.controls))

    def test_completion_commits_before_animation_and_cannot_pay_twice(self):
        a=self.app();a.modal=object();a.puzzle=Constellation(0,seed=12)
        for star in a.puzzle.order:a.puzzle.select(star)
        a.puzzle_star_positions=[(410+x*390,290+y*130) for x,y in a.puzzle.points]
        before=a.economy.state.resources[:]
        def save():
            self.assertIn(0,a.economy.state.talismans)
            self.assertFalse(getattr(a,"puzzle_celebrating",False))
            return True
        a.save=save;a.finish_puzzle()
        self.assertTrue(a.puzzle_celebrating)
        paid=a.economy.state.resources[:]
        self.assertNotEqual(before,paid)
        a.finish_puzzle();self.assertEqual(a.economy.state.resources,paid)
        callback=a.root.after.call_args.args[1]
        a.cancel_constellation_animation();a.modal=None
        callback();self.assertEqual(a.economy.state.resources,paid)
        self.assertIn(0,a.economy.state.talismans)

    def test_storage_update_can_be_dismissed_and_stays_dismissed(self):
        a=self.app();s=a.economy.state;s.storage_update=True;a.lesson_key='storage_update'
        a.skip_learning()
        self.assertFalse(s.storage_update)
        self.assertIn('storage_update',s.lessons_seen)
        self.assertNotEqual(a.guide.pending_lesson(),'storage_update')

    def test_failed_payment_never_starts_completion_effect(self):
        a=self.app();a.modal=object();a.puzzle=Constellation(0,seed=12)
        for star in a.puzzle.order:a.puzzle.select(star)
        a.puzzle_hint=None;a.economy.state.resources=[0]*5
        a.finish_puzzle()
        self.assertFalse(getattr(a,"puzzle_celebrating",False))
        self.assertEqual(a.economy.state.talismans,[])
        a.root.after.assert_not_called()

if __name__=="__main__":unittest.main()
