"""Bounded decorative scenery effects; never register interaction targets."""
import math
from array import array

def environment(image,scene):
 from PIL import ImageDraw
 if scene=='Moonlit Ruins':return
 d=ImageDraw.Draw(image)
 color='#243f51' if scene=='Reflecting Pond' else '#625c38'
 d.polygon([(0,730),(180,700),(400,745),(630,700),(1000,680),(1000,1000),(0,1000)],fill=color)
 if scene=='Glowing Hay Field':
  for j in range(550):
   x=(j*137)%1000;y=720+(j*73)%280
   d.line((x,y,x-3,y-13),fill=('#8c8550','#aaa05b','#797747')[j%3],width=2)

def reflection(image):
 from PIL import Image,ImageEnhance
 strip=image.crop((70,240,940,920)).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((780,100))
 strip=ImageEnhance.Color(strip).enhance(.25)
 strip=Image.blend(Image.new('RGBA',strip.size,'#243f51'),strip.convert('RGBA'),.23)
 image.paste(strip,(110,895))

def object_reflections(app,t,moving):
 import tkinter as tk
 from PIL import Image,ImageDraw,ImageTk
 c=app.scene
 if not isinstance(c,tk.Canvas):return
 s=app.economy.state;w,h=app.scene_width,app.scene_height
 signature=(w,h,tuple(s.owned),tuple(s.research),tuple(s.restoration_levels),s.awakenings,
            tuple((ch['target'],ch['equipped']) for ch in s.charms),bool(s.lantern_remaining))
 if signature!=getattr(app,'reflection_signature',None):
  im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
  tags=['building-'+str(i) for i in range(5)]+['cabinet','pedestal']
  identities=set(item for tag in tags for item in c.find_withtag(tag))
  for item in sorted(identities):
   kind=c.type(item);coords=c.coords(item)
   if kind not in ('rectangle','oval','polygon','line'):continue
   fill=c.itemcget(item,'fill') or None
   outline=(c.itemcget(item,'outline') or None) if kind!='line' else None
   if not fill and not outline:continue
   if kind=='line':d.line(coords,fill=fill,width=2)
   elif kind=='polygon':d.polygon(list(zip(coords[::2],coords[1::2])),fill=fill,outline=outline)
   elif kind=='oval':d.ellipse(coords,fill=fill,outline=outline)
   else:d.rectangle(coords,fill=fill,outline=outline)
  strip=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((w,max(12,round(h*.11))))
  strip.putalpha(strip.getchannel('A').point(lambda a:round(a*.23)))
  frames=[]
  for phase in range(12):
   frame=Image.new('RGBA',strip.size)
   for y in range(0,strip.height,4):
    offset=round(2*math.sin(phase*math.tau/12+y*.3)) if phase else 0
    frame.paste(strip.crop((0,y,w,min(y+4,strip.height))),(offset,y))
   frames.append(ImageTk.PhotoImage(frame))
  app.reflection_frames=frames;app.reflection_signature=signature
 phase=1+int(t*4)%11 if moving and app.preference('pond_ripples') else 0
 c.create_image(0,h*.885,image=app.reflection_frames[phase],anchor='nw',tags='environment')

def draw_environment_effects(app):
 c=app.scene;w=app.scene_width;h=app.scene_height;s=app.economy.state
 scene=s.scenery
 moving=not app.reduced_motion and app.preference('scenery_animation')
 t=app.anim_time if moving else 0
 if scene=='Reflecting Pond':
  object_reflections(app,t,moving)
  for j in range(9):
   offset=math.sin(t*.7+j)*7 if app.preference('pond_ripples') else 0
   x=(j*117%850+65)*w/1000;y=(910+j*9)*h/1000
   c.create_line(x-25+offset,y,x+25+offset,y,fill='#4c6b79',tags='environment')
 elif scene=='Glowing Hay Field':
  for j in range(65):
   x=(j*137%980+10)*w/1000;y=(925+j*31%75)*h/1000
   sway=math.sin(t*.65+x/130)*5 if app.preference('field_sway') else 0
   c.create_line(x,y,x+sway,y-12,fill='#a29859' if app.preference('ambient_glow') else '#7e784d',width=2,tags='environment')

class ArrivalChime:
 """One independent mixer channel; absence of audio never blocks gameplay."""
 def __init__(self):self.sound=None
 def play(self,volume):
  try:
   from pygame import mixer
   if not mixer.get_init():mixer.init()
   if self.sound is None:
    rate,_,channels=mixer.get_init();samples=array('h')
    for i in range(int(rate*.45)):
     t=i/rate;v=int(8000*math.sin(2*math.pi*660*t)*math.exp(-9*t)*min(1,t*60))
     samples.extend([v]*channels)
    self.sound=mixer.Sound(buffer=samples.tobytes())
   self.sound.set_volume(max(0,min(1,volume/100)));self.sound.play()
  except Exception:pass
