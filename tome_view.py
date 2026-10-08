"""Resizable reference book with a separate, always visible footer."""
import tkinter as tk

FLOWS={'first':'Spark → Spirit Wells → Crystal Gardens',
 'research':'Materials → Inscription → 2× station output',
 'distillery':'3 Shards → Distillery → 1 Essence',
 'crucible':'4 Essence → Crucible → 1 Elixir',
 'astral':'5 Elixirs → Astral Circle → 1 Stardust',
 'charms':'Stored → Equipped → Active until expiry',
 'talismans':'Bind → Attune → +20–35% production',
 'reawakening':'Deposit Stardust → Keep one talisman → Reawaken',
 'offline':'Leave sanctuary → Produce up to storage limits → Return'}

class TomeView:
 def open_tome(self,chapter=None):
  from main import CHAPTERS
  self.close_tree()
  if self.in_menu:return
  self.economy.state.tome_opened=True;self.guide.update()
  if chapter:
   self.tome_chapter=chapter
   if chapter not in self.economy.state.chapters_unlocked:self.tome_all=True
  self.guide.read(self.tome_chapter);self.save()
  if not self.tome_window:
   win=self.new_window();self.tome_window=win
   win.title('The Spell Tome');win.transient(self.root);win.geometry('960x620');win.minsize(700,480)
   win.configure(bg='#ecddbb');win.rowconfigure(1,weight=1);win.columnconfigure(1,weight=1)
   header=tk.Frame(win,bg='#ecddbb',padx=16,pady=18);header.grid(row=0,column=0,columnspan=2,sticky='ew')
   self.tome_heading=tk.Label(header,bg='#ecddbb',fg='#743c40',font=('Georgia',20),anchor='w');self.tome_heading.pack(fill='x')
   tk.Button(header,text='Relevant / all chapters',command=self.toggle_tome_all).pack(anchor='w',pady=(8,0))
   left=tk.Frame(win);left.grid(row=1,column=0,sticky='nsew',padx=(16,8))
   self.tome_list=tk.Listbox(left,width=25,exportselection=False,activestyle='dotbox',font=('Segoe UI',round(11*self.preference('text_size')/100)));self.tome_list.pack(side='left',fill='both',expand=True)
   ls=tk.Scrollbar(left,command=self.tome_list.yview);ls.pack(side='right',fill='y');self.tome_list.configure(yscrollcommand=ls.set)
   self.tome_list.bind('<<ListboxSelect>>',self.select_tome_row)
   right=tk.Frame(win);right.grid(row=1,column=1,sticky='nsew',padx=(8,16))
   self.tome_body=tk.Text(right,wrap='word',bg='#f7edda',fg='#3f3027',padx=16,pady=16,spacing3=12,relief='flat')
   self.tome_body.pack(side='left',fill='both',expand=True)
   scroll=tk.Scrollbar(right,command=self.tome_body.yview);scroll.pack(side='right',fill='y');self.tome_body.configure(yscrollcommand=scroll.set)
   footer=tk.Frame(win,bg='#ecddbb',padx=16,pady=16);footer.grid(row=2,column=0,columnspan=2,sticky='ew')
   self.tome_flow=tk.Label(footer,bg='#ecddbb',fg='#246b66',font=('Segoe UI',round(11*self.preference('text_size')/100)),wraplength=650)
   self.tome_flow.grid(row=0,column=0,columnspan=3,sticky='ew',pady=(0,12))
   for j,(label,callback) in enumerate((('Replay first steps',self.restart_tutorial),('Materials walkthrough',self.start_materials_tutorial),('Close',self.close_tome))):
    footer.columnconfigure(j,weight=1)
    tk.Button(footer,text=label,command=callback,font=('Segoe UI',round(10*self.preference('text_size')/100)),wraplength=190,padx=8,pady=8).grid(row=1,column=j,sticky='ew',padx=4)
   win.protocol('WM_DELETE_WINDOW',self.close_tome);win.bind('<Escape>',lambda e:self.close_tome())
  self.draw_tome();self.tome_window.deiconify();self.tome_window.lift();self.draw_ui()

 def select_tome_row(self,event=None):
  selection=self.tome_list.curselection()
  if selection:self.choose_chapter(self.tome_visible[selection[0]][0])

 def draw_tome(self):
  from main import CHAPTERS
  if not self.tome_window:return
  s=self.economy.state
  position=self.tome_body.yview()[0] if getattr(self,'tome_rendered_chapter',None)==self.tome_chapter else 0
  self.tome_visible=[ch for ch in CHAPTERS if self.tome_all or ch[0] in s.chapters_unlocked]
  self.tome_list.delete(0,'end')
  for i,(key,title,_) in enumerate(self.tome_visible):
   self.tome_list.insert('end',title)
   if key==self.tome_chapter:self.tome_list.selection_set(i);self.tome_list.see(i)
  key,title,body=next(ch for ch in CHAPTERS if ch[0]==self.tome_chapter)
  self.tome_heading.configure(text=title,wraplength=max(500,self.tome_window.winfo_width()-50))
  self.tome_flow.configure(text=FLOWS.get(key,''))
  self.tome_body.configure(state='normal',font=('Segoe UI',round(12*self.preference('text_size')/100)))
  self.tome_body.delete('1.0','end');self.tome_body.insert('1.0',body)
  self.tome_body.configure(state='disabled');self.tome_body.yview_moveto(position)
  self.tome_rendered_chapter=key;self.tome_signature=(tuple(s.chapters_unlocked),tuple(s.chapters_read))
