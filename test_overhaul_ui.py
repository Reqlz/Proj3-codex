"""Behavior checks with canvas doubles; real visual checks live in verify_overhaul.py."""
import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from main import AtelierApp, Economy, State, Crafting, Guide
from learning import LESSONS
from astral_systems import Constellation

class Canvas:
    def __init__(self):
        self.button_bindings=[];self.hover_regions=[];self.info_regions=[];self.items=[];self.deleted=[];self.configured={};self.offset=0;self.scroll_calls=0
    def create_text(self,*args,**kw):self.items.append((args,kw));return len(self.items)
    create_rectangle=create_text
    create_line=create_text
    create_image=create_text
    create_polygon=create_text
    create_oval=create_text
    def delete(self,*args):self.deleted.extend(args)
    def coords(self,item,*coords):
        if coords:self.items[item-1]=(coords,self.items[item-1][1])
        return self.items[item-1][0]
    def itemconfigure(self,item,**kw):self.configured.setdefault(item,{}).update(kw)
    def tag_raise(self,*args):pass
    def find_all(self):return tuple(i for i in range(1,len(self.items)+1) if i not in self.deleted)
    def find_withtag(self,tag):return tuple(i for i in self.find_all() if self.items[i-1][1].get("tags")==tag)
    def tag_bind(self,*args):return "binding"
    def tag_unbind(self,*args):pass
    def canvasx(self,v):return v
    def canvasy(self,v):return v+self.offset
    def winfo_width(self):return 450
    def winfo_height(self):return 410
    def winfo_rootx(self):return 0
    def winfo_rooty(self):return 0
    def cget(self,name):return "0 0 450 2240"
    def yview_moveto(self,fraction):self.scroll=fraction;self.scroll_calls+=1

