"""Exercise actual opening clicks with the live refresh loop and temporary saves."""
import tempfile
import time
import tkinter as tk
from pathlib import Path
from main import AtelierApp,SaveStore


def verify():
    with tempfile.TemporaryDirectory() as temp:
        root=tk.Tk()
        errors=[]
        root.report_callback_exception=lambda kind,value,trace:errors.append(value)
        app=AtelierApp(root,SaveStore(Path(temp)/"windows.json"),show_welcome=False,apply_preferences=False)
        def pump(seconds=.12):
            end=time.monotonic()+seconds
            while time.monotonic()<end:
                root.update()
                time.sleep(.005)
            assert not errors,errors
        def open_by_click(callback):
            app.button(app.background,25,70,170,26,"Window regression",callback)
            app.background.event_generate("<ButtonPress-1>",x=60,y=80)
            app.background.event_generate("<ButtonRelease-1>",x=60,y=80)
            pump(.7)
            window=app.modal or app.tree_window or app.tome_window
            assert window and window.winfo_viewable(),"Opening click lost its window"
            for surface in (root,window):
                native=app.frames[surface].native
                if native:
                    user,handle,*_=native
                    assert not user.GetWindowLongPtrW(handle,-16)&0x00C50000,"Native frame returned"
            assert not any(window.resizable())
            return window
        try:
            s=app.economy.state
            s.owned=[10]*5;s.research=[2]*5;s.resources=[1e6]*5;s.awakenings=3;s.legacies[0]=3
            s.tutorial_skipped=True;s.materials_tutorial=6
            for fullscreen in (False,True):
                root.attributes("-fullscreen",fullscreen)
                app.frames[root].update_visibility()
                pump()
                for callback in (app.open_tree,app.open_tome,app.show_legacy_reallocation,
                                 app.confirm_prestige,lambda:app.confirm_dismantle(0)):
                    window=open_by_click(callback)
                    window.focus_force();pump()
                    assert window.winfo_viewable()
                    root.focus_force();pump()
                    assert window.winfo_viewable(),"Focus change dismissed popup"
                    app.escape();pump()
                    assert not (app.modal or app.tree_window or app.tome_window)
                # Native queued clicks must not run while building a popup.
                app.button(app.background,25,70,170,26,"Queued window",app.open_tree)
                app.background.event_generate("<ButtonPress-1>",x=60,y=80,when="tail")
                app.background.event_generate("<ButtonRelease-1>",x=60,y=80,when="tail")
                pump(.7)
                assert app.tree_window and app.tree_window.winfo_viewable()
                app.background.event_generate("<ButtonPress-1>",x=15,y=60)
                app.background.event_generate("<ButtonRelease-1>",x=15,y=60)
                pump()
                assert app.tree_window is None
            print("Window regression passed: real/queued button clicks, live refresh, fullscreen/windowed, focus changes, native-caption suppression and outside-click cancellation.")
        finally:app.destroy()


if __name__=="__main__":verify()
