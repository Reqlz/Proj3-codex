import unittest
from main import State, Economy, BUILDINGS, Preferences, SAVE_VERSION
from storage import capacities, MAX_LEVELS

class BalanceUpdateTests(unittest.TestCase):
    def test_storage_and_surplus(self):
        s=State(resources=[5000000,1000000,100000,10000,0])
        self.assertEqual(capacities(s)[:4],[250000,100000,15000,500])
        self.assertEqual(MAX_LEVELS,(10,10,10,10,3))
        Economy(s).advance(7200)
        self.assertEqual(s.resources[:4],[5000000,1000000,100000,10000])
    def test_starter_wells_and_preview(self):
        s=State(); e=Economy(s)
        self.assertEqual(e.flows()[0][0],2)
        for n in (1,4,5,6,15):
            s.owned[0]=n
            self.assertAlmostEqual(e.capacities()[0],BUILDINGS[0].rate*(n+.5*min(n,5)))
        s.owned[0]=4
        self.assertAlmostEqual(e.purchase_output(0,10),BUILDINGS[0].rate*10.5)
    def test_scenery_and_defaults(self):
        self.assertEqual(SAVE_VERSION,13)
        self.assertEqual(State().scenery,'Moonlit Ruins')
        self.assertEqual(Preferences.DEFAULTS['presentation'],'Concise')
        self.assertEqual(Preferences.DEFAULTS['tutorial_detail'],'Short')

class CompatibilityTests(unittest.TestCase):
    def test_v12_scenery_default_and_slot_isolation(self):
        import tempfile,json
        from pathlib import Path
        from dataclasses import asdict
        from main import SaveStore
        with tempfile.TemporaryDirectory() as tmp:
            one=SaveStore(Path(tmp)/'one.json');two=SaveStore(Path(tmp)/'two.json')
            s=State(resources=[1e9]*5,rebirth_dust=10000,storage_levels=[6,6,6,6,3])
            data=asdict(s);data.pop('scenery')
            one.path.write_text(json.dumps(dict(version=12,state=data)))
            loaded=one.read(one.path)
            self.assertEqual(loaded,s)
            loaded.scenery='Reflecting Pond';one.save(loaded);two.save(State())
            self.assertEqual(one.load()[0].scenery,'Reflecting Pond')
            self.assertEqual(two.load()[0].scenery,'Moonlit Ruins')
            loaded.owned=[1]*5;e=Economy(loaded);self.assertTrue(e.reawaken())
            self.assertEqual(e.state.scenery,'Reflecting Pond')
    def test_preferences_options_and_old_values(self):
        import tempfile,json
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'settings.json'
            path.write_text(json.dumps(dict(volume=17,reduced_motion=True)))
            p=Preferences(path)
            self.assertEqual(p.values['volume'],17);self.assertTrue(p.values['reduced_motion'])
            self.assertEqual(p.values['presentation'],'Concise')
            for key,value in [('text_size',125),('presentation','invalid'),('chime_volume',101),('tooltip_delay',1)]:
                path.write_text(json.dumps({key:value}))
                self.assertTrue(Preferences(path).notice)
    def test_all_lessons_have_short_and_full_content(self):
        from learning import OPENING,LESSONS,lesson_content
        for step in range(len(OPENING)):
            c=lesson_content(step);self.assertEqual(c['full'],OPENING[step][2]);self.assertTrue(c['short']);self.assertTrue(c['target'])
        for key in LESSONS:
            c=lesson_content(key=key);self.assertEqual(c['full'],LESSONS[key][2]);self.assertLessEqual(c['short'].count('.'),2)
    def test_reduced_motion_retains_preferences(self):
        from scenery import draw_environment_effects
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        prefs=dict(Preferences.DEFAULTS,reduced_motion=True)
        for scene in ('Reflecting Pond','Glowing Hay Field'):
            a=SimpleNamespace(scene=MagicMock(),scene_width=600,scene_height=400,economy=Economy(State(scenery=scene)),reduced_motion=True,anim_time=100,preference=lambda k:prefs[k])
            draw_environment_effects(a);first=a.scene.mock_calls[:];a.scene.reset_mock();a.anim_time=999
            draw_environment_effects(a);self.assertEqual(first,a.scene.mock_calls)
            self.assertTrue(prefs['pond_ripples']);self.assertTrue(prefs['field_sway'])
    def test_chime_failure_is_quiet(self):
        from scenery import ArrivalChime
        from unittest.mock import patch
        with patch.dict('sys.modules',{'pygame':None}):ArrivalChime().play(30)

class PresentationRegressionTests(unittest.TestCase):
    def test_tome_is_shown_after_withdrawn_factory(self):
        from unittest.mock import MagicMock,patch
        from test_overhaul_ui import OverhaulUIBehaviorTests
        a=OverhaulUIBehaviorTests().app();a.close_tree=lambda:None;a.tome_chapter='first';a.tome_all=True
        a.new_window=MagicMock();a.draw_tome=MagicMock()
        with patch('tome_view.tk.Frame'),patch('tome_view.tk.Label'),patch('tome_view.tk.Button'),patch('tome_view.tk.Listbox'),patch('tome_view.tk.Text'),patch('tome_view.tk.Scrollbar'):
            a.open_tome()
        a.tome_window.deiconify.assert_called_once()
    def test_production_action_parity(self):
        from types import SimpleNamespace
        from test_overhaul_ui import OverhaulUIBehaviorTests
        rendered=[]
        for mode in ('Concise','Classic'):
            a=OverhaulUIBehaviorTests().app();a.preferences=SimpleNamespace(values=dict(Preferences.DEFAULTS,presentation=mode))
            a.selected=0;a.quantity=10;a.economy.state.owned[0]=4
            a.production_card(0,50)
            rendered.append([(c['label'],c.get('enabled'),c.get('tip')) for c in a.controls])
        self.assertEqual(*rendered)
    def test_contextual_off_keeps_manual_opening(self):
        from types import SimpleNamespace
        from test_overhaul_ui import OverhaulUIBehaviorTests
        a=OverhaulUIBehaviorTests().app();a.preferences=SimpleNamespace(values=dict(Preferences.DEFAULTS,contextual_lessons=False))
        a.economy.state.tutorial_skipped=True
        a.refresh_learning();self.assertFalse(a.guide_active)

class SceneCacheTests(unittest.TestCase):
    def test_reflections_are_bounded_and_decorative(self):
        from unittest.mock import MagicMock,patch
        from types import SimpleNamespace
        import tkinter as tk
        from scenery import object_reflections
        c=MagicMock(spec=tk.Canvas);c.find_withtag.return_value=(1,)
        c.type.return_value='rectangle';c.coords.return_value=[10,20,40,50]
        c.itemcget.side_effect=lambda item,key:'#667788' if key=='fill' else ''
        a=SimpleNamespace(scene=c,scene_width=500,scene_height=350,economy=Economy(State()),preference=lambda key:True)
        with patch('PIL.ImageTk.PhotoImage',side_effect=lambda im:im.copy()):
            for frame in range(120):object_reflections(a,frame/60,True)
        self.assertEqual(len(a.reflection_frames),12)
        self.assertEqual(c.type.call_count,1)
        self.assertTrue(all(call.kwargs['tags']=='environment' for call in c.create_image.call_args_list))
        c.tag_bind.assert_not_called()

if __name__=='__main__':unittest.main()
