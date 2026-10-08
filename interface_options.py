"""Shared, validated display preferences and category definitions."""
SCENES=('Moonlit Ruins','Reflecting Pond','Glowing Hay Field')
DEFAULTS=dict(presentation='Concise',numbers='Compact',storage_bars=True,suggestions=True,
 tooltip_delay=550,text_size=100,high_contrast=False,scenery_animation=True,pond_ripples=True,
 field_sway=True,ambient_glow=True,visitor_cue='Clear',visitor_notice=True,chime=False,
 chime_volume=30,tutorial_detail='Short',contextual_lessons=True)
OPTIONS=dict(presentation=('Concise','Classic'),numbers=('Compact','Full'),tooltip_delay=(300,550,900),
 text_size=(100,115,130),visitor_cue=('Subtle','Clear','Prominent'),tutorial_detail=('Short','Full'))
CATEGORIES=('Interface','Accessibility','Scenery','Visitors & Notifications','Audio','Help')
CONTROLS={
 'Interface':(('presentation','Presentation'),('numbers','Numbers'),('storage_bars','Storage bars'),('suggestions','Suggested next step'),('tooltip_delay','Tooltip delay (ms)')),
 'Accessibility':(('text_size','Text size (%)'),('high_contrast','Higher contrast'),('reduced_motion','Reduced motion'),('celestial_cursor','Celestial cursor'),('station_cursors','Station cursors')),
 'Scenery':(('scenery_animation','Scenery animation'),('pond_ripples','Pond ripples'),('field_sway','Field sway'),('ambient_glow','Ambient glow'),('density','Effect density'),('fps','Frame rate')),
 'Visitors & Notifications':(('spirits','Celestial visitors'),('visitor_cue','Arrival cue'),('visitor_notice','Visitor notice'),('chime','Arrival chime'),('chime_volume','Chime volume (%)')),
 'Audio':(('music','Music'),('volume','Music volume (%)'),('shuffle','Shuffle playlist')),
 'Help':(('tutorial_detail','Tutorial explanations'),('contextual_lessons','Contextual lessons'))}

def valid_option(key,value):
 return (key not in OPTIONS or value in OPTIONS[key]) and (key!='chime_volume' or 0<=value<=100)

class SettingsUI:
 def preference(self,key,default=None):
  prefs=getattr(self,'preferences',None)
  return getattr(prefs,'values',{}).get(key,DEFAULTS.get(key,default))

 def settings_navigation(self):
  category=getattr(self,'settings_category','Interface')
  for i,name in enumerate(CATEGORIES):
   self.button(self.background,32,135+i*57,220,46,name,lambda n=name:self.select_settings_category(n),primary=name==category)

 def select_settings_category(self,name):
  if not hasattr(self,'settings_positions'):self.settings_positions={}
  self.settings_positions[getattr(self,'settings_category','Interface')]=self.panel.yview()[0]
  self.settings_category=name
  self.panel.yview_moveto(0)
  self.draw_ui()
  self.panel.yview_moveto(self.settings_positions.get(name,0))

 def change_scene(self,name):
  if self.in_menu:return
  self.economy.state.scenery=name
  self.save();self.art.cache.clear();self.draw_ui()

 def settings_page(self):
  c,w=self.panel,self.panel_width
  category=getattr(self,'settings_category','Interface')
  self.text(c,24,20,category,22,'#743c40','Georgia')
  y=80
  if category=='Scenery':
   self.text(c,24,y,'Sanctuary scenery' if not self.in_menu else 'Select a sanctuary to change its scenery.',12)
   y+=38
   for name in SCENES:
    self.button(c,24,y,w-48,38,name,lambda n=name:self.change_scene(n),enabled=not self.in_menu,primary=not self.in_menu and self.economy.state.scenery==name)
    y+=48
   y+=20
  for key,label in CONTROLS[category]:
   value=self.preference(key)
   self.text(c,24,y,label,12)
   y+=32
   choices=OPTIONS.get(key)
   if key=='density':choices=('Low','Standard','High')
   if key=='fps':choices=(30,60)
   if key in ('volume','chime_volume'):choices=(max(0,value-10),value,min(100,value+10))
   if choices:
    bw=(w-48-8*(len(choices)-1))/len(choices)
    for j,v in enumerate(choices):self.button(c,24+j*(bw+8),y,bw,36,str(v),lambda k=key,n=v:self.set_preference(k,n),primary=value==v)
   else:self.button(c,24,y,w-48,36,'On' if value else 'Off',lambda k=key,v=value:self.set_preference(k,not v),primary=bool(value))
   y+=65
  if category=='Interface':
   self.button(c,24,y,w-48,38,'Toggle fullscreen (F11)',self.toggle_fullscreen);y+=55
  if category=='Accessibility':
   self.text(c,24,y,'Tab selects controls. Enter or Space activates. Escape closes a dialog. Reduced motion keeps saved scenery choices.',11,width=w-48);y+=100
  if category=='Audio':
   for label,callback in [('Pause / resume',self.music.pause),('Next track',self.music.next),('Reload playlist',self.music.reload)]:
    self.button(c,24,y,w-48,36,label,callback);y+=48
   self.text(c,24,y,self.music.status,11,width=w-48);y+=80
   self.button(c,24,y,w-48,36,'Playlist help',lambda:self.dialog('Your music','Copy OGG, MP3 or WAV files into assets/music. List exact filenames in playlist.json, then reload the playlist. Nothing is uploaded.','Close'));y+=48
  if category=='Help':
   def tour():self.close_settings();self.restart_tutorial()
   def materials():self.close_settings();self.start_materials_tutorial()
   for label,callback in [('Replay guided first steps',tour),('Replay materials walkthrough',materials),('Reset preferences',self.reset_preferences)]:
    self.button(c,24,y,w-48,38,label,callback,enabled=not self.in_menu or label=='Reset preferences');y+=52
  self.settings_content_height=y+60