class OverhaulUIBehaviorTests(unittest.TestCase):
    def app(self):
        a=AtelierApp.__new__(AtelierApp)
        a.economy=Economy(State(resources=[100000,90000,10000,100,100],owned=[10]*5,research=[1]*5,run_mana=1e7,run_dust=120))
        a.crafting=Crafting(a.economy);a.guide=Guide(a.economy)
        a.panel=Canvas();a.background=Canvas();a.scene=Canvas();a.modal_canvas=Canvas()
        a.panel_width=450;a.scene_width=540;a.panel_x=600
        a.modal=a.tome_window=a.tree_window=None
        a.in_menu=a.settings_open=False;a.tab="Workshop";a.crafting_section="Talismans"
        a.art=SimpleNamespace(parchment=lambda *args:None)
        a.save=lambda:True;a.sync_time=lambda:None;a.draw_ui=lambda:None;a.shield=lambda widget:None
        a.root=MagicMock()
        a.controls=[]
        def button(c,x,y,w,h,label,callback,**kw):a.controls.append(dict(rect=(x,y,x+w,y+h),label=label,callback=callback,**kw))
        a.button=button
        return a

    def test_cards_puzzle_and_explicit_retention(self):
        a=self.app();a.draw_talisman_page()
        self.assertEqual(sum(c["label"]=="Trace constellation" for c in a.controls),5)
        a.economy.state.talismans=[0,1];a.economy.state.attunements=[3,2,0,0,0]
        a.controls=[];a.draw_talisman_page()
        self.assertIn("Practice · no reward",[c["label"] for c in a.controls])
        self.assertIn("Attune to rank 3",[c["label"] for c in a.controls])
        a.puzzle=Constellation(2,3,seed=123);a.puzzle_hint=None;a.puzzle_message=a.puzzle.message
        a.draw_puzzle();self.assertEqual(len(a.puzzle_star_positions),a.puzzle.count)
        self.assertFalse(next(c for c in a.controls if c["label"]=="Confirm attunement")["enabled"])
        a.retain=set();a.retention_decided=False;a.controls=[];a.draw_retention()
        self.assertFalse(next(c for c in a.controls if c["label"].startswith("Reawaken"))["enabled"])
        a.toggle_retain(1);self.assertEqual(a.retain,{1})
        a.toggle_retain(0);self.assertEqual(a.retain,{0})
        a.retain_none();self.assertTrue(a.retention_decided);self.assertEqual(a.retain,set())

    def test_lesson_queue_targets_gate_and_dialog_delay(self):
        a=self.app();s=a.economy.state;s.guide_step=10;s.tutorial_skipped=True
        a.register_target("tab-Workshop",a.background,(100,100,200,130))
        with patch("overhaul_ui.tk.Frame",MagicMock()),patch("overhaul_ui.tk.Label",MagicMock()),patch("overhaul_ui.tk.Button",MagicMock()):
            a.refresh_learning();self.assertEqual(a.lesson_key,"research");self.assertTrue(a.guide_active)
            self.assertTrue(a.guide_control_allowed(a.background,(100,100,200,130)))
            self.assertFalse(a.guide_control_allowed(a.panel,(0,0,100,40)))
            a.finish_lesson();self.assertIn("research",s.lessons_seen)
            a.modal=object();a.refresh_learning();self.assertFalse(a.guide_active)
            self.assertNotIn("converter",s.lessons_seen)
            a.modal=None;a.refresh_learning();self.assertEqual(a.lesson_key,"converter")
            a.settings_open=True;a.refresh_learning();self.assertFalse(a.guide_active)
            a.settings_open=False;s.lessons_seen=list(LESSONS);a.refresh_learning();self.assertFalse(a.guide_active)

    def test_scene_target_card_does_not_cover_target(self):
        a=self.app();s=a.economy.state;s.guide_step=3;s.garden_selected=False
        a.register_target("building-1",a.scene,(330,180,440,260))
        with patch("overhaul_ui.tk.Frame",MagicMock()),patch("overhaul_ui.tk.Label",MagicMock()),patch("overhaul_ui.tk.Button",MagicMock()):
            a.refresh_learning()
            a.guide_frame.place.assert_called_with(x=a.panel_x+12,y=280,width=a.panel_width-24)
            self.assertEqual(a.guide_target[0],a.scene)

    def test_repeated_refresh_does_not_unmap_card_or_recreate_overlay(self):
        a=self.app();s=a.economy.state;s.guide_step=10;s.tutorial_skipped=True
        a.register_target("tab-Workshop",a.background,(100,100,200,130))
        with patch("overhaul_ui.tk.Frame",MagicMock()),patch("overhaul_ui.tk.Label",MagicMock()),patch("overhaul_ui.tk.Button",MagicMock()):
            a.refresh_learning()
            items=dict(a.background.learning_items)
            count=len(a.background.items)
            a.guide_frame.reset_mock()
            for _ in range(4):a.refresh_learning()
            a.guide_frame.place_forget.assert_not_called()
            a.guide_frame.place.assert_not_called()
            self.assertEqual(a.background.learning_items,items)
            self.assertEqual(len(a.background.items),count)
            a.background.create_rectangle(0,0,100,100)
            a.clear_learning_artwork(a.background)
            self.assertTrue(set(items.values()).isdisjoint(a.background.deleted))

    def test_scroll_mask_covers_content_and_refresh_does_not_scroll_back(self):
        a=self.app();s=a.economy.state;s.guide_step=10;s.tutorial_skipped=True
        s.lessons_seen=["research","converter","shortage"]
        a.crafting.craft(0)
        a.register_target("activity-Charms",a.panel,(12,54,430,155))
        with patch("overhaul_ui.tk.Frame",MagicMock()),patch("overhaul_ui.tk.Label",MagicMock()),patch("overhaul_ui.tk.Button",MagicMock()):
            a.refresh_learning()
            self.assertEqual(a.lesson_key,"crafted")
            mask=a.panel.learning_items["mask-1"]
            self.assertEqual(a.panel.coords(mask)[3],2240)
            a.panel.offset=700
            calls=a.panel.scroll_calls
            a.refresh_learning()
            self.assertEqual(a.panel.scroll_calls,calls)
            self.assertEqual(a.panel.coords(mask)[3],2240)

    def test_highlighted_click_runs_action_and_acknowledges_only_original_lesson(self):
        a=self.app();s=a.economy.state;s.guide_step=10;s.tutorial_skipped=True
        a.guide_active=True;a.lesson_key="research"
        a.guide_target=(a.background,(100,100,200,130))
        def action():
            a.tab="Workshop"
            a.lesson_key="converter"  # An action can redraw or open a new page.
        a.activate_learning_control(a.background,(100,100,200,130),action)
        self.assertEqual(a.tab,"Workshop")
        self.assertIn("research",s.lessons_seen)
        self.assertNotIn("converter",s.lessons_seen)

    def test_hover_dwell_and_action_steps(self):
        a=self.app();s=a.economy.state;s.guide_step=10;s.tutorial_skipped=True
        a.guide_active=True;a.lesson_key="research";a.guide_target=(a.panel,(0,700,100,800))
        a.panel.offset=700
        event=SimpleNamespace(widget=a.panel,x=20,y=20)
        a.learning_hover(event)
        delay,callback=a.root.after.call_args.args
        self.assertEqual(delay,650);self.assertNotIn("research",s.lessons_seen)
        callback();self.assertIn("research",s.lessons_seen)
        a.lesson_key="converter";a.learning_hover(event)
        self.assertEqual(a.root.after.call_count,1) # No chained dismissal under a stationary pointer.
        s.guide_step=0;a.lesson_key=None;a.learning_hover_latched=False
        a.learning_hover(event);self.assertEqual(a.root.after.call_count,1)
        a.activate_learning_control(a.panel,(0,700,100,800),lambda:None)
        self.assertEqual(s.guide_step,0) # Failed purchases still require the action.

    def test_leaving_cancels_hover_and_stale_timer_cannot_dismiss_next_stage(self):
        a=self.app();s=a.economy.state;s.guide_step=10;s.tutorial_skipped=True
        a.guide_active=True;a.lesson_key="research";a.guide_target=(a.panel,(0,0,100,100))
        a.learning_hover(SimpleNamespace(widget=a.panel,x=20,y=20))
        callback=a.root.after.call_args.args[1]
        a.learning_hover(SimpleNamespace(widget=a.panel,x=200,y=200))
        a.root.after_cancel.assert_called_once()
        a.lesson_key="converter";callback()
        self.assertEqual(s.lessons_seen,[])

if __name__=="__main__":unittest.main()
