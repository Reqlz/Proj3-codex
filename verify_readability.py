"""Live Tk checks using temporary saves. Not a substitute for inspecting captures."""
from pathlib import Path
import tempfile
import tkinter as tk
from main import AtelierApp,SaveStore
from learning import LESSONS
from interface_options import SCENES,CATEGORIES
from verify_ui import capture

def verify():
 with tempfile.TemporaryDirectory() as tmp:
  root=tk.Tk();errors=[]
  root.report_callback_exception=lambda kind,value,trace:errors.append(value)
  app=AtelierApp(root,SaveStore(Path(tmp)/'slot.json'),start_loop=False,show_welcome=False,apply_preferences=False)
  try:
   s=app.economy.state;s.tutorial_skipped=True;s.guide_step=10;s.materials_tutorial=6;s.lessons_seen=list(LESSONS)
   s.owned=[12]*5;s.research=[2]*5;s.run_mana=1e7;s.resources=[100000,80000,10000,400,100]
   for dimensions in ('1100x720','1440x900','fullscreen'):
    root.attributes('-fullscreen',dimensions=='fullscreen')
    if dimensions!='fullscreen':root.geometry(dimensions)
    root.update()
    for size in (100,115,130):
     app.preferences.values['text_size']=size
     for mode in ('Concise','Classic'):
      app.preferences.values['presentation']=mode;app.layout();root.update()
      for scene in SCENES:
       s.scenery=scene;app.scene_signature=None
       for fps in (30,60):
        for frame in range(fps):app.anim_time=frame/fps;app.draw_scene()
        assert len(app.scene.find_all())<5000
        assert len(getattr(app,'reflection_frames',[]))<=12
       root.update();assert not errors,errors
       capture(root,Path('verification')/f'readability-{dimensions}-{size}-{mode}-{scene}.png')
     app.open_tome();root.update();assert app.tome_window.state()!='withdrawn'
     capture(app.tome_window,Path('verification')/f'tome-{dimensions}-{size}.png');app.close_tome()
     app.open_settings()
     for category in CATEGORIES:
      app.select_settings_category(category);root.update();assert not errors,errors
      capture(root,Path('verification')/f'settings-{dimensions}-{size}-{category}.png')
     app.close_settings()
   s.spirit_remaining=10;app.draw_scene();root.update()
   notice=next(e for e in app.scene.controls.entries if e['label'].startswith('Visitor arrived'))
   x,y,x2,y2=notice['rect'];x=int((x+x2)/2);y=int((y+y2)/2)
   app.scene.event_generate('<ButtonPress-1>',x=x,y=y);app.scene.event_generate('<ButtonRelease-1>',x=x,y=y);root.update()
   assert s.spirit_offer and s.spirit_remaining==0
   offer=s.spirit_offer[:];app.capture_spirit();assert s.spirit_offer==offer
   assert not errors,errors
   print('Live geometry, animation bounds and visitor notice pointer checks passed; inspect captures for visual quality.')
  finally:
   app.destroy()

if __name__=='__main__':verify()
