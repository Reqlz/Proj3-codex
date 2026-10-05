"""Pannable spell graph presentation; all purchases use the app's economy."""
import math
import time
import tkinter as tk
from presentation import PAPER, LIGHT, INK, GOLD, BURGUNDY

TEAL,MUTED="#246b66","#79654d"
BRANCHES=("Charmcraft","Deliveries","Sanctuary")
ICONS={"Charmcraft":("◇","⌛","✦","☾","⚗","◆"),"Deliveries":("✉","▣","◷","✧","✚","▤"),"Sanctuary":("⚒","☼","⇄","☀","✥","⟳")}


class SpellGraph:
    def close_tree(self):
        if self.tree_window:
            self.tooltip.hide()
            win=self.tree_window
            self.tree_window=None
            self.destroy_window(win)

    def open_tree(self):
        if self.in_menu or not self.economy.state.owned[2]:return
        self.close_tome()
        self.guide.read("enchantments")
        self.save()
        if self.tree_window:
            self.tree_window.lift()
            return
        win=tk.Toplevel(self.root)
        self.tree_window=win
        win.title("The branching spell tree")
        win.transient(self.root)
        width=min(1120,self.root.winfo_screenwidth()-30)
        height=min(720,self.root.winfo_screenheight()-60)
        win.geometry(f"{width}x{height}+{max(0,(self.root.winfo_screenwidth()-width)//2)}+30")
        win.minsize(850,580)
        win.configure(bg="#101727")
        self.tree_toolbar=tk.Canvas(win,bg=PAPER,highlightthickness=0,height=48)
        self.tree_toolbar.place(x=0,y=33,relwidth=1,height=48)
        self.tree_canvas=tk.Canvas(win,bg="#101727",highlightthickness=0)
        self.tree_canvas.place(x=10,y=84,relwidth=1,width=-344,relheight=1,height=-94)
        self.tree_detail=tk.Canvas(win,bg=LIGHT,highlightthickness=1,highlightbackground=GOLD)
        self.tree_detail.place(relx=1,x=-326,y=84,width=304,relheight=1,height=-94)
        self.tree_scroll=tk.Scrollbar(win,command=self.tree_detail.yview)
        self.tree_scroll.place(relx=1,x=-20,y=84,width=12,relheight=1,height=-94)
        self.tree_detail.configure(yscrollcommand=self.tree_scroll.set)
        self.tree_detail.bind("<MouseWheel>",lambda e:self.tree_detail.yview_scroll(-int(e.delta/120),"units"))
        self.tree_canvas.bind("<ButtonPress-1>",self.tree_press)
        self.tree_canvas.bind("<B1-Motion>",self.tree_drag)
        self.tree_canvas.bind("<ButtonRelease-1>",self.tree_release)
        self.tree_canvas.bind("<MouseWheel>",lambda e:self.tree_zoom(1.15 if e.delta>0 else 1/1.15,e.x,e.y))
        self.tree_canvas.bind("<Configure>",lambda e:self.draw_tree())
        self.tree_canvas.bind("<Motion>",self.tree_hover)
        self.tree_canvas.bind("<Leave>",lambda e:self.tooltip.hide())
        win.bind("<Escape>",lambda e:self.close_tree())
        win.bind("<F11>",lambda e:self.toggle_fullscreen())
        win.protocol("WM_DELETE_WINDOW",self.close_tree)
        self.tree_gesture=None
        self.frame_window(win,"The branching spell tree",self.close_tree)
        win.update()
        if not getattr(self,"tree_seen",False):
            self.fit_tree()
            self.tree_seen=True
        self.draw_tree()
        self.draw_tree_detail()

    @staticmethod
    def tree_position(branch,node):
        radius={0:185,1:365,2:365,4:540,5:540,3:710}[node]
        offset=-23 if node in (1,4) else 23 if node in (2,5) else 0
        angle=math.radians((-90,30,150)[BRANCHES.index(branch)]+offset)
        return 800+radius*math.cos(angle),800+radius*math.sin(angle)

    def fit_tree(self):
        if not self.tree_window:return
        w,h=self.tree_canvas.winfo_width(),self.tree_canvas.winfo_height()
        scale=max(.25,min(1.6,(w-50)/1540,(h-50)/1540))
        self.tree_view=[scale,w/2-800*scale,h/2-800*scale]
        self.draw_tree()

    def centre_tree(self):
        x,y=self.tree_position(*self.tree_selected)
        scale=self.tree_view[0]
        self.tree_view[1:]=[self.tree_canvas.winfo_width()/2-x*scale,self.tree_canvas.winfo_height()/2-y*scale]
        self.draw_tree()

    def tree_zoom(self,factor,x=None,y=None):
        if not self.tree_window:return
        c=self.tree_canvas
        x=c.winfo_width()/2 if x is None else x
        y=c.winfo_height()/2 if y is None else y
        scale,ox,oy=self.tree_view
        new=max(.25,min(1.6,scale*factor))
        self.tree_view=[new,x-(x-ox)*new/scale,y-(y-oy)*new/scale]
        self.draw_tree()

    def tree_press(self,event):
        self.tooltip.hide()
        hit=next((key for key,box in self.tree_boxes.items() if box[0]<=event.x<=box[2] and box[1]<=event.y<=box[3]),None)
        self.tree_gesture=(event.x,event.y,self.tree_view[1],self.tree_view[2],hit,0.)

    def tree_drag(self,event):
        if not self.tree_gesture:return
        x,y,ox,oy,hit,moved=self.tree_gesture
        moved=max(moved,math.hypot(event.x-x,event.y-y))
        self.tree_gesture=(x,y,ox,oy,hit,moved)
        if hit is None:
            self.tree_view[1:]=[ox+event.x-x,oy+event.y-y]
            self.draw_tree()

    def tree_release(self,event):
        if not self.tree_gesture:return
        x,y,ox,oy,hit,moved=self.tree_gesture
        self.tree_gesture=None
        if hit and max(moved,math.hypot(event.x-x,event.y-y))<5:
            self.tree_selected=hit
            self.tree_detail.yview_moveto(0)
            self.draw_tree()
            self.draw_tree_detail()

    def tree_hover(self,event):
        self.cursor_on(self.tree_canvas)
        hit=next((key for key,box in self.tree_boxes.items() if box[0]<=event.x<=box[2] and box[1]<=event.y<=box[3]),None)
        if hit:
            tree=self.spell_tree()
            self.tooltip.show(tree.name(*hit)+" · "+hit[0]+"\n"+(tree.unlock_reason(*hit) or "Select to inspect this star's inscription."),event)
        else:self.tooltip.hide()

    def draw_tree(self):
        if not self.tree_window:return
        c=self.tree_canvas
        c.delete("all")
        scale,ox,oy=self.tree_view
        w,h=c.winfo_width(),c.winfo_height()
        if w<24 or h<24:return
        c.paper=self.art.astral(max(1,w),max(1,h))
        c.create_image(0,0,image=c.paper,anchor="nw")
        tree=self.spell_tree()
        self.tree_boxes={}
        hubx,huby=800*scale+ox,800*scale+oy
        c.create_oval(hubx-30,huby-30,hubx+30,huby+30,fill="#27304b",outline="#b9a4db",width=2)
        c.create_text(hubx,huby,text="✧",fill="#f6de9e",font=("Segoe UI Symbol",32))
        for branch in BRANCHES:
            for node in range(6):
                x,y=self.tree_position(branch,node)
                sources=[(self.tree_position(branch,parent),tree.rank(branch,parent)>=required) for parent,required in tree.prerequisites(node)]
                if node==0:sources=[((800,800),True)]
                for (px,py),complete in sources:
                    c.create_line(px*scale+ox,py*scale+oy,x*scale+ox,y*scale+oy,fill="#88adbd" if complete else "#46536f",width=2 if complete else 1)
                    for fraction in (.3,.65):
                        xx=(px+(x-px)*fraction)*scale+ox
                        yy=(py+(y-py)*fraction)*scale+oy
                        c.create_oval(xx-2,yy-2,xx+2,yy+2,fill="#b0b5d3" if complete else "#64708d",outline="")
            for node in range(6):
                x,y=self.tree_position(branch,node)
                cx,cy=x*scale+ox,y*scale+oy
                radius=max(23,39*scale)
                box=(cx-radius,cy-radius,cx+radius,cy+radius)
                self.tree_boxes[(branch,node)]=box
                rank=tree.rank(branch,node)
                available=tree.available(branch,node)
                full=rank==tree.maximum(node)
                affordable=available and self.tree_affordable(tree.price(branch,node))
                selected=self.tree_selected==(branch,node)
                colour="#efd596" if full else "#a8dfd5" if affordable else "#a6afd3" if available or rank else "#68718b"
                if selected or full or affordable:
                    c.create_oval(cx-radius-5,cy-radius-5,cx+radius+5,cy+radius+5,fill="#263c4b" if affordable else "#353349",outline="#eee0b8" if selected else "#424e69",width=2 if selected else 1)
                c.create_oval(*box,fill="#403c56" if full else "#1d293d",outline=colour,width=2)
                multi=tree.maximum(node)>1
                c.create_text(cx,cy-(6 if multi else 0),text=ICONS[branch][node],fill=colour,font=("Segoe UI Symbol",max(17,int(25*scale))))
                if multi:c.create_text(cx,cy+radius*.52,text=f"{rank}/{tree.maximum(node)}",fill="#e5e0d8",font=("Segoe UI",9))
                if not available and not rank:
                    c.create_text(cx+radius*.75,cy-radius*.75,text="×",fill="#9a9eb5",font=("Segoe UI",10))
                elif full:
                    c.create_text(cx+radius*.75,cy-radius*.75,text="✓",fill="#f2d48d",font=("Segoe UI",10))
        bar=self.tree_toolbar
        self.clear_page(bar)
        self.button(bar,12,6,90,29,"Fit tree",self.fit_tree)
        self.button(bar,111,6,138,29,"Centre selected",self.centre_tree)
        self.button(bar,259,6,40,29,"−",lambda:self.tree_zoom(1/1.15))
        self.button(bar,307,6,40,29,"+",lambda:self.tree_zoom(1.15))
        self.text(bar,361,13,f"{scale:.0%} · Drag the sky to explore",10,MUTED)

    def tree_affordable(self,price):
        return all(have+1e-8>=need for have,need in zip(self.economy.state.resources,price))

    def draw_tree_detail(self):
        if not self.tree_window:return
        c=self.tree_detail
        if hasattr(c,"controls") and c.controls.pressed:return
        position=c.yview()[0]
        self.clear_page(c)
        tree=self.spell_tree()
        branch,node=self.tree_selected
        rank=tree.rank(branch,node)
        self.text(c,18,18,branch.upper(),10,MUTED)
        self.text(c,18,46,tree.name(branch,node),22,BURGUNDY,"Georgia",width=262)
        status="Complete" if rank==tree.maximum(node) else "Purchased" if rank else "Affordable" if tree.available(branch,node) and self.tree_affordable(tree.price(branch,node)) else "Available" if tree.available(branch,node) else "Locked"
        self.text(c,18,111,f"Rank {rank}/{tree.maximum(node)} · {status}",11,MUTED)
        self.text(c,18,151,"CURRENT",10,MUTED)
        self.text(c,18,175,tree.effect(branch,node),12,TEAL,width=262)
        full=rank>=tree.maximum(node)
        self.text(c,18,238,"NEXT RANK",10,MUTED)
        self.text(c,18,262,"Fully inscribed" if full else tree.effect(branch,node,rank+1),12,BURGUNDY,width=262)
        requirements=[f"{tree.name(branch,parent)}: rank {need}" for parent,need in tree.prerequisites(node)]
        reason=tree.unlock_reason(branch,node)
        self.text(c,18,334,reason or "Requires: "+("; ".join(requirements) if requirements else "Own an Essence Distillery"),10,BURGUNDY if reason else MUTED,width=262)
        price=tree.price(branch,node)
        self.recipe_lines(c,18,410,price)
        self.button(c,18,520,262,36,"Fully learned" if full else "Activity not yet unlocked" if reason else "Purchase inscription",self.buy_tree_node,enabled=tree.available(branch,node) and self.tree_affordable(price),primary=True,tip=reason or None)
        self.text(c,18,577,"New charm effects apply at crafting. Courier effects apply to new offers. All skill ranks reset at Reawakening.",10,MUTED,width=262)
        if time.monotonic()<self.feedback_until:self.text(c,18,650,self.feedback_text,11,TEAL,width=262)
        c.configure(scrollregion=(0,0,300,710))
        c.yview_moveto(position)

    def buy_tree_node(self):
        self.sync_time()
        if self.spell_tree().buy(*self.tree_selected):
            self.feedback("Inscription learned: "+self.spell_tree().name(*self.tree_selected))
            self.save()
            self.draw_tree()
            self.draw_tree_detail()
