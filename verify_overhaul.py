"""Real Tk checks for the overhaul, isolated from player saves."""
from pathlib import Path
import tempfile
import time
import tkinter as tk
from main import AtelierApp, SaveStore, State
from learning import LESSONS
from verify_ui import capture

def verify():
    with tempfile.TemporaryDirectory() as tmp:
        root=tk.Tk();root.maxsize(2200,1400)
        errors=[]
        root.report_callback_exception=lambda k,v,t:errors.append(v)
        app=AtelierApp(root,SaveStore(Path(tmp)/"slot.json"),start_loop=False,show_welcome=False,apply_preferences=False)
        def flush():
            root.update_idletasks();app.layout();root.update()
            assert not errors,errors
        def finish_animation():
            deadline=time.monotonic()+2
            while app.modal and time.monotonic()<deadline:
                root.update();time.sleep(.01)
            assert app.modal is None
        def shot(name):
            flush();capture(app.modal or root,Path("verification")/(name+".png"))
        try:
            for size in ("1100x720","1440x900"):
                root.geometry(size);shot("90-guide-"+size)
            s=app.economy.state
            app.action("buy",0);assert s.guide_step==1
            app.finish_lesson();s.resources[0]=1000
            app.action("buy",1);assert s.guide_step==3
            app.select_building(1);assert s.guide_step==4
            app.set_tab("Research");assert s.guide_step==5
            app.finish_lesson();app.set_tab("Workshop");assert s.guide_step==7
            app.finish_lesson();app.finish_lesson();assert s.guide_step==9
            app.open_tome();app.close_tome();flush();assert s.guide_step==10
            s.lessons_seen=list(LESSONS);s.tutorial_skipped=True;s.materials_tutorial=6
            s.owned=[20]*5;s.research=[1]*5;s.run_mana=1e7;s.resources=[1e8]*5
            for size in ("1100x720","1440x900"):
                root.geometry(size)
                app.tab="Workshop";app.crafting_section="Talismans"
                shot("91-talismans-"+size)
                app.open_puzzle(0);shot("92-puzzle-"+size)
                for star in app.puzzle.order:app.trace_star(star)
                app.finish_puzzle();assert 0 in s.talismans
                finish_animation()
                app.open_puzzle(0);shot("93-attunement-"+size)
                for star in app.puzzle.order:app.trace_star(star)
                app.finish_puzzle();finish_animation()
                app.crafting_section="Charms";shot("94-patterns-"+size)
                app.set_pattern("relay");app.crafting_action("craft",0)
                if app.crafting.charm(0):app.crafting_action("equip",0)
                s.talismans=list(range(5));s.attunements=[3,2,1,3,2];s.run_dust=s.rebirth_goal
                app.confirm_prestige();assert not app.retention_decided
                app.toggle_retain(2);assert app.retain=={2}
                shot("95-retention-"+size);app.dismiss(force=True)
                s.talismans=[];s.attunements=[0]*5
            root.attributes("-fullscreen",True);app.crafting_section="Talismans";shot("96-fullscreen-talismans")
            root.attributes("-fullscreen",False)
            app.preferences.values["reduced_motion"]=True;flush()
            print("Overhaul UI passed: guided actions, sizes, puzzles, attunement, patterns, retention, fullscreen and reduced motion.")
        finally:app.destroy()

if __name__=="__main__":verify()
