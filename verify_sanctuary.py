"""Real Tk smoke checks; temporary saves only. Run where Tcl/Tk is installed."""
from pathlib import Path
import tempfile
import time
import tkinter as tk
from main import AtelierApp, SaveStore
from learning import LESSONS
from verify_ui import capture


def verify():
    with tempfile.TemporaryDirectory() as tmp:
        root=tk.Tk()
        errors=[]
        root.report_callback_exception=lambda kind,value,trace:errors.append(value)
        app=AtelierApp(root,SaveStore(Path(tmp)/"slot.json"),start_loop=False,show_welcome=False,apply_preferences=False)
        try:
            s=app.economy.state
            s.tutorial_skipped=True;s.guide_step=10;s.materials_tutorial=6;s.lessons_seen=list(LESSONS)
            s.resources=[1000000,100000,10000,1000,100];s.owned=[20]*5;s.research=[1]*5;s.run_mana=1e7
            s.awakenings=6;s.legacies[6]=3
            app.crafting.expand_shelf();app.crafting.expand_shelf()
            for target in range(5):
                assert app.crafting.craft(target)
                assert app.crafting.equip(target)
            def shot(name):
                root.update_idletasks();app.layout();app.draw_ui();app.draw_scene();root.update()
                assert not errors,errors
                capture(app.modal or root,Path("verification")/(name+".png"))
            for size in ("1100x720","1440x900"):
                root.geometry(size)
                app.open_cabinet();shot("100-cabinet-"+size)
                app.crafting_section="Restoration";shot("101-shelves-"+size)
                app.panel.yview_moveto(.62);shot("102-storage-cards-"+size)
                app.panel.yview_moveto(1);shot("102-stardust-storage-"+size)
                app.panel.yview_moveto(0)
                s.station_event=dict(target=1,amount=100,remaining=60)
                shot("103-station-discovery-"+size)
                old=s.resources[1];app.select_building(1)
                assert s.resources[1]>=old+100 and s.station_event is None
                for target in range(5):
                    app.material_information(target);shot("104-material-"+str(target)+"-"+size)
                    app.dismiss(force=True)
                app.open_puzzle(0)
                for star in app.puzzle.order:app.trace_star(star)
                shot("105-complete-route-"+size)
                app.finish_puzzle();assert 0 in s.talismans
                root.update();capture(app.modal,Path("verification")/("106-flare-"+size+".png"))
                deadline=time.monotonic()+2
                while app.modal and time.monotonic()<deadline:root.update();time.sleep(.01)
                assert app.modal is None
                s.talismans=[];s.attunements=[0]*5
            root.attributes("-fullscreen",True);app.open_cabinet();shot("107-sanctuary-fullscreen")
            app.preferences.values["reduced_motion"]=True;shot("108-sanctuary-reduced-motion")
            assert not errors,errors
            print("Sanctuary UI checks passed.")
        finally:app.destroy()

if __name__=="__main__":verify()
