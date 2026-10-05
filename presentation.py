"""Parchment window chrome, native cursors and persistent Canvas controls."""
from pathlib import Path
import os
import struct
import tkinter as tk
from PIL import Image, ImageDraw

PAPER, INK, GOLD, BURGUNDY, LIGHT = "#ecddbb", "#3f3027", "#ad8950", "#743c40", "#f7edda"


class WindowFrame:
    """Keep a managed Win32 window; replace only its non-client presentation."""
    def __init__(self,app,window,title,close,main=False):
        self.app,self.window,self.main,self.close=app,window,main,close
        self.native=None
        self.resizable=False
        window.resizable(False,False)
        self.bar=tk.Canvas(window,height=32,bg=PAPER,highlightthickness=0,takefocus=False)
        self.title=title
        self.bar.bind("<Configure>",self.draw)
        self.bar.bind("<ButtonPress-1>",self.press)
        self.bar.bind("<ButtonRelease-1>",self.release)
        self.bar.bind("<Motion>",self.hover)
        self.bar.bind("<Leave>",lambda e:self.draw())
        self.action=None
        self.origin=None
        if main:
            self.update_visibility()
        else:
            self.bar.place(x=0,y=0,relwidth=1,height=32)
        window.update_idletasks()
        if os.name=="nt":
            self.install_native()
        elif not main:
            window.overrideredirect(True)
        self.centre()
        self.draw()

    def install_native(self):
        import ctypes as ct
        from ctypes import wintypes as wt
        user=ct.windll.user32
        user.GetParent.argtypes=[wt.HWND]
        user.GetParent.restype=wt.HWND
        hwnd=user.GetParent(self.window.winfo_id())
        get=user.GetWindowLongPtrW
        put=user.SetWindowLongPtrW
        get.argtypes=[wt.HWND,ct.c_int];get.restype=ct.c_ssize_t
        put.argtypes=[wt.HWND,ct.c_int,ct.c_ssize_t];put.restype=ct.c_ssize_t
        call=user.CallWindowProcW
        call.argtypes=[ct.c_void_p,wt.HWND,wt.UINT,wt.WPARAM,wt.LPARAM]
        call.restype=ct.c_ssize_t
        user.GetWindowRect.argtypes=[wt.HWND,ct.POINTER(wt.RECT)]
        user.SetWindowPos.argtypes=[wt.HWND,wt.HWND,ct.c_int,ct.c_int,ct.c_int,ct.c_int,wt.UINT]
        previous=get(hwnd,-4)
        put(hwnd,-16,get(hwnd,-16) & ~0x00C50000)
        proc_type=ct.WINFUNCTYPE(ct.c_ssize_t,wt.HWND,wt.UINT,wt.WPARAM,wt.LPARAM)
        @proc_type
        def procedure(handle,message,wparam,lparam):
            if message==0x83 and wparam:  # WM_NCCALCSIZE: the client draws the frame.
                return 0
            if message==0x84:  # Client only: no native resizing or dragging.
                return 1
            if message==0x112 and (wparam & 0xfff0) in (0xf000,0xf010,0xf030):
                return 0  # Block system size, move and maximise commands.
            return call(previous,handle,message,wparam,lparam)
        self.native=(user,hwnd,put,previous,procedure)
        put(hwnd,-4,ct.cast(procedure,ct.c_void_p).value)
        # Keep standard managed/taskbar styles. Suppress the system-drawn caption
        # via NCCALCSIZE rather than using overrideredirect on the main window.
        user.SetWindowPos(hwnd,None,0,0,0,0,0x37)

    def dispose(self):
        if self.native:
            user,hwnd,put,previous,procedure=self.native
            put(hwnd,-4,previous)
            self.native=None

    def update_visibility(self):
        if self.main:
            if self.window.attributes("-fullscreen"):
                self.bar.pack_forget()
            else:
                self.bar.pack(side="top",fill="x",before=self.app.background)
            if self.native:
                user,hwnd,put,previous,procedure=self.native
                get=user.GetWindowLongPtrW
                put(hwnd,-16,get(hwnd,-16) & ~0x00C50000)
                user.SetWindowPos(hwnd,None,0,0,0,0,0x37)

    def regions(self):
        w=self.bar.winfo_width()
        return [(w-42,"×",self.close)]+([(w-84,"—",self.window.iconify)] if self.main else [])

    def draw(self,event=None,hover=None):
        c=self.bar;w=max(1,c.winfo_width())
        c.delete("all")
        c.create_rectangle(0,0,w,32,fill=PAPER,outline=GOLD)
        c.create_line(1,2,w-1,2,fill=LIGHT)
        c.create_text(15,16,text=self.title,anchor="w",fill=INK,font=("Georgia",10))
        for x,label,callback in self.regions():
            c.create_rectangle(x,3,x+36,29,fill=BURGUNDY if self.action==x else LIGHT if hover==x else PAPER,outline=GOLD)
            c.create_text(x+18,16,text=label,fill=LIGHT if self.action==x else INK,font=("Segoe UI",13))

    def press(self,event):
        self.origin=(event.x_root,event.y_root,self.window.winfo_x(),self.window.winfo_y())
        self.action=next((x for x,_,_ in self.regions() if x<=event.x<=x+36),None)
        self.draw()

    def drag(self,event):
        return "break"

    def release(self,event):
        selected=self.action
        self.action=None;self.origin=None
        self.draw()
        for x,_,callback in self.regions():
            if selected==x and x<=event.x<=x+36 and 0<=event.y<=32:
                callback()
                return

    def hover(self,event):
        self.draw(hover=next((x for x,_,_ in self.regions() if x<=event.x<=x+36),None))

    def double(self,event):
        return "break"

    def maximise(self):
        return "break"

    def centre(self):
        self.window.update_idletasks()
        if not self.window.attributes("-fullscreen"):
            x=max(0,(self.window.winfo_screenwidth()-self.window.winfo_width())//2)
            y=max(0,(self.window.winfo_screenheight()-self.window.winfo_height())//2)
            self.window.geometry(f"+{x}+{y}")


class CursorSet:
    def __init__(self,directory):
        self.paths={}
        if os.name!="nt":return
        try:
            directory=Path(directory)/"cursors-v1"
            directory.mkdir(parents=True,exist_ok=True)
            for kind in range(6):
                path=directory/f"celestial-{kind}.cur"
                if not path.exists():self.generate(path,kind)
                self.paths[kind]="@"+path.as_posix()
        except OSError:
            self.paths={}

    @staticmethod
    def generate(path,kind):
        image=Image.new("RGBA",(128,128))
        d=ImageDraw.Draw(image)
        d.polygon((8,8,8,91,29,70,46,108,61,101,43,65,76,62),fill="#fff4d7",outline="#493650",width=5)
        if kind==0 or kind==5:
            d.polygon((92,25,99,45,119,52,99,59,92,80,85,59,65,52,85,45),fill="#c8aaf3",outline="#796198",width=3)
        elif kind==1:
            d.polygon((91,27,74,58,73,71,83,80,100,80,110,69,108,57),fill="#a6e4df",outline="#497b87",width=3)
        elif kind==2:
            d.polygon((92,22,112,47,106,79,83,88,71,58),fill="#c8b4ef",outline="#766494",width=3)
            d.line((92,22,94,78,83,88),fill="#fff4ec",width=3)
        else:
            d.polygon((82,27,100,27,100,47,115,75,109,85,73,85,67,75,82,47),fill="#e8efe4",outline="#73638a",width=3)
            d.rectangle((78,60,105,77),fill="#9adcd6" if kind==3 else "#e7b89b")
        image=image.resize((32,32),Image.Resampling.LANCZOS)
        # CUR: 32-bit BGRA DIB with an explicit AND mask and a (2,2) hotspot.
        pixels=image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes("raw","BGRA")
        mask=bytearray()
        for y in reversed(range(32)):
            row=0
            for x in range(32):row=(row<<1)|(image.getpixel((x,y))[3]==0)
            mask.extend(int(row).to_bytes(4,"big"))
        dib=struct.pack("<IiiHHIIiiII",40,32,64,1,32,0,len(pixels),0,0,0,0)+pixels+mask
        path.write_bytes(struct.pack("<HHH",0,2,1)+struct.pack("<BBBBHHII",32,32,0,0,2,2,len(dib),22)+dib)

    def apply(self,widget,enabled=True,kind=0):
        try:widget.configure(cursor=self.paths.get(kind,"arrow") if enabled else "arrow")
        except tk.TclError:widget.configure(cursor="arrow")


class CanvasButtons:
    """Stable press/release state, independent of Canvas item replacement."""
    def __init__(self,app,canvas):
        self.app,self.canvas=app,canvas
        self.entries=[]
        self.pressed=None
        self.focus=None
        self.hovered=None
        self.flash_rect=None
        self.flash_timer=None
        canvas.configure(takefocus=True)
        canvas.bind("<ButtonPress-1>",self.press)
        canvas.bind("<ButtonRelease-1>",self.release)
        canvas.bind("<Motion>",self.motion)
        canvas.bind("<Leave>",self.leave)
        canvas.bind("<Tab>",self.tab)
        canvas.bind("<Shift-Tab>",lambda e:self.tab(e,-1))
        canvas.bind("<Return>",self.activate)
        canvas.bind("<space>",self.activate)
        canvas.bind("<FocusOut>",lambda e:self.paint())

    def clear(self):
        self.entries=[]

    def add(self,rect,label,callback,enabled,primary,tip,items):
        key=(tuple(rect),label)
        self.entries.append(dict(key=key,rect=rect,label=label,callback=callback,enabled=enabled,primary=primary,tip=tip,items=items))
        self.paint()

    def hit(self,event):
        x,y=self.canvas.canvasx(event.x),self.canvas.canvasy(event.y)
        return next((e for e in reversed(self.entries) if e["rect"][0]<=x<=e["rect"][2] and e["rect"][1]<=y<=e["rect"][3]),None)

    def paint(self):
        c=self.canvas
        for e in self.entries:
            shadow,face,label=e["items"]
            if not c.type(face):continue
            key=e["key"];down=key==self.pressed;hot=key==self.hovered
            x,y,x2,y2=e["rect"]
            offset=2 if down and not self.app.reduced_motion else 0
            c.coords(face,x,y+offset,x2,y2+offset)
            c.coords(label,(x+x2)/2,(y+y2)/2+offset)
            bg=BURGUNDY if e["primary"] and e["enabled"] else LIGHT if e["enabled"] else "#ded0b5"
            if e["enabled"] and (hot or down):bg="#885156" if e["primary"] else "#fff4dc" if hot else "#dac397"
            c.itemconfigure(face,fill=bg,outline="#c59a3f" if hot or key==self.focus else GOLD,width=2 if hot or key==self.focus else 1)
            c.itemconfigure(shadow,state="hidden" if down else "normal")
        c.delete("purchase-flash")
        if self.flash_rect:
            x,y,x2,y2=self.flash_rect
            c.create_rectangle(x-2,y-2,x2+2,y2+2,outline="#69a695",width=3,tags="purchase-flash")

    def press(self,event):
        self.canvas.focus_set()
        entry=self.hit(event)
        if entry and entry["enabled"]:
            self.pressed=self.focus=entry["key"]
            self.paint()
        return "break"

    def release(self,event):
        key=self.pressed;self.pressed=None
        entry=self.hit(event)
        self.paint()
        if entry and entry["enabled"] and entry["key"]==key:
            before=self.app.feedback_until
            entry["callback"]()
            if self.app.feedback_until!=before and not self.app.reduced_motion and self.canvas.winfo_exists():
                self.flash_rect=entry["rect"]
                if self.flash_timer:self.canvas.after_cancel(self.flash_timer)
                self.flash_timer=self.canvas.after(350,self.end_flash)
                self.paint()
        return "break"

    def end_flash(self):
        self.flash_timer=None
        self.flash_rect=None
        if self.canvas.winfo_exists():self.paint()

    def dispose(self):
        if self.flash_timer:
            self.canvas.after_cancel(self.flash_timer)
            self.flash_timer=None

    def motion(self,event):
        entry=self.hit(event)
        key=entry["key"] if entry else None
        if key!=self.hovered:
            self.hovered=key;self.paint()
        self.app.cursor_on(self.canvas)
        if entry and entry["tip"]:self.app.tooltip.show(entry["tip"],event)
        else:self.app.tooltip.hide()

    def leave(self,event):
        self.hovered=None;self.paint();self.app.tooltip.hide()

    def tab(self,event,direction=1):
        keys=[e["key"] for e in self.entries if e["enabled"]]
        if not keys:return
        index=keys.index(self.focus) if self.focus in keys else (-1 if direction==1 else 0)
        self.focus=keys[(index+direction)%len(keys)]
        self.paint()
        return "break"

    def activate(self,event):
        entry=next((e for e in self.entries if e["key"]==self.focus and e["enabled"]),None)
        if entry:entry["callback"]()
        return "break"
