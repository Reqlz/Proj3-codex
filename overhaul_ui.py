"""Talisman and guided-learning presentation for the existing Tk canvas application."""
import tkinter as tk
from astral_systems import (Constellation, TALISMAN_ABILITIES, PATTERNS, charm_contributions,
                           effect_text, RESOURCE_NAMES, TALISMAN_NAMES)
from learning import OPENING, LESSONS

INK, MUTED, BURGUNDY, TEAL, GOLD, PAPER, LIGHT = "#3f3027", "#79654d", "#743c40", "#246b66", "#ad8950", "#ecddbb", "#f7edda"
NAMES = TALISMAN_NAMES
ICONS = ("☽", "◇", "⚗", "♨", "☆")

def price_text(recipe):
    return " + ".join(f"{n:,.0f} {RESOURCE_NAMES[i]}" for i,n in enumerate(recipe) if n)

class OverhaulUI:
    def info_button(self, canvas, x, y, title, body):
        self.button(canvas,x,y,26,24,"ⓘ",lambda:self.illustrated_information(title,body),tip=body)

    def talisman_details(self, target):
        s=self.economy.state
        owned=target in s.talismans
        active={c["target"] for c in s.charms if self.economy.charm_active(c)}
        source={0:0,2:1,3:2,4:3}.get(target)
        if target==1:
            ready=any(self.economy.construction_level(i) and i in active for i in range(5))
            link="Project link active" if ready else "Link needs a built project and an active charm on its resource"
        else:
            link="Resource link active" if source in active else f"Link needs an active {RESOURCE_NAMES[source]} charm"
        if target==4: link+=f"; constellation harmony {min(3,len(active))}/3 active targets"
        return f"+{20+5*s.attunements[target]}% {RESOURCE_NAMES[target]} while owned. Rank {s.attunements[target]}/3.\n\n"+TALISMAN_ABILITIES[target]+"\n\n"+(link if owned else "Craft to activate these abilities. Stored mastery is inactive.")+"\n\nKeep one talisman at Reawakening. Unchosen mastery loses one rank; recrafting restores what remains."

    def draw_talisman_page(self):
        c,w,s=self.panel,self.panel_width,self.economy.state
        self.text(c,24,108,"All owned talismans work together. Keep ONE at Reawakening. Attunement improves lasting production without upkeep.",11,MUTED,width=w-48)
        for i,name in enumerate(NAMES):
            y=178+i*355
            owned=i in s.talismans
            rank=s.attunements[i]
            c.create_rectangle(12,y,w-14,y+339,fill=LIGHT,outline=GOLD)
            self.text(c,26,y+12,ICONS[i]+"  "+name,18,BURGUNDY,"Georgia")
            self.info_button(c,w-59,y+12,name,self.talisman_details(i))
            self.text(c,26,y+49,f"+{20+5*rank}% {RESOURCE_NAMES[i]} · rank {rank}/3 · "+("ACTIVE" if owned else "Not crafted"),11,TEAL)
            self.text(c,26,y+80,TALISMAN_ABILITIES[i],11,INK,width=w-55)
            active={ch["target"] for ch in s.charms if self.economy.charm_active(ch)}
            self.text(c,26,y+151,self.talisman_details(i).split("\n\n")[2],10,MUTED,width=w-55)
            next_rank=min(3,rank+1) if owned else 0
            price=self.crafting.challenge_price(i,next_rank)
            label="Practice · no reward" if owned and rank==3 else f"Attune to rank {next_rank}" if owned else "Trace constellation"
            self.text(c,26,y+208,"No cost or reward for practice" if owned and rank==3 else "On success: "+price_text(price),10,MUTED,width=w-55)
            unlocked=owned or self.crafting.talisman_unlocked(i)
            missing=[f"{max(0,n-s.resources[j]):,.0f} {RESOURCE_NAMES[j]}" for j,n in enumerate(price) if n>s.resources[j]+1e-8]
            self.text(c,26,y+250,"Requires this station's first inscription" if not unlocked else "Missing: "+", ".join(missing) if missing and not (owned and rank==3) else "Puzzle is free to try. Payment is checked on confirmation.",9,BURGUNDY,width=w-55)
            self.button(c,26,y+296,w-52,29,label,lambda target=i:self.open_puzzle(target),enabled=unlocked,primary=True,tip=self.talisman_details(i))
            self.register_target(f"talisman-{i}",c,(12,y,w-14,y+339))

    def open_puzzle(self, target):
        self.sync_time()
        s=self.economy.state
        if target not in s.talismans and not self.crafting.talisman_unlocked(target): return
        owned=target in s.talismans
        rank=min(3,s.attunements[target]+1) if owned else 0
        practice=owned and s.attunements[target]==3
        saved=s.astral_challenge
        if saved and (saved["target"],saved["rank"],saved["practice"])==(target,rank,practice):
            self.puzzle=Constellation.restore(saved)
        else:
            self.puzzle=Constellation(target,rank,practice=practice)
        self.persist_puzzle()
        self.puzzle_message=self.puzzle.message
        self.puzzle_hint=None
        self.puzzle_celebrating=False
        self.dialog("","","",cancel="Close")
        self.modal.geometry("820x650")
        self.modal_canvas.configure(width=820,height=650)
        self.frame_window(self.modal,"Astral connection · "+NAMES[target],lambda:self.dismiss(force=True))
        self.draw_puzzle()

    def persist_puzzle(self):
        self.economy.state.astral_challenge=self.puzzle.snapshot()
        self.save()

    def draw_puzzle(self):
        c,p=self.modal_canvas,self.puzzle
        self.clear_page(c)
        c.paper_image=self.art.parchment(820,650)
        c.create_image(0,0,image=c.paper_image,anchor="nw")
        title="Practice — no reward" if p.practice else f"Attunement {p.rank}/3" if p.rank else "Bind talisman"
        self.text(c,25,39,ICONS[p.target]+"  "+NAMES[p.target]+" · "+title,20,BURGUNDY,"Georgia")
        self.text(c,25,76,p.rules,11,INK,width=765)
        c.create_rectangle(22,132,798,444,fill=("#29334b","#342d49","#203b47","#422d38","#242b48")[p.target],outline=GOLD,width=2)
        coords=[(410+x*390,290+y*130) for x,y in p.points]
        self.puzzle_star_positions=coords
        legal={star for star in range(p.count) if not p.reason(star)}
        for a,b in sorted(p.edges):
            blocked=(a,b) in p.blocked
            available=bool(p.path and ((a==p.path[-1] and b in legal) or (b==p.path[-1] and a in legal)))
            c.create_line(*coords[a],*coords[b],fill="#b66970" if blocked else "#b8d8d0" if available else "#47556d",width=3 if available else 1,dash=(4,4) if blocked else ())
        for a,b in zip(p.path,p.path[1:]):
            c.create_line(*coords[a],*coords[b],fill="#786d71",width=9)
            c.create_line(*coords[a],*coords[b],fill="#ffe5a5",width=4)
        for i,(x,y) in enumerate(coords):
            tag=f"star-{i}"
            if i in legal:
                c.create_oval(x-22,y-22,x+22,y+22,outline="#aadcd3",width=2)
            if i in p.required and i not in p.path:
                c.create_oval(x-20,y-20,x+20,y+20,outline="#d9bf88",width=1)
            fill="#f5d79b" if i in p.path else ("#a3d4dc" if p.colours[i]==0 else "#bcaae0")
            if p.rank>=3 and p.colours[i]:
                c.create_polygon(x,y-17,x+17,y,x,y+17,x-17,y,fill=fill,outline=LIGHT,width=2,tags=tag)
            else:c.create_oval(x-16,y-16,x+16,y+16,fill=fill,outline=LIGHT,width=2,tags=tag)
            self.text(c,x,y,chr(65+i),10,"#182334",anchor="center",tags=tag)
            label="START" if i==p.start else "END" if i==p.end else (f"Rune {p.runes.index(i)+1}" if i in p.runes else "Required" if i in p.required else "Optional")
            self.text(c,x,y+22,label,9,LIGHT,anchor="n",tags=tag)
            if i==self.puzzle_hint:c.create_rectangle(x-22,y-22,x+22,y+22,outline="#ffdf83",width=3)
            binding=c.tag_bind(tag,"<Button-1>",lambda e,star=i:self.trace_star(star))
            c.button_bindings.append((tag,binding))
        reached=len(p.required.intersection(p.path))
        self.text(c,31,141,f"REQUIRED STARS  {reached}/{len(p.required)}",9,"#eee0bc")
        self.text(c,790,141,"Teal ring = available connection",9,"#aadcd3",anchor="ne")
        self.text(c,25,457,self.puzzle_message,11,TEAL,width=765)
        price=self.crafting.challenge_price(p.target,p.rank)
        self.text(c,25,495,"Practice is free; it cannot award mastery or materials." if p.practice else "Payment on confirmation: "+price_text(price),10,MUTED,width=765)
        self.button(c,25,551,85,31,"Undo",self.puzzle_undo)
        self.button(c,121,551,85,31,"Reset",self.puzzle_reset)
        self.button(c,217,551,85,31,"Hint",self.puzzle_show_hint)
        self.button(c,313,551,260,31,"Finish practice" if p.practice else "Confirm attunement" if p.rank else "Bind talisman",self.finish_puzzle,enabled=p.complete and not p.claimed,primary=True)
        self.button(c,640,551,155,31,"Save & close",self.dismiss)
        self.text(c,25,606,"No timer. Free hints and undo. Your route resumes when you return to this talisman.",10,MUTED)

    def trace_star(self,index):
        if getattr(self,"puzzle_celebrating",False) or self.puzzle.claimed:return
        self.puzzle.select(index)
        self.puzzle_hint=None
        self.puzzle_message=self.puzzle.message
        self.persist_puzzle();self.draw_puzzle()

    def puzzle_undo(self):
        if getattr(self,"puzzle_celebrating",False) or self.puzzle.claimed:return
        self.puzzle.undo();self.puzzle_hint=None
        self.puzzle_message="Last step removed. Try another connection."
        self.persist_puzzle();self.draw_puzzle()

    def puzzle_reset(self):
        if getattr(self,"puzzle_celebrating",False) or self.puzzle.claimed:return
        self.puzzle.path=[];self.puzzle_hint=None
        self.puzzle_message="Start a fresh route at START."
        self.persist_puzzle();self.draw_puzzle()

    def puzzle_show_hint(self):
        if getattr(self,"puzzle_celebrating",False) or self.puzzle.claimed:return
        self.puzzle_hint=self.puzzle.hint();self.puzzle_message=self.puzzle.message
        self.draw_puzzle()

    def finish_puzzle(self):
        if getattr(self,"puzzle_celebrating",False) or self.puzzle.claimed:return
        self.sync_time()
        success=self.puzzle.practice and self.puzzle.complete
        if success:
            self.economy.state.astral_challenge=None
            self.puzzle.claimed=True
        else:success=self.crafting.finish_talisman(self.puzzle)
        if success:
            # Commit before any effects. Interrupting or closing the animation cannot award twice.
            if self.save():self.celebrate_constellation()
            else:
                self.puzzle_message="Reward applied, but saving failed. Your journal will retry; do not close the game yet."
                self.draw_puzzle()
        else:
            self.puzzle_message="No payment taken: finish the route, gather the listed materials, or reopen if ownership or rank changed."
            self.draw_puzzle()

    def cancel_constellation_animation(self):
        timer=getattr(self,"puzzle_animation_timer",None)
        if timer is not None:self.root.after_cancel(timer)
        self.puzzle_animation_timer=None
        self.puzzle_celebrating=False

    def celebrate_constellation(self):
        self.puzzle_celebrating=True
        window=self.modal
        points=self.puzzle_star_positions[:]
        path=self.puzzle.path[:]
        c=self.modal_canvas
        self.clear_page(c)
        c.create_rectangle(0,0,820,650,fill="#202c43",outline="")
        self.text(c,410,75,"CONSTELLATION COMPLETE",22,"#efdeba","Georgia",anchor="center")
        self.text(c,410,535,"A pattern remembered." if self.puzzle.practice else "Your talisman holds the light.",14,"#c1d6d2",anchor="center")
        def frame(number=0):
            self.puzzle_animation_timer=None
            if self.modal is not window or not self.puzzle_celebrating:return
            c.delete("constellation-finale")
            progress=number/30
            flare=0 if self.reduced_motion else max(0,1-abs(progress-.55)/.35)
            for a,b in zip(path,path[1:]):
                c.create_line(*points[a],*points[b],fill="#5c697d",width=5+flare*8,tags="constellation-finale")
                c.create_line(*points[a],*points[b],fill="#f5ddb0",width=2+flare*2,tags="constellation-finale")
            for star in path:
                x,y=points[star];radius=3+flare*4
                c.create_oval(x-radius,y-radius,x+radius,y+radius,fill="#fff0cd",outline="",tags="constellation-finale")
                if progress<.35 and not self.reduced_motion:
                    shade=int(220-(progress/.35)*160)
                    colour=f"#{shade:02x}{shade:02x}{min(255,shade+15):02x}"
                    self.text(c,x,y-25,chr(65+star),10,colour,anchor="center",tags="constellation-finale")
            if self.reduced_motion or number>=30:
                def done():
                    self.puzzle_animation_timer=None
                    if self.modal is window:
                        self.dismiss(force=True);self.draw_ui()
                self.puzzle_animation_timer=self.root.after(250 if self.reduced_motion else 120,done)
            else:self.puzzle_animation_timer=self.root.after(33,lambda:frame(number+1))
        frame()

    def confirm_prestige(self):
        self.retain=set();self.retention_decided=False
        self.legacy_selection=None
        self.dialog("","","",cancel="Keep tending")
        self.modal.geometry("820x650")
        self.modal_canvas.configure(width=820,height=650)
        self.frame_window(self.modal,"Choose one talisman to carry",lambda:self.dismiss(force=True))
        self.draw_retention()

    def toggle_retain(self,target):
        self.retain={target};self.retention_decided=True
        self.draw_retention()

    def retain_none(self):
        self.retain=set();self.retention_decided=True
        self.draw_retention()

    def draw_retention(self):
        c,s=self.modal_canvas,self.economy.state
        self.clear_page(c)
        c.paper_image=self.art.parchment(820,650);c.create_image(0,0,image=c.paper_image,anchor="nw")
        self.text(c,25,39,"Choose the next run's foundation",23,BURGUNDY,"Georgia")
        self.text(c,25,77,f"Receive {self.economy.reward()} Moon Seals from deposited Stardust. Keep ONE talisman, or keep none.",11,INK)
        for i,name in enumerate(NAMES):
            y=111+i*74;owned=i in s.talismans;selected=i in self.retain;rank=s.attunements[i]
            c.create_rectangle(22,y,798,y+68,fill=LIGHT,outline=TEAL if selected else GOLD,width=2 if selected else 1)
            self.text(c,34,y+7,f"{name} · mastery {rank} → {rank if selected else max(0,rank-1)}",12,BURGUNDY)
            self.text(c,34,y+31,TALISMAN_ABILITIES[i],9,MUTED,width=558)
            self.button(c,620,y+16,162,30,"KEEP" if selected else "Choose" if owned else "Not owned",lambda target=i:self.toggle_retain(target),enabled=owned,primary=selected,tip=self.talisman_details(i))
        self.button(c,25,492,173,29,"Keep none",self.retain_none,primary=self.retention_decided and not self.retain)
        lost=[NAMES[i] for i in s.talismans if i not in self.retain]
        self.text(c,215,487,"Lost: "+(", ".join(lost) if lost else "no owned talismans"),10,BURGUNDY,width=580)
        self.text(c,25,534,"Deposited Stardust, stored materials, stations, charms, research and workshop progress reset. Unchosen mastery loses one rank, even for uncrafted talismans. Remaining mastery returns when recrafted.",10,MUTED,width=765)
        self.button(c,25,597,520,32,f"Reawaken · keep {len(self.retain)}/1 talisman",lambda:self.show_legacy_choice(True),enabled=self.retention_decided,primary=True,tip="Choose a talisman or Keep none before continuing.")
        self.button(c,620,597,175,32,"Keep tending",self.dismiss)

    def set_pattern(self,pattern):
        self.charm_pattern=pattern;self.draw_ui()

    def charm_details(self,charm):
        active={ch["target"] for ch in self.economy.state.charms if self.economy.charm_active(ch)}
        values=charm_contributions(charm,active,1 in self.economy.state.talismans and self.economy.construction_level(charm["target"])>0)
        status="Active now" if self.economy.charm_active(charm) else "Inactive now; stored or waiting for its mode"
        return f"{charm.get('pattern','standard').title()}: {effect_text(values)}. {status}.\n"+PATTERNS[charm.get("pattern","standard")]+"\nSecondary bonuses do not trigger further links. Charms reset at Reawakening."

    def register_target(self,key,canvas,rect):
        if not hasattr(self,"guide_targets"): self.guide_targets={}
        self.guide_targets[key]=(canvas,rect)

    def guide_gate(self,event):
        if not getattr(self,"guide_active",False) or self.modal or self.tome_window or self.tree_window: return
        widget=event.widget
        if getattr(self,"guide_frame",None) and str(widget).startswith(str(self.guide_frame)): return
        target=getattr(self,"guide_target",None)
        if target:
            canvas,(x1,y1,x2,y2)=target
            x=event.x_root-canvas.winfo_rootx()+canvas.canvasx(0)
            y=event.y_root-canvas.winfo_rooty()+canvas.canvasy(0)
            if widget==canvas and x1<=x<=x2 and y1<=y<=y2:return
        if widget==getattr(self,"scroll",None):return
        return "break"

    def guide_control_allowed(self,canvas,rect):
        if not getattr(self,"guide_active",False) or self.modal or self.tome_window or self.tree_window:return True
        target=getattr(self,"guide_target",None)
        if not target or target[0]!=canvas:return False
        x1,y1,x2,y2=target[1];a,b,d,e=rect
        return a>=x1-2 and b>=y1-2 and d<=x2+2 and e<=y2+2

    def finish_lesson(self):
        s=self.economy.state
        if getattr(self,"lesson_key",None):
            if self.lesson_key not in s.lessons_seen:s.lessons_seen.append(self.lesson_key)
            if self.lesson_key=="update":s.update_tour=False
            if self.lesson_key=="storage_update":s.storage_update=False
        else:self.guide.acknowledge()
        self.save();self.draw_ui()

    def skip_learning(self):
        s=self.economy.state
        if getattr(self,"lesson_key",None):self.finish_lesson();return
        s.tutorial_skipped=True;s.guide_step=len(OPENING);s.tutorial_step=5
        s.materials_tutorial=6
        self.save();self.draw_ui()

    def show_lesson_activity(self):
        key=getattr(self,"learning_target_id","")
        if key.startswith("activity-"):
            self.tab="Workshop";self.crafting_section=key[len("activity-"):]
            self.panel.yview_moveto(0);self.draw_ui()

    def learning_token(self):
        if not getattr(self,"guide_active",False) or self.modal or self.tome_window or self.tree_window:
            return None
        return (getattr(self,"lesson_key",None),self.economy.state.guide_step)

    def acknowledge_learning_interaction(self, token):
        # A callback can change pages or advance the tour. Never acknowledge its successor.
        if token is None: return
        key,step=token
        s=self.economy.state
        if key:
            if key in s.lessons_seen:return
            s.lessons_seen.append(key)
            if key=="update":s.update_tour=False
            if key=="storage_update":s.storage_update=False
        elif s.guide_step==step and step<len(OPENING) and OPENING[step][3]=="next":
            self.guide.acknowledge()
        else:return
        self.cancel_learning_hover()
        self.learning_hover_latched=True
        self.save();self.draw_ui()

    def activate_learning_control(self,canvas,rect,callback):
        token=self.learning_token() if self.guide_control_allowed(canvas,rect) else None
        self.cancel_learning_hover()
        callback()
        self.acknowledge_learning_interaction(token)

    def learning_hit(self,event):
        target=getattr(self,"guide_target",None)
        if not self.learning_token() or not target or event.widget!=target[0]:return False
        canvas,(x1,y1,x2,y2)=target
        x,y=canvas.canvasx(event.x),canvas.canvasy(event.y)
        return x1<=x<=x2 and y1<=y<=y2

    def cancel_learning_hover(self,event=None):
        timer=getattr(self,"learning_hover_timer",None)
        if timer is not None:self.root.after_cancel(timer)
        self.learning_hover_timer=None
        if event is not None:self.learning_hover_latched=False

    def learning_hover(self,event):
        token=self.learning_token()
        if getattr(event,"state",0)&0x100:
            self.cancel_learning_hover();return
        if not self.learning_hit(event):
            self.cancel_learning_hover();self.learning_hover_latched=False
            return
        if token[0] is None and (token[1]>=len(OPENING) or OPENING[token[1]][3]!="next"):return
        if getattr(self,"learning_hover_latched",False) or getattr(self,"learning_hover_timer",None) is not None:return
        def acknowledge():
            self.learning_hover_timer=None
            if self.learning_token()==token:self.acknowledge_learning_interaction(token)
        self.learning_hover_timer=self.root.after(650,acknowledge)

    def learning_press(self,event):
        self.cancel_learning_hover()
        self.learning_press_token=self.learning_token() if self.learning_hit(event) else None
        return self.guide_gate(event)

    def learning_release(self,event):
        token=getattr(self,"learning_press_token",None)
        self.learning_press_token=None
        if not token or not self.learning_hit(event):return
        controls=getattr(event.widget,"controls",None)
        # CanvasButtons performs acknowledgements after its actual action succeeds.
        if controls and controls.hit(event):return
        self.acknowledge_learning_interaction(token)

    def hide_learning(self):
        self.guide_active=False
        self.cancel_learning_hover()
        self.learning_stage_signature=None
        if getattr(self,"guide_frame",None):self.guide_frame.place_forget()
        self.guide_frame_geometry=None
        for canvas in (self.background,self.panel,self.scene):
            canvas.itemconfigure("guide-overlay",state="hidden")

    @staticmethod
    def clear_learning_artwork(canvas):
        # Keep spotlight items alive across normal redraws and animation frames.
        overlay=set(canvas.find_withtag("guide-overlay"))
        artwork=[item for item in canvas.find_all() if item not in overlay]
        if artwork:canvas.delete(*artwork)

    def refresh_learning(self):
        if self.in_menu or self.settings_open or self.modal or self.tome_window or self.tree_window or self.economy.state.tutorial_invite:
            self.hide_learning();return
        s=self.economy.state
        self.guide.update_learning()
        opening=not s.tutorial_skipped and not s.tutorial_invite and s.guide_step<len(OPENING)
        key=None if opening or not self.preference("contextual_lessons",True) else self.guide.pending_lesson()
        # Lessons are a saved queue. Skip dismisses this lesson only; the next is shown on a later redraw.
        if not opening and not key:
            self.hide_learning();return
        if opening:
            title,target,body,kind=OPENING[s.guide_step]
        else:
            title,target,body=LESSONS[key];kind="next"
        from learning import lesson_content
        content=lesson_content(s.guide_step,key)
        full_body=body
        if self.preference("tutorial_detail")=="Short":body=content["short"]
        self.lesson_key=key;self.learning_target_id=target
        stage=(id(s),opening,s.guide_step,key,target)
        new_stage=stage!=getattr(self,"learning_stage_signature",None)
        if new_stage:self.cancel_learning_hover()
        self.learning_stage_signature=stage
        required_tab="Production" if target in ("buy-0","buy-1") else "Research" if target.startswith("research-") else None
        if required_tab and self.tab!=required_tab:
            self.tab=required_tab;self.panel.yview_moveto(0);self.draw_panel()
        if target.startswith("activity-") and (self.tab!="Workshop" or target not in getattr(self,"guide_targets",{})):
            target="tab-Workshop"
        self.guide_target=getattr(self,"guide_targets",{}).get(target)
        if not self.guide_target:
            self.guide_target=getattr(self,"guide_targets",{}).get("tab-Workshop")
        if new_stage and self.guide_target and self.guide_target[0]==self.panel:
            _,(_,y1,_,y2)=self.guide_target
            top=self.panel.canvasy(0);height=self.panel.winfo_height()
            if y1<top or y2>top+height:
                region=self.panel.cget("scrollregion").split()
                if region:self.panel.yview_moveto(max(0,y1-15)/float(region[3]))
        self.guide_active=True
        if not getattr(self,"guide_frame",None):
            self.guide_frame=tk.Frame(self.background,bg=LIGHT,highlightbackground=BURGUNDY,highlightthickness=3,padx=12,pady=10)
            self.guide_title=tk.Label(self.guide_frame,bg=LIGHT,fg=BURGUNDY,font=("Georgia",15),anchor="w",justify="left")
            self.guide_title.pack(fill="x")
            self.guide_body=tk.Label(self.guide_frame,bg=LIGHT,fg=INK,font=("Segoe UI",11),anchor="w",justify="left")
            self.guide_body.pack(fill="x",pady=(8,10))
            self.guide_actions=tk.Frame(self.guide_frame,bg=LIGHT);self.guide_actions.pack(fill="x")
        signature=(opening,s.guide_step,key,self.scene_width,body,self.preference("text_size"))
        if getattr(self,"guide_card_signature",None)!=signature:
            self.guide_card_signature=signature
            for widget in self.guide_actions.winfo_children():widget.destroy()
            self.guide_title.configure(font=("Georgia",round(15*self.preference("text_size")/100)))
            self.guide_body.configure(font=("Segoe UI",round(11*self.preference("text_size")/100)))
            self.guide_title.configure(text=(f"GUIDED TOUR {s.guide_step+1}/{len(OPENING)} · " if opening else "NEW DISCOVERY · ")+title,wraplength=self.scene_width-60)
            self.guide_body.configure(text="✧  "+body,wraplength=self.scene_width-60)
            def control(label,callback):
                index=len(self.guide_actions.winfo_children())
                tk.Button(self.guide_actions,text=label,command=callback,bg=PAPER,fg=INK,font=("Segoe UI",round(10*self.preference("text_size")/100)),relief="flat",padx=6,pady=4).grid(row=index//2,column=index%2,sticky="ew",padx=3,pady=3)
            control("More detail",lambda:self.dialog(title,full_body,"Close"))
            if kind=="next":control("Got it" if key else "Next",self.finish_lesson)
            if self.learning_target_id.startswith("activity-"):control("Show activity",self.show_lesson_activity)
            control("Dismiss lesson" if key else "Skip tour",self.skip_learning)
            if kind=="action":
                tk.Label(self.guide_actions,text="Use the highlighted item",bg=LIGHT,fg=TEAL,font=("Segoe UI",9)).grid(row=3,column=0,columnspan=2,sticky="w")
        frame_x,frame_y,frame_width=35,205,self.scene_width-22
        if self.guide_target and self.guide_target[0]==self.scene:
            # Keep the illustrated target unobscured at the minimum window size.
            frame_x=self.panel_x+12;frame_y=280;frame_width=self.panel_width-24
            self.guide_title.configure(wraplength=frame_width-35)
            self.guide_body.configure(wraplength=frame_width-35)
        geometry=(frame_x,frame_y,frame_width)
        if geometry!=getattr(self,"guide_frame_geometry",None):
            self.guide_frame.place(x=frame_x,y=frame_y,width=frame_width)
            self.guide_frame.lift()
            self.guide_frame_geometry=geometry
        self.shield(self.guide_frame)
        for canvas in (self.background,self.panel,self.scene):self.paint_learning(canvas)

    def paint_learning(self,canvas):
        if not getattr(self,"guide_active",False) or self.modal or self.tome_window or self.tree_window:
            canvas.itemconfigure("guide-overlay",state="hidden")
            return
        left,top=0.,0.
        right,bottom=float(canvas.winfo_width()),float(canvas.winfo_height())
        region=canvas.cget("scrollregion").split()
        if len(region)==4:
            x1,y1,x2,y2=map(float,region)
            left,top=min(left,x1),min(top,y1)
            right,bottom=max(right,x2),max(bottom,y2)
        target=getattr(self,"guide_target",None)
        rect=target[1] if target and target[0]==canvas else None
        masks=[(left,top,right,bottom)]+[(0,0,0,0)]*3 if not rect else [
            (left,top,right,rect[1]-5),(left,rect[3]+5,right,bottom),
            (left,rect[1]-5,rect[0]-5,rect[3]+5),(rect[2]+5,rect[1]-5,right,rect[3]+5)]
        if not hasattr(canvas,"learning_items"):canvas.learning_items={}
        def item(key,kind,coords,**options):
            if key not in canvas.learning_items:
                canvas.learning_items[key]=getattr(canvas,"create_"+kind)(*coords,tags="guide-overlay",**options)
            else:
                identity=canvas.learning_items[key]
                canvas.coords(identity,*coords);canvas.itemconfigure(identity,**options)
        for i,(x1,y1,x2,y2) in enumerate(masks):
            item(f"mask-{i}","rectangle",(x1,y1,max(x1,x2),max(y1,y2)),fill="#172033",stipple="gray50",outline="",state="normal" if x2>x1 and y2>y1 else "hidden")
        if rect:
            x1,y1,x2,y2=rect
            item("outline","rectangle",(x1-4,y1-4,x2+4,y2+4),outline="#fff5d4",width=7,state="normal")
            item("border","rectangle",(x1-4,y1-4,x2+4,y2+4),outline=BURGUNDY,width=3,state="normal")
            x=(x1+x2)/2
            above=y1-top>45
            start=y1-38 if above else y2+38;end=y1-8 if above else y2+8
            item("arrow","line",(x,start,x,end),fill="#fff0bc",width=6,arrow="last",arrowshape=(14,18,7),state="normal")
            item("label","text",(x,start-8 if above else start+8),text="THIS ITEM",fill=BURGUNDY,font=("Segoe UI",10,"bold"),state="normal")
        else:
            for key in ("outline","border","arrow","label"):
                if key in canvas.learning_items:canvas.itemconfigure(canvas.learning_items[key],state="hidden")
        canvas.tag_raise("guide-overlay")

    def suggested_card(self,y):
        if not self.preference("suggestions",True):return
        c=self.background
        self.text(c,28,y,"SUGGESTED NEXT STEP",10,BURGUNDY)
        self.text(c,28,y+24,self.guide.suggested(),10,INK,width=self.scene_width-18)

    def contextual_tip(self,label):
        if "Inscribe" in label:return "Research doubles capacity and consumes this station's output. Own the station and gather the shown material. Research resets at Reawakening."
        if label.startswith("Buy "):return "Spend the listed Mana for the selected quantity. Dawn Vessel discounts this price. Stations reset at Reawakening."
        if "Craft for" in label:return "Requires the target station, recipe tier, selected pattern/mode unlocks, ingredients, and no existing charm of this target. Crafting stores the charm; Equip activates it."
        if label=="Equip":return "Equip a stored charm in a free cabinet place. Its clock runs only in its selected mode. Online and offline activity determines its synergies."
        if "Build level" in label or "Upgrade to level" in label:return "Own this station, complete first research, and gather the displayed Mana and Shards. Each level adds production. Violet Crown reduces Shard cost. Construction resets at Reawakening."
        if "Refill" in label:return "Own a Crucible and equip an unexpired charm with missing time. Pay Elixirs to restore its crafted maximum. Refill prices grow after each use; Ember Heart discounts them."
        if label in ("Online","Offline","Combined"):return "Online works while loaded; Offline works while away and requires a Distillery; Combined works in both and requires a Crucible. Only active charms trigger links."
        if "contract" in label.lower() or "Deliver" in label:return "Requires the courier unlock and the shown materials. Quotes are fixed; completing or declining starts a cooldown. Rewards do not count as prestige production."
        if "Transmute" in label:return "Own the source station and afford the displayed input plus Mana fee. The conversion is lossy and does not count as production."
        if "commission" in label.lower() or "exchange" in label.lower():return "Requires an Astral Circle, displayed materials, and a ready cooldown. Review the quoted output; rewards do not count toward prestige earnings."
        if "Reawaken" in label:return "Own every station and reach the run-earned Stardust goal. Spent Stardust still counts. Keep one talisman; unchosen attunement loses one rank. Review all losses before confirming."
        return ""
