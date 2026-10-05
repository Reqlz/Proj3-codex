"""Run real Tk UI checks with temporary saves and optional window-only captures."""
import argparse
import ctypes
from ctypes import wintypes
from pathlib import Path
import tempfile
import time
import tkinter as tk
import struct
from unittest.mock import patch

from PIL import Image
from main import AtelierApp, SaveStore, PRESTIGE_TARGET, SlotManager, SCENE_ANCHORS, SCENE_FOOTPRINTS


def capture_part(root):
    user, gdi = ctypes.windll.user32, ctypes.windll.gdi32
    user.GetParent.argtypes = [wintypes.HWND]
    user.GetParent.restype = wintypes.HWND
    user.GetWindowDC.argtypes = [wintypes.HWND]
    user.GetWindowDC.restype = wintypes.HDC
    user.ReleaseDC.argtypes = [wintypes.HWND,wintypes.HDC]
    user.GetWindowRect.argtypes = [wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    user.PrintWindow.argtypes = [wintypes.HWND,wintypes.HDC,wintypes.UINT]
    gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi.CreateCompatibleDC.restype = wintypes.HDC
    gdi.CreateCompatibleBitmap.argtypes = [wintypes.HDC,ctypes.c_int,ctypes.c_int]
    gdi.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi.SelectObject.argtypes = [wintypes.HDC,wintypes.HGDIOBJ]
    gdi.SelectObject.restype = wintypes.HGDIOBJ
    gdi.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi.DeleteDC.argtypes = [wintypes.HDC]
    gdi.GetDIBits.argtypes = [wintypes.HDC,wintypes.HBITMAP,wintypes.UINT,wintypes.UINT,ctypes.c_void_p,ctypes.c_void_p,wintypes.UINT]
    hwnd = user.GetParent(root.winfo_id())
    rect = wintypes.RECT()
    user.GetWindowRect(hwnd,ctypes.byref(rect))
    width,height = rect.right-rect.left,rect.bottom-rect.top
    dc = user.GetWindowDC(hwnd)
    memory = gdi.CreateCompatibleDC(dc)
    bitmap = gdi.CreateCompatibleBitmap(dc,width,height)
    previous = gdi.SelectObject(memory,bitmap)
    try:
        assert user.PrintWindow(hwnd,memory,2), "Window capture failed"
        gdi.SelectObject(memory,previous)
        info = ctypes.create_string_buffer(struct.pack("<IiiHHIIiiII",40,width,-height,1,32,0,width*height*4,0,0,0,0))
        pixels = ctypes.create_string_buffer(width*height*4)
        assert gdi.GetDIBits(memory,bitmap,0,height,pixels,info,0)
        return Image.frombytes("RGB",(width,height),pixels.raw,"raw","BGRX")
    finally:
        gdi.SelectObject(memory,previous)
        gdi.DeleteObject(bitmap)
        gdi.DeleteDC(memory)
        user.ReleaseDC(hwnd,dc)


def capture(root, path):
    """Tile only our window when it exceeds the verification display size."""
    user = ctypes.windll.user32
    user.GetParent.argtypes = [wintypes.HWND]
    user.GetParent.restype = wintypes.HWND
    user.GetWindowRect.argtypes = [wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    user.SetWindowPos.argtypes = [wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
    hwnd = user.GetParent(root.winfo_id())
    rect = wintypes.RECT()
    user.GetWindowRect(hwnd,ctypes.byref(rect))
    width,height = rect.right-rect.left,rect.bottom-rect.top
    sw,sh = root.winfo_screenwidth(),root.winfo_screenheight()
    result = Image.new("RGB",(width,height))
    try:
        for x in sorted({0,min(0,sw-width)}):
            for y in sorted({0,min(0,sh-height)}):
                user.SetWindowPos(hwnd,0,x,y,0,0,0x15)
                root.update()
                time.sleep(.15)
                root.update()
                image = capture_part(root)
                box = (max(0,-x),max(0,-y),min(width,sw-x),min(height,sh-y))
                result.paste(image.crop(box),box[:2])
        result.save(path)
    finally:
        user.SetWindowPos(hwnd,0,rect.left,rect.top,0,0,0x15)
        root.update()


def verify(output=None):
    if output:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        root = tk.Tk()
        root.maxsize(2200, 1400)
        errors = []
        root.report_callback_exception = lambda kind, value, trace: errors.append(value)
        app = AtelierApp(root, SaveStore(Path(temp)/"save.json"), start_loop=False, show_welcome=False,apply_preferences=False)

        def flush():
            root.update_idletasks()
            app.layout()
            root.update()
            assert not errors, errors

        def shot(name):
            flush()
            if output:
                capture(app.modal or root, output/f"{name}.png")

        def click_button(canvas, caption):
            for item in canvas.find_all():
                if canvas.type(item) == "text" and canvas.itemcget(item,"text") == caption:
                    x, y = canvas.coords(item)
                    canvas.event_generate("<Motion>", x=int(x-canvas.canvasx(0)), y=int(y-canvas.canvasy(0)))
                    canvas.event_generate("<Button-1>", x=int(x-canvas.canvasx(0)), y=int(y-canvas.canvasy(0)))
                    canvas.event_generate("<ButtonRelease-1>", x=int(x-canvas.canvasx(0)), y=int(y-canvas.canvasy(0)))
                    root.update()
                    return
            raise AssertionError(f"Button not found: {caption}")

        try:
            shot("01-new-sanctuary")
            click_button(app.panel, "Buy 1 · 30.0 Mana")
            assert app.economy.state.owned[0] == 1, errors
            app.economy.state.run_mana = 500000
            app.economy.state.resources = [1e7, 1e6, 1e5, 1e4, 300]
            app.economy.state.owned = [28, 24, 12, 6, 3]
            app.economy.state.research = [2, 2, 2, 2, 1]
            app.economy.state.run_dust = PRESTIGE_TARGET
            app.economy.discover()
            shot("02-restored-sanctuary")
            # Every scene building must navigate to its matching card.
            for index in range(5):
                item = app.scene.find_withtag(f"building-{index}")[-1]
                x,y = app.scene.coords(item)
                app.scene.event_generate("<Motion>",x=int(x),y=int(y))
                app.scene.event_generate("<Button-1>",x=int(x),y=int(y))
                app.scene.event_generate("<ButtonRelease-1>",x=int(x),y=int(y))
                root.update()
                assert app.selected == index, (index, app.selected, app.scene.find_withtag("current"), (x,y))
            app.set_tab("Research")
            shot("03-research")
            before = app.economy.state.research[0]
            click_button(app.panel,"Inscribe · 180.00k Mana")
            assert app.economy.state.research[0] == before+1
            app.set_tab("Reawakening")
            shot("04-reawakening")
            app.confirm_prestige()
            shot("05-confirmation")
            app.dismiss()
            assert app.economy.state.awakenings == 0
            root.geometry("1100x720")
            flush()
            app.set_tab("Production")
            shot("06-minimum-production")
            app.set_tab("Research")
            shot("07-minimum-research")
            app.set_tab("Reawakening")
            shot("08-minimum-reawakening")
            app.toggle_motion()
            assert app.reduced_motion
            app.anim_time = 1
            app.draw_scene()
            first = [(app.scene.type(i),app.scene.coords(i)) for i in app.scene.find_all()]
            app.anim_time = 4
            app.draw_scene()
            assert first == [(app.scene.type(i),app.scene.coords(i)) for i in app.scene.find_all()]
            app.toggle_motion()
            start = time.perf_counter()
            callbacks = len(app.scene._tclCommands)
            for frame in range(90):
                app.anim_time = frame/30
                app.draw_scene()
            print(f"Scene draw: {(time.perf_counter()-start)/90*1000:.1f} ms/frame")
            assert len(app.scene.find_all()) < 300
            assert len(app.scene._tclCommands) == callbacks
            callbacks = len(app.background._tclCommands) + len(app.panel._tclCommands)
            for _ in range(10):
                app.draw_ui()
            assert len(app.background._tclCommands) + len(app.panel._tclCommands) == callbacks
            app.perform_prestige()
            assert app.economy.state.awakenings == 1
            assert app.economy.state.seals == 3
            assert app.store.load()[0].seals == 3
            app.tick()
            root.update()
            assert not errors, errors
            print("UI passed: purchases, scene selection, research, prestige/cancel, scrolling, both sizes, reduced motion, save, animation.")
        finally:
            app.destroy()


def verify_expansion(output=None):
    output=Path(output) if output else None
    with tempfile.TemporaryDirectory() as temp:
        slots=SlotManager(Path(temp)/"Starstruck",Path(temp)/"Moonveil"/"save.json")
        root=tk.Tk()
        root.maxsize(2200,1400)
        errors=[]
        root.report_callback_exception=lambda kind,value,trace:errors.append(value)
        app=AtelierApp(root,slots=slots,start_loop=False,show_welcome=False,apply_preferences=False)

        def flush():
            root.update_idletasks()
            app.layout()
            root.update()
            assert not errors,errors

        def shot(name,surface=None):
            flush()
            if output:
                capture(surface or app.modal or app.tome_window or root,output/f"{name}.png")

        def click(canvas,caption):
            root.update_idletasks()
            root.update()
            for item in canvas.find_all():
                if canvas.type(item)=="text" and canvas.itemcget(item,"text")==caption:
                    x,y=canvas.coords(item)
                    x,y=int(x-canvas.canvasx(0)),int(y-canvas.canvasy(0))
                    canvas.event_generate("<Motion>",x=x,y=y)
                    canvas.event_generate("<Button-1>",x=x,y=y)
                    canvas.event_generate("<ButtonRelease-1>",x=x,y=y)
                    root.update()
                    assert not errors,errors
                    return
            raise AssertionError("Missing button: "+caption)

        try:
            assert app.in_menu
            shot("20-three-empty-slots")
            click(app.background,"New sanctuary")
            entry=next(w for w in app.modal.winfo_children() if isinstance(w,tk.Entry))
            entry.delete(0,"end")
            entry.insert(0,"The Amber Observatory")
            click(app.modal_canvas,"Create sanctuary")
            assert not app.in_menu and app.active_slot==1
            assert app.economy.state.sanctuary_name=="The Amber Observatory"
            shot("21-guided-first-steps")
            click(app.panel,"Buy 1 · 30.0 Mana")
            app.economy.advance(20)
            app.draw_ui()
            click(app.panel,"Buy 1 · 60.0 Mana")
            app.select_building(1)
            assert app.economy.state.tutorial_step==4
            app.open_tome()
            assert app.economy.state.tutorial_step==5
            shot("22-spell-tome")
            click(app.tome_canvas,"View all chapters")
            app.choose_chapter("astral")
            assert "astral" in app.economy.state.chapters_read
            assert "astral" not in app.economy.state.chapters_unlocked
            shot("23-tome-preview")
            app.close_tome()
            app.economy.state.run_mana=500000
            app.economy.state.resources=[1e7]*5
            app.economy.state.owned=[20,20,12,10,5]
            app.economy.state.research=[2]*5
            app.economy.state.run_dust=120
            app.economy.discover()
            app.guide.update()
            app.set_tab("Workshop")
            app.set_crafting_section("Charms")
            shot("24-charm-rack")
            for i,mode in ((0,"online"),(1,"offline"),(2,"both")):
                app.set_recipe(mode=mode,long=i==1)
                app.crafting_action("craft",i)
                app.crafting_action("equip",i)
            assert len(app.economy.state.charms)==3
            app.panel.yview_moveto(0)
            shot("25-occupied-rack")
            app.open_puzzle(0)
            shot("26-constellation-puzzle")
            click(app.modal_canvas,"Hint")
            assert app.puzzle_hint==app.puzzle.order[0]
            for star in app.puzzle.order:
                x,y=app.puzzle_star_positions[star]
                app.modal_canvas.event_generate("<Motion>",x=int(x),y=int(y))
                app.modal_canvas.event_generate("<Button-1>",x=int(x),y=int(y))
                app.modal_canvas.event_generate("<ButtonRelease-1>",x=int(x),y=int(y))
                root.update()
            assert app.puzzle.complete
            shot("27-completed-trace")
            click(app.modal_canvas,"Bind talisman")
            assert app.economy.state.talismans==[0]
            app.economy.state.talismans=list(range(5))
            app.confirm_prestige()
            app.toggle_retain(1)
            app.toggle_retain(4)
            assert app.retain=={0,2,4}
            shot("28-talisman-retention")
            app.dismiss()
            assert len(app.economy.state.talismans)==5
            # Failed saving must keep the current live sanctuary and slot.
            with patch.object(app.store,"save",side_effect=OSError("Test write failure")):
                assert app.return_to_slots() is False
                assert not app.in_menu and app.active_slot==1
            app.dismiss()
            app.return_to_slots()
            slots.create(2,"The Violet Garden")
            slots.create(3,"The Quiet Crucible")
            app.refresh_slots()
            shot("29-three-sanctuaries")
            app.open_slot(2)
            assert app.economy.state.owned==[0]*5
            assert app.economy.state.charms==[]
            app.open_tome()
            assert app.tome_chapter=="first"
            app.close_tome()
            app.return_to_slots()
            app.open_slot(1)
            if app.modal:
                app.dismiss()
            assert app.economy.state.talismans==list(range(5))
            assert len(app.economy.state.charms)==3
            root.geometry("1100x720")
            flush()
            app.set_tab("Workshop")
            app.set_crafting_section("Charms")
            shot("30-minimum-rack")
            app.panel.yview_moveto(.7)
            shot("31-minimum-talismans")
            app.open_tome("charms")
            shot("32-minimum-tome")
            app.close_tome()
            app.set_tab("Production")
            shot("33-minimum-scene")
            app.confirm_prestige()
            app.toggle_retain(1)
            app.toggle_retain(4)
            click(app.modal_canvas,"Reawaken · keep 3/3 talismans")
            app.select_legacy(0)
            click(app.modal_canvas,"Reawaken with this memory")
            assert app.economy.state.talismans==[0,2,4],(app.economy.state.talismans,app.retain,app.economy.reward(),app.modal)
            assert app.economy.state.charms==[]
            assert app.store.load()[0].talismans==[0,2,4]
            app.return_to_slots()
            shot("34-minimum-slots")
            app.name_slot(2,False)
            entry=next(w for w in app.modal.winfo_children() if isinstance(w,tk.Entry))
            entry.delete(0,"end")
            entry.insert(0,"Renamed Garden")
            click(app.modal_canvas,"Save name")
            assert slots.store(2).load()[0].sanctuary_name=="Renamed Garden"
            app.delete_slot(3)
            click(app.modal_canvas,"Keep sanctuary")
            assert slots.occupied(3)
            app.delete_slot(3)
            click(app.modal_canvas,"Delete sanctuary")
            assert not slots.occupied(3)
            assert slots.occupied(1) and slots.occupied(2)
            # The four grounded footprints must fit inside the terrace diamond.
            def inside(x,y):
                polygon=((95,676),(500,547),(910,681),(500,883))
                signs=[]
                for (ax,ay),(bx,by) in zip(polygon,polygon[1:]+polygon[:1]):
                    signs.append((bx-ax)*(y-ay)-(by-ay)*(x-ax))
                return all(v>=0 for v in signs) or all(v<=0 for v in signs)
            for (x,y),(rx,ry) in zip(SCENE_ANCHORS[:4],SCENE_FOOTPRINTS[:4]):
                for dx,dy in ((-rx,0),(rx,0),(0,-ry/2),(0,ry)):
                    assert inside(x+dx,y+dy),(x+dx,y+dy)
            assert not errors,errors
            print("Expansion UI passed: three slots, naming, tutorial, tome previews, rack, star clicks, binding, retention, failed-save switching, independent progress, minimum-size layouts and grounded footprints.")
        finally:
            app.destroy()


def verify_workshop(output=None):
    from main import Deliveries, MusicPlayer, State
    import json
    import math
    import wave
    with tempfile.TemporaryDirectory() as temp:
        root=tk.Tk()
        errors=[]
        root.report_callback_exception=lambda kind,value,trace:errors.append(value)
        app=AtelierApp(root,SaveStore(Path(temp)/"save.json"),start_loop=False,show_welcome=False)
        def shot(name):
            root.update()
            app.layout()
            root.update()
            assert not errors,errors
            if output:
                capture(app.modal or app.tome_window or root,Path(output)/f"{name}.png")
        try:
            root.update()
            assert root.attributes("-fullscreen")
            s=app.economy.state
            s.resources=[1e7]*5
            s.owned=[35,100,15,4,1]
            s.research=[2]*5
            s.run_mana=1e6
            s.run_dust=120
            app.guide.update()
            app.set_tab("Workshop")
            app.set_crafting_section("Home")
            s.spirit_remaining=7.5
            shot("40-fullscreen-workshop-moth")
            # Fullscreen Escape closes Settings before leaving fullscreen.
            app.open_settings()
            shot("41-fullscreen-settings")
            app.escape()
            assert not app.settings_open and root.attributes("-fullscreen")
            app.escape()
            root.update()
            assert not root.attributes("-fullscreen")
            root.focus_force()
            root.event_generate("<F11>")
            root.update()
            assert root.attributes("-fullscreen")
            root.event_generate("<F11>")
            root.update()
            assert not root.attributes("-fullscreen")
            root.geometry("1100x720")
            root.update()
            app.layout()
            for stage in range(4):
                s.research=[stage]*5
                app.anim_time=stage+.25
                shot(f"42-stage-{stage}")
            s.research=[2]*5
            app.set_crafting_section("Enchantments")
            shot("43-minimum-spell-tree")
            app.set_crafting_section("Charms")
            app.set_recipe(tier=4,mode="both",long=True)
            app.toggle_infusion()
            app.panel.yview_moveto(.2)
            shot("44-minimum-charm-recipe")
            app.crafting_action("craft",0)
            app.crafting_action("equip",0)
            app.economy.advance(100)
            app.set_crafting_section("Infusion & Recharge")
            shot("45-minimum-recharge")
            app.workshop_change(lambda:app.crafting.recharge(0))
            assert app.crafting.charm(0)["recharges"]==1
            for i in range(5):
                app.crafting.restore(i)
            app.set_crafting_section("Restoration")
            shot("46-minimum-construction")
            s.spell_ranks["Deliveries"]=[3,3,3,1]
            Deliveries(app.economy).generate()
            assert s.contracts
            app.set_crafting_section("Deliveries")
            shot("47-minimum-deliveries")
            s.spirit_remaining=.1
            app.panel.yview_moveto(.27)
            shot("47b-delivery-reward-and-payment")
            for item in app.scene.find_withtag("visitor"):
                box=app.scene.bbox(item)
                assert box[0]>=0 and box[2]<=app.scene_width,box
            app.open_tome("deliveries")
            shot("48-delivery-tome")
            app.escape()
            app.preferences.values["reduced_motion"]=True
            s.spirit_remaining=7.5
            app.draw_scene()
            visitor=app.scene.find_withtag("visitor")
            assert visitor
            image=next(i for i in visitor if app.scene.type(i)=="image")
            x,y=app.scene.coords(image)
            app.scene.event_generate("<Motion>",x=int(x),y=int(y))
            app.scene.event_generate("<Button-1>",x=int(x),y=int(y))
            app.scene.event_generate("<ButtonRelease-1>",x=int(x),y=int(y))
            root.update()
            assert s.spirit_offer
            shot("49-celestial-choice")
            app.dismiss(force=True)
            app.encounters.choose(0)
            assert s.blessing
            app.open_settings()
            app.panel.yview_moveto(.42)
            shot("50-minimum-audio-settings")
            app.panel.yview_moveto(1)
            shot("51-minimum-music-help")
            # Real streamed playback through the installed mixer and actual device.
            audio=Path(temp)/"music"
            audio.mkdir()
            with wave.open(str(audio/"fixture.wav"),"wb") as wav:
                wav.setparams((1,2,22050,0,"NONE","not compressed"))
                wav.writeframes(b"".join(struct.pack("<h",int(2500*math.sin(2*math.pi*220*i/22050))) for i in range(22050)))
            (audio/"playlist.json").write_text(json.dumps({"tracks":["fixture.wav"]}))
            music=MusicPlayer(audio,app.preferences)
            try:
                assert music.playing,music.status
                assert music.backend.music.get_busy()
                music.pause()
                assert music.paused
                music.pause()
                music.next()
                assert music.backend.music.get_busy()
                print("Actual music playback passed through pygame-ce mixer.")
            finally:
                music.close()
            assert not errors,errors
            app.close_settings()
            callbacks=len(app.scene._tclCommands)
            for frame in range(60):
                app.anim_time=frame/30
                app.draw_scene()
            assert len(app.scene._tclCommands)==callbacks
            app.save()
            assert app.store.load()[0].contracts==s.contracts
            from main import Preferences
            assert not Preferences(Path(temp)/"settings.json").values["fullscreen"]
            print("Workshop UI passed: fullscreen, minimum layout, settings, four stages, moth click, reduced motion, tree, recipes, recharging, construction, deliveries and tome.")
        finally:
            app.destroy()


def verify_branching(output=None):
    from main import SpellTree
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as temp:
        root=tk.Tk()
        root.maxsize(2200,1400)
        errors=[]
        root.report_callback_exception=lambda kind,value,trace:errors.append((value,trace))
        app=AtelierApp(root,SaveStore(Path(temp)/"branch.json"),start_loop=False,show_welcome=False,apply_preferences=False)
        def flush():
            root.update()
            app.layout()
            root.update()
            assert not errors,errors
        def shot(name,surface=None):
            flush()
            if output:capture(surface or app.tree_window or app.modal or root,Path(output)/f"{name}.png")
        def click(c,entry):
            x,y,x2,y2=entry["rect"]
            x,y=(x+x2)/2-c.canvasx(0),(y+y2)/2-c.canvasy(0)
            c.event_generate("<Motion>",x=int(x),y=int(y))
            c.event_generate("<ButtonPress-1>",x=int(x),y=int(y))
            c.event_generate("<ButtonRelease-1>",x=int(x),y=int(y))
            root.update()
        try:
            root.geometry("1440x900")
            s=app.economy.state
            s.owned=[35,100,15,4,1];s.research=[2]*5;s.resources=[1e7]*5;s.run_mana=1e6
            s.tutorial_skipped=True
            flush()
            shot("60-parchment-main-window",root)
            app.open_tree()
            shot("61-tree-overview")
            assert len(app.tree_boxes)==18
            before=s.resources[:]
            box=app.tree_boxes[("Sanctuary",0)]
            x,y=(box[0]+box[2])/2,(box[1]+box[3])/2
            app.tree_press(SimpleNamespace(x=x,y=y))
            app.tree_drag(SimpleNamespace(x=x+10,y=y))
            app.tree_release(SimpleNamespace(x=x,y=y))
            assert app.tree_selected==("Charmcraft",0)
            app.tree_press(SimpleNamespace(x=x,y=y))
            app.tree_release(SimpleNamespace(x=x,y=y))
            assert app.tree_selected==("Sanctuary",0)
            assert s.resources==before
            old=app.tree_view[:]
            app.tree_press(SimpleNamespace(x=3,y=3))
            app.tree_drag(SimpleNamespace(x=80,y=45))
            app.tree_release(SimpleNamespace(x=80,y=45))
            assert app.tree_view[1]!=old[1]
            app.tree_zoom(2)
            app.centre_tree()
            shot("62-tree-zoomed-detail")
            price=SpellTree(app.economy).price("Sanctuary",0)
            button=next(e for e in app.tree_detail.controls.entries if e["label"]=="Purchase inscription")
            click(app.tree_detail,button)
            assert s.spell_ranks["Sanctuary"][0]==1,errors
            assert before[1]-price[1]<=s.resources[1]<before[1],(s.resources,before,price)
            saved_view=app.tree_view[:]
            app.close_tree();app.open_tree()
            assert saved_view==app.tree_view
            app.open_tome("enchantments")
            assert app.tree_window is None and app.tome_window
            shot("63-parchment-tome",app.tome_window)
            app.open_tree()
            assert app.tome_window is None
            # A click on the underlying purchase button closes the tree only.
            old_owned=s.owned[:]
            app.background.event_generate("<ButtonPress-1>",x=30,y=80)
            app.background.event_generate("<ButtonRelease-1>",x=30,y=80)
            root.update()
            assert not app.tree_window
            assert s.owned==old_owned
            app.set_tab("Production");app.panel.yview_moveto(0);app.draw_ui()
            entry=next(e for e in app.panel.controls.entries if e["label"].startswith("Buy 1"))
            x,y,x2,y2=entry["rect"];x,y=(x+x2)/2,(y+y2)/2
            c=app.panel
            c.event_generate("<ButtonPress-1>",x=int(x),y=int(y))
            pressed=c.coords(entry["items"][1])
            assert pressed[1]==entry["rect"][1]+2
            app.draw_ui()  # A replacement of Canvas items must keep pressed state.
            assert c.controls.pressed
            c.event_generate("<ButtonRelease-1>",x=1,y=1)
            assert s.owned==old_owned
            entry=next(e for e in c.controls.entries if e["label"].startswith("Buy 1"))
            click(c,entry)
            assert s.owned[0]==old_owned[0]+1
            # Keyboard activation uses the same action.
            c.focus_set();c.controls.focus=next(e["key"] for e in c.controls.entries if e["label"].startswith("Buy 1"))
            c.controls.activate(None)
            assert s.owned[0]==old_owned[0]+2
            # Safe outside cancellation cannot take the dangerous cancel callback.
            calls=[]
            app.dialog("Unsaved journal","Retry saving before closing.","Retry",cancel="Close without saving",on_cancel=lambda:calls.append("discard"))
            shot("64-parchment-dialog",app.modal)
            app.background.event_generate("<ButtonPress-1>",x=20,y=80)
            app.background.event_generate("<ButtonRelease-1>",x=20,y=80)
            root.update()
            assert app.modal is None and not calls
            s.spirit_offer=[dict(target=0,percent=20),dict(target=1,percent=30)]
            app.show_spirit_offer();app.escape()
            assert s.spirit_offer
            for i in range(6):
                app.cursor_on(app.scene,i)
                assert str(app.scene.cget("cursor")).endswith(f"celestial-{i}.cur"),app.scene.cget("cursor")
            app.preferences.values["celestial_cursor"]=False
            app.cursor_on(app.scene)
            assert app.scene.cget("cursor")=="arrow"
            app.preferences.values["celestial_cursor"]=True
            frame=app.frames[root]
            frame.maximise();root.update();assert root.state()=="zoomed"
            frame.maximise();root.update();assert root.state()=="normal"
            root.iconify();root.update();assert root.state()=="iconic"
            root.deiconify();root.update()
            root.geometry("1100x720");flush()
            app.open_tree();app.fit_tree()
            shot("65-minimum-tree")
            app.preferences.values["reduced_motion"]=True
            app.tree_selected=("Charmcraft",4);app.draw_tree();app.draw_tree_detail()
            shot("66-advanced-node-detail")
            app.close_tree();app.open_settings();app.panel.yview_moveto(1)
            shot("67-cursor-settings",root)
            app.close_settings()
            app.set_tab("Workshop");app.set_crafting_section("Restoration")
            for i in range(5):
                for _ in range(i+1):app.crafting.restore(i)
            shot("68-construction-levels",root)
            assert s.restoration_levels[:4]==[1,2,3,4]
            # Upgrades paid at fixed levels are visible and show the next price.
            app.panel.yview_moveto(.65)
            shot("69-late-construction-costs",root)
            s.run_dust=s.rebirth_goal
            app.confirm_prestige()
            app.show_legacy_choice(True)
            app.select_legacy(0)
            shot("70-legacy-bonus-choice",app.modal)
            app.dismiss(force=True)
            assert s.legacies==[0]*6
            assert not errors,errors
            print("Branching UI passed: graph pan/zoom/selection, purchase, state retention, window switching, safe outside dismissal, press/release/cancel, keyboard activation, six cursors, maximise and minimise.")
        finally:app.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture")
    parser.add_argument("--workshop-only",action="store_true")
    parser.add_argument("--branching-only",action="store_true")
    args=parser.parse_args()
    if not args.workshop_only and not args.branching_only:
        verify(args.capture)
        verify_expansion(args.capture)
    if not args.branching_only:verify_workshop(args.capture)
    verify_branching(args.capture)
