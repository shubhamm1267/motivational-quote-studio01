"""Local demo: creates distinct template samples without an API key."""
import sys, uuid
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from worker.editorial import TEMPLATES,render_editorial
from worker.main import paste_uploaded_icon

root=Path(__file__).resolve().parents[1]
out=root/'examples'/'editorial_v6';out.mkdir(parents=True,exist_ok=True)
texts=[
 ('You are not behind in life:', 'It is possible to start again without having the entire path mapped out. A setback can change your plans, but it does not get to decide your worth. You still have time to build something meaningful.', 'The next chapter is still yours to write.'),
 ('Life gets beautiful in quiet ways', 'Sometimes the smallest moments carry the most meaning. Someone remembering a detail. An evening without a rush. A conversation where you can finally be yourself.', 'Pay attention to what makes your day lighter.'),
 ('Discipline is choosing to return.', 'On difficult days you may not feel inspired, and that is okay. Build the kind of routine that makes room for the days when motivation is missing. Quiet repetition becomes trust in yourself.', 'One steady action counts more than a perfect plan.'),
 ('Dear self,', '', 'You do not have to make up for every slow day.'),
 ('A few gentle reminders:', '', 'Your feelings deserve curiosity, not judgment.'),
 ('Stop expecting everyone:', '', 'Choose people who make honesty feel safe.'),
 ('Little wins that matter:', '', 'Some of the greatest victories are ordinary.'),
 ('I read a thought that stayed with me…', 'You can love what a memory meant without living inside it. Some goodbyes are lessons, not invitations to return.', 'Tomorrow can still surprise you.'),
 ('Someone who speaks gently', 'Is not always the person who has had an easy life. Sometimes kindness is a skill that someone built through many difficult days. You never know how much strength it took to stay soft.', 'Gentleness is not weakness.'),
 ('A little positive thinking', 'Is not pretending everything is perfect. It is allowing one difficult moment to be real without letting it define the entire day. Look for what you can do next.', 'The next small step is enough.'),
 ('You have no idea', 'How much an ordinary kind gesture can matter to someone who has been carrying more than they say. Notice people. Say the good thing out loud. Let your care be visible.', 'Small kindness can travel a long way.'),
 ('Being left on read hurts', 'Not because you need everyone to reply immediately, but because uncertainty has a way of filling the silence with stories. Ask what you need to know. Then let actions give you clarity.', 'You deserve communication, not constant guessing.'),
 ('One of life’s rarest blessings', 'Is finding someone who celebrates your growth without needing to compete with it. They let you be both ambitious and tired. They make ordinary moments easier to carry.', 'Be grateful for those who feel like home.'),
 ('I had to learn this slowly:', 'Wanting a better future does not mean you have to dislike the life you have today. You can be grateful for what is here while working quietly toward what comes next.', 'Progress and peace can belong together.'),
 ('You never forget', 'The person who showed up during a difficult season without asking for an explanation. The little things matter. Consistency tells the truth more clearly than dramatic promises.', 'Remember the people who stayed kind.'),
 ('Someone asked: “What is strength?”', 'I thought about the people who choose to apologize, begin again, ask for help and stay kind after a hard day.', 'I answered: strength is being brave enough to remain human.'),
 ('As you grow older,', 'You become less interested in being understood by everyone. You choose people who listen. You forgive yourself for learning slowly. You make room for the kind of peace that never needs an announcement.', 'Maturity is knowing what deserves your energy.'),
 ('Some truths take time:', '', 'You are allowed to take responsibility and still treat yourself gently.')
]
points=['Time to rest is not wasted.','You can start over today.','One hard week is not your whole story.','An ordinary good day is worth celebrating.','Your peace is allowed to be a priority.','You do not have to earn every moment of joy.']
rows=[];fails=[]
iconpath=Path('/mnt/data/gold_sunrise_monogram_emblem.png');icon=Image.open(iconpath).convert('RGBA') if iconpath.exists() else None
for idx,(tpl,*_) in enumerate(TEMPLATES.items()):
 title,para,close=texts[idx]
 fmt=TEMPLATES[tpl][2]
 post={'headline':title,'detail':'','paragraphs':[{'text':para,'highlights':['next small step' if 'next small step' in para else 'smallest moments' if 'smallest moments' in para else 'an ordinary kind gesture' if 'an ordinary kind gesture' in para else 'quiet repetition' if 'quiet repetition' in para else '']}] if para else [],'items':points if fmt in ['list','letter','numbered'] else [],'closing':close,'highlights':[title.split(':')[0]+':' if ':' in title else title.split(' ').pop(0)+' '+title.split(' ')[1]]}
 try:
  outfile=out/f'{idx+1:02}_{tpl}.png'
  meta=render_editorial(post,'@everydayresetnotes','portrait',tpl,outfile,paste_uploaded_icon,icon)
  im=Image.open(outfile).convert('RGB')
  th=ImageOps.contain(im,(220,275)); t=Image.new('RGB',(244,320),'white');t.paste(th,((244-th.width)//2,0));ImageDraw.Draw(t).text((8,290),f'{idx+1:02} {tpl}',fill='black');rows.append(t)
  print('OK',idx+1,tpl,meta)
 except Exception as e: print('FAILED',idx+1,tpl,e);fails.append((tpl,str(e)))
if rows:
 sheet=Image.new('RGB',(6*244,((len(rows)+5)//6)*320),'white')
 for i,t in enumerate(rows):sheet.paste(t,((i%6)*244,(i//6)*320))
 sheet.save('/mnt/data/Editorial_v6_18_Templates_Preview.jpg',quality=92)
if fails:raise RuntimeError(failss if False else repr(fails))
