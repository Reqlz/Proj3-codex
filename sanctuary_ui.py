"""Physical sanctuary details and illustrated, plain-language information cards."""
import math
import tkinter as tk
from storage import capacities as storage_capacities, upgrade_price as storage_price, MAX_LEVELS
from sanctuary import MATERIAL_GUIDES, legacy_points, pedestal_ring
from astral_systems import RESOURCE_NAMES
from overhaul_ui import INK,MUTED,BURGUNDY,TEAL,GOLD,LIGHT,ICONS,price_text

class SanctuaryUI:
    def open_cabinet(self):
        self.tab="Workshop";self.crafting_section="Charms"
        self.panel.yview_moveto(0);self.draw_ui()

    def draw_cabinet(self,canvas,box,physical=False):
        x1,y1,x2,y2=box;s=self.economy.state
        width,height=x2-x1,y2-y1
        tag="cabinet" if physical else "cabinet-card"
        canvas.create_rectangle(x1,y1,x2,y2,fill="#654d41",outline=GOLD,width=2,tags=tag)
        canvas.create_line(x1+4,y1+height/2,x2-4,y1+height/2,fill="#b99a70",width=3,tags=tag)
        usable=(True,s.shelf_level>=1,s.shelf_level>=2,s.legacies[6]>=1,s.legacies[6]>=2,s.legacies[6]>=3)
        equipped=iter(ch for ch in s.charms if ch["equipped"])
        for j in range(6):
            left=x1+5+(j%3)*(width-10)/3
            top=y1+5+(j//3)*(height-10)/2
            cw,ch=(width-10)/3,(height-10)/2
            canvas.create_rectangle(left+2,top+2,left+cw-2,top+ch-3,fill="#f0dfba" if usable[j] else "#856c58",outline="#ac8d64",tags=tag)
            charm=next(equipped,None) if j<5 and usable[j] else None
            icon="✧" if j==5 and usable[j] else ICONS[charm["target"]] if charm else "·" if usable[j] else "×"
            canvas.create_text(left+cw/2,top+ch*.32,text=icon,fill=TEAL if j==5 and s.lantern_remaining else BURGUNDY if usable[j] else "#d0bfa0",font=("Segoe UI Symbol",12 if physical else 23),tags=tag)
            if not physical:
                label="Astral Lantern" if j==5 else RESOURCE_NAMES[charm["target"]] if charm else "Empty place" if usable[j] else "Shelf upgrade "+str(j) if j in (1,2) else "Cabinet legacy "+str(j-2)
                self.text(canvas,left+cw/2,top+ch*.62,label,8,INK if usable[j] else LIGHT,anchor="center",tags=tag)
                if charm:self.text(canvas,left+cw/2,top+ch*.83,f"{charm['remaining']/60:.1f}m · {charm['mode']}",8,MUTED,anchor="center",tags=tag)
                elif j==5:self.text(canvas,left+cw/2,top+ch*.83,"Lit" if s.lantern_remaining else "Legacy 3",8,MUTED,anchor="center",tags=tag)
        if physical:
            canvas.create_text((x1+x2)/2,y2+12,text="Astral Cabinet",fill="#e8d8b6",font=("Georgia",9),tags=tag)
        else:
            self.info_button(canvas,x2-28,y1-27,"Charm shelf","Start with one charm place. Build two shelf expansions each run. Cabinet legacies permanently add two more charm places, then the separate Lantern. Stored charms do not use places.")

    def draw_physical_cabinet(self,c,box):
        x,y,right,bottom=box;s=self.economy.state
        sx,sy=(right-x)/123,(bottom-y)/190
        def rect(a,b,d,e,**kw):return c.create_rectangle(x+a*sx,y+b*sy,x+d*sx,y+e*sy,tags="cabinet",**kw)
        def poly(points,**kw):return c.create_polygon(*[x+v*sx if j%2==0 else y+v*sy for j,v in enumerate(points)],tags="cabinet",**kw)
        c.create_oval(x-6*sx,y+167*sy,right+6*sx,y+186*sy,fill="#263d36",outline="",tags="cabinet")
        # Feet, right side, top plane, and recessed face sit on the meadow.
        rect(9,157,24,180,fill="#70503e",outline="#b49367")
        rect(88,157,103,180,fill="#70503e",outline="#b49367")
        poly((108,17,123,8,123,158,108,171),fill="#473a35",outline="#a38460")
        poly((0,17,15,8,123,8,108,17),fill="#b19368",outline="#dbc49a")
        rect(0,17,108,167,fill="#715542",outline="#c4a576",width=2)
        rect(8,28,100,153,fill="#332e36",outline="#bb9468")
        usable=(True,s.shelf_level>=1,s.shelf_level>=2,s.legacies[6]>=1,s.legacies[6]>=2,s.legacies[6]>=3)
        equipped=iter(ch for ch in s.charms if ch['equipped'])
        for j in range(6):
            left=11+(j%3)*30;top=31+(j//3)*61
            rect(left,top,left+26,top+52,fill="#52443d" if usable[j] else "#74604a",outline="#917451")
            charm=next(equipped,None) if j<5 and usable[j] else None
            icon="✧" if j==5 and usable[j] else ICONS[charm['target']] if charm else "·" if usable[j] else "×"
            if charm:
                c.create_line(x+(left+13)*sx,y+(top+4)*sy,x+(left+13)*sx,y+(top+15)*sy,fill=GOLD,tags="cabinet")
                c.create_oval(x+(left+5)*sx,y+(top+17)*sy,x+(left+21)*sx,y+(top+39)*sy,fill="#bda783",outline="#e0c695",tags="cabinet")
            c.create_text(x+(left+13)*sx,y+(top+28)*sy,text=icon,fill="#91dbce" if j==5 and s.lantern_remaining else "#ead7b4",font=("Segoe UI Symbol",max(8,round(12*sx))),tags="cabinet")
        for yy in (86,148):rect(5,yy,104,yy+6,fill="#b49469",outline="#d3b381")
        rect(-3,14,111,23,fill="#a2825b",outline="#d4b98b")
        rect(-2,158,110,167,fill="#997751",outline="#c9aa7b")
        c.create_text(x+55*sx,y+192*sy,text="Astral Cabinet",fill="#e8d8b6",font=("Georgia",9),tags="cabinet")

    def draw_storage_upgrades(self):
        c,w,s=self.panel,self.panel_width,self.economy.state
        limits=storage_capacities(s)
        for i,name in enumerate(RESOURCE_NAMES):
            y=1620+i*205;level=s.storage_levels[i];maximum=level>=MAX_LEVELS[i]
            recipe=storage_price(s,i)
            c.create_rectangle(12,y,w-14,y+190,fill=LIGHT,outline=GOLD)
            self.text(c,26,y+10,name+" storage",16,BURGUNDY,"Georgia")
            self.text(c,26,y+38,f"{s.resources[i]:,.0f} / {limits[i]:,.0f} · Upgrade {level}/{MAX_LEVELS[i]}",10,TEAL,width=w-52)
            self.text(c,26,y+67,"Maximum capacity for this run" if maximum else f"Next capacity: {limits[i]*2:,.0f} · Cost: "+price_text(recipe),10,INK,width=w-52)
            explanation="Goal-based capacity: 1×, 2×, 4×, 8×. Deposit stored Stardust in Reawakening to free room; deposits have no storage cap." if i==4 else "Base capacity grows 50% per Reawakening. Purchased expansions reset each run."
            self.text(c,26,y+101,explanation,9,MUTED,width=w-52)
            blocker="Maximum storage level" if maximum else "Requires first research" if not any(s.research) else "Own the matching station first" if not s.owned[i] else "Not enough "+name if s.resources[i]+1e-8<recipe[i] else ""
            self.button(c,26,y+151,w-52,28,"Storage complete" if maximum else "Expand "+name+" storage",lambda target=i:self.workshop_change(lambda:self.economy.upgrade_storage(target)),enabled=not blocker,primary=True,tip=blocker or "Double storage for this run. Automatic Reawakening capacity growth is permanent.")

    def draw_shelf_upgrade(self):
        c,w,s=self.panel,self.panel_width,self.economy.state
        y=164
        c.create_rectangle(12,y,w-14,y+203,fill=LIGHT,outline=GOLD)
        self.text(c,26,y+12,"Astral Cabinet · charm shelf",17,BURGUNDY,"Georgia")
        self.text(c,26,y+45,f"Shelf {s.shelf_level}/2 · {self.crafting.rack_capacity()} usable charm places",11,TEAL)
        self.text(c,26,y+74,"One base place + two run-built shelves + two legacy places. Shelf construction resets at Reawakening; legacies stay.",10,MUTED,width=w-52)
        recipe=self.crafting.shelf_price()
        self.text(c,26,y+123,"Both shelves built for this run" if s.shelf_level==2 else "Next shelf: "+price_text(recipe),10,INK,width=w-52)
        self.button(c,26,y+164,w-52,28,"Shelves complete" if s.shelf_level==2 else "Build next charm shelf",lambda:self.workshop_change(self.crafting.expand_shelf),enabled=s.shelf_level<2 and any(s.research) and all(have>=need for have,need in zip(s.resources,recipe)),primary=True,tip="Requires first research and the displayed Mana and Shards. Construction discounts apply. Adds one charm place for this run.")

    def draw_pedestal_stones(self,c,sx,sy):
        count=self.economy.state.awakenings
        completed,current=pedestal_ring(count)
        rings=[(min(6,count),29,11,553)]
        if count>6:rings.append((current or 6,53,19,578))
        for filled,rx,ry,cy in rings:
            for j in range(6):
                a=math.tau*j/6-math.pi/2
                x,y=500+rx*math.cos(a),cy+ry*math.sin(a)
                c.create_oval((x-5)*sx,(y-6)*sy,(x+5)*sx,(y+6)*sy,fill="#c3b5e4" if j<filled else "#393c4c",outline="#e9d5a7" if j<filled else "#a39486",width=1,tags="pedestal")
        if completed>=2:
            c.create_text(500*sx,615*sy,text=f"{completed} rings · {count} Reawakenings",fill="#dcc7a0",font=("Segoe UI",8),tags="pedestal")
        c.create_polygon(455*sx,527*sy,500*sx,505*sy,545*sx,527*sy,545*sx,568*sy,500*sx,590*sy,455*sx,568*sy,fill="",outline="",tags="pedestal")

    def pedestal_information(self):
        n=self.economy.state.awakenings
        self.dialog("The stones we carry",f"{n} Reawakenings remembered. Each Reawakening fills one socket. The first six stones complete the inner ring; later stones continue around the base.\n\nLegacy points per Reawakening: 1, 1, 2, 2, 3, 3 — twelve by the first completed ring. Later Reawakenings grant three each.\n\nNext Reawakening: {legacy_points(n+1)} legacy point(s). Spend them on permanent memories or cabinet upgrades.","Return to sanctuary")

    def draw_sanctuary_details(self,c,sx,sy):
        s=self.economy.state
        # Quiet fixed details: repeated frames do not generate new scenery.
        for j in range(12):
            x=130+j*64;y=815+(j%3)*19
            c.create_oval((x-7)*sx,(y-3)*sy,(x+7)*sx,(y+3)*sy,fill="#747b72",outline="#9d9e83")
        for x,y in ((110,660),(870,765),(195,815),(810,810)):
            for dx,dy in ((-7,0),(3,-5),(10,2)):
                c.create_line((x+dx)*sx,(y+8)*sy,(x+dx)*sx,(y+dy-9)*sy,fill="#6c8878",width=2)
                c.create_oval((x+dx-3)*sx,(y+dy-12)*sy,(x+dx+3)*sx,(y+dy-6)*sy,fill="#b6a3c3",outline="")
        patterns=(((110,170),(160,110),(220,150),(175,225)),((790,115),(835,190),(920,150),(875,85)),((310,90),(370,135),(420,80),(460,145)))
        for index,points in enumerate(patterns):
            if s.awakenings<(index+1)*2:continue
            for a,b in zip(points,points[1:]):c.create_line(a[0]*sx,a[1]*sy,b[0]*sx,b[1]*sy,fill="#696e8a",width=1)
            for x,y in points:c.create_oval((x-3)*sx,(y-3)*sy,(x+3)*sx,(y+3)*sy,fill="#c3c3dc",outline="")

    def draw_station_discovery(self,c,index,x,y,sx,sy):
        event=self.economy.state.station_event
        if not event or event["target"]!=index:return
        tag=f"building-{index}"
        cx,cy=x*sx,(y-175)*sy
        c.create_oval(cx-13,cy-13,cx+13,cy+13,fill="#e9dab2",outline="#b19c70",tags=tag)
        c.create_text(cx,cy,text="✦",fill=BURGUNDY,font=("Segoe UI Symbol",15),tags=tag)
        c.create_text(cx,cy-24,text="Discovery · click",fill="#eee1c5",font=("Segoe UI",9),tags=tag)

    def diagram(self,canvas,labels,x,y,width):
        gap=24;box=(width-gap*(len(labels)-1))/len(labels)
        for i,label in enumerate(labels):
            left=x+i*(box+gap)
            canvas.create_rectangle(left,y,left+box,y+56,fill="#e6d9bb",outline=GOLD)
            self.text(canvas,left+box/2,y+28,label,10,BURGUNDY,anchor="center",width=box-12)
            if i<len(labels)-1:
                canvas.create_line(left+box+3,y+28,left+box+gap-3,y+28,fill=TEAL,width=2,arrow="last")

    def material_information(self,target):
        purpose,production,uses,labels=MATERIAL_GUIDES[target]
        self.dialog(RESOURCE_NAMES[target],"","",cancel=None)
        c=self.modal_canvas
        self.clear_page(c)
        c.paper_image=self.art.parchment(550,450);c.create_image(0,0,image=c.paper_image,anchor="nw")
        self.text(c,28,50,ICONS[target]+"  "+RESOURCE_NAMES[target],24,BURGUNDY,"Georgia")
        self.text(c,28,94,purpose,12,INK,width=490)
        self.diagram(c,labels,28,133,490)
        self.text(c,28,211,"PRODUCED BY",9,TEAL)
        self.text(c,28,233,production,11,INK,width=490)
        self.text(c,28,286,"USED FOR",9,TEAL)
        self.text(c,28,308,uses,11,INK,width=490)
        def show_production():
            self.dismiss(force=True);self.set_tab("Production");self.panel.yview_moveto((54+target*190)/1012)
        self.button(c,28,391,290,36,"View production details",show_production,primary=True)
        self.button(c,330,391,192,36,"Close",self.dismiss)

    def visitor_position(self,progress,width,height):
        progress=max(0.,min(1.,progress))
        fade=min(1.,progress/.12,(1-progress)/.12)
        x=width*.5 if self.reduced_motion else -42+(width+84)*progress
        y=height*.24 if self.reduced_motion else height*(.22+.025*math.sin(progress*math.tau))
        return x,y,max(0.,fade)

    def illustrated_information(self,title,body):
        title_lower=title.lower()
        stations={"spirit well":0,"crystal garden":1,"essence distillery":2,"potion crucible":3,"astral circle":4}
        labels=next((MATERIAL_GUIDES[i][3] for name,i in stations.items() if name in title_lower),None)
        if labels is None:
            if "charm" in title_lower or "cabinet" in title_lower:labels=("Craft / Store","Equip","Bonus + links")
            elif "transmut" in title_lower:labels=("Source + Mana","Convert","Earlier material")
            elif "restoration" in title_lower or "construction" in title_lower:labels=("Mana + Shards","Build project","Production bonus")
            elif "talisman" in title_lower or title in ("Dawn Vessel","Violet Crown","Tideglass","Ember Heart","Star Compass"):labels=("Connect stars","Bind / Attune","Lasting ability")
        if labels is None:
            self.dialog(title,body,"Got it");return
        self.dialog(title,"","",cancel=None)
        self.modal.geometry("580x570");self.modal_canvas.configure(width=580,height=570)
        self.frame_window(self.modal,title,lambda:self.dismiss(force=True))
        c=self.modal_canvas;self.clear_page(c)
        c.paper_image=self.art.parchment(580,570);c.create_image(0,0,image=c.paper_image,anchor="nw")
        self.text(c,28,49,title,22,BURGUNDY,"Georgia",width=524)
        self.diagram(c,labels,28,110,524)
        area=tk.Text(self.modal,bg=LIGHT,fg=INK,font=("Segoe UI",11),wrap="word",relief="flat",padx=8,pady=8)
        area.place(x=28,y=190,width=508,height=292)
        area.insert("1.0",body);area.configure(state="disabled")
        scroll=tk.Scrollbar(self.modal,command=area.yview)
        scroll.place(x=537,y=190,width=15,height=292);area.configure(yscrollcommand=scroll.set)
        self.button(c,28,511,524,34,"Got it",self.dismiss,primary=True)
