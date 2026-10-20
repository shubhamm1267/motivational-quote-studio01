// 18 distinct editorial formats correspond to the 18 user-supplied composition references.
// Layout is original; no pixel assets, existing watermark, or quotes are extracted from them.
export const TEMPLATES = Object.freeze([
  ['comeback','01 • Comeback Note','statement'],
  ['beauty','02 • Life Beauty Essay','essay'],
  ['discipline','03 • Discipline Lesson','essay'],
  ['dear_self','04 • Dear Self Letter','letter'],
  ['emotions','05 • Feelings Checklist','list'],
  ['expectations','06 • Boundaries List','list'],
  ['underrated','07 • Daily Wins Numbered','numbered'],
  ['book_quote','08 • Blush Poem','poem'],
  ['truth_teller','09 • Honest Insight','essay'],
  ['thinking','10 • Positive Thinking Centered','center'],
  ['heart','11 • Heartfelt Essay','essay'],
  ['ghosted','12 • Ghosting Truth','essay'],
  ['blessings','13 • Little Blessings','essay'],
  ['hard_truth','14 • Hard Truth','essay'],
  ['remember','15 • Never Forget','essay'],
  ['dialogue','16 • Question & Answer','dialogue'],
  ['maturity','17 • Maturity Lesson','essay'],
  ['wake_up','18 • Harsh Truth List','list']
].map(([id,label,format])=>({id,label,format})));

export const VALID_TEMPLATES = new Set(['auto','classic_dark',...TEMPLATES.map(t=>t.id)]);
const byFormat=Object.fromEntries(TEMPLATES.map(t=>[t.id,t.format]));
const BY_CATEGORY = {
  life:['beauty','underrated','maturity','hard_truth','wake_up','blessings'],
  motivation:['comeback','discipline','dear_self','blessings','thinking'],
  discipline:['discipline','underrated','wake_up'],
  healing:['dear_self','book_quote','heart','remember'],
  self:['expectations','thinking','comeback','remember'],
  relationships:['ghosted','heart','expectations','dialogue'],
  breakup:['ghosted','dear_self','book_quote','dialogue'],
  attitude:['expectations','truth_teller','maturity'],
  success:['discipline','comeback','underrated'],
  sad:['heart','ghosted','book_quote','truth_teller'],
  family:['blessings','heart','dear_self'],
  friendship:['expectations','ghosted','dialogue'],
  comedy:['dialogue','underrated','expectations'],
  study:['discipline','comeback','underrated'],
  gratitude:['underrated','blessings','dear_self'],
  maturity:['maturity','hard_truth','wake_up'],
  boundaries:['expectations','truth_teller','remember'],
  reality:['wake_up','hard_truth','ghosted'],
  affirmation:['dear_self','comeback','thinking'],
  positivity:['thinking','blessings','beauty']
};
let previousTemplate='';
export function chooseTemplate(wanted='auto',category='all') {
  if(wanted!=='auto' && VALID_TEMPLATES.has(wanted))return wanted;
  const available=BY_CATEGORY[category]||TEMPLATES.map(t=>t.id);
  const distinct=available.filter(t=>t!==previousTemplate);
  const pool=distinct.length?distinct:available;
  const choice=pool[Math.floor(Math.random()*pool.length)];
  previousTemplate=choice;
  return choice;
}
export function templateFormat(id){return byFormat[id]||'essay';}

// Useful locally when Gemini isn't supplied. The fallback is visibly labelled as local content.
const LOCAL_LINES={
  life:['The quiet mornings you never thought you would see again.','The friend who checks in without needing a reason.','The courage to change your mind.','An ordinary day when you finally feel like yourself.','A little room to start over.','The peace of not having to prove anything.','A meal you did not have to rush.','The freedom to change your mind.','A quiet apology that comes with changed behavior.','Having enough energy to try again.'],
  motivation:['Show up before you feel ready.','Start with what you can control.','Keep your promises to yourself.','Be willing to begin badly.','Celebrate progress you cannot post online.','Try again after a hard day.'],
  self:['You can say no without writing an apology.','Your time deserves protection.','A healthy boundary can be a kind response.','You do not need an audience to grow.','Trust the person you are becoming.'],
  relationships:['Notice the way people treat your boundaries.','A sincere apology comes with changed behavior.','You can care and still choose distance.','Respect should not be a special occasion.','A real connection makes room for honesty.'],
  healing:['Some days healing is getting out of bed.','Some days it is saying what you really feel.','Rest is not a failure.','You can miss a person and protect your peace.','Progress is rarely a straight line.'],
  comedy:['Opening the fridge for the third time.','Making a to-do list instead of doing the list.','Saying “five more minutes” every morning.','Treating Friday like a personal achievement.','Pretending an unread email does not exist.'],
};
const LOCAL_PARA={
  life:'Growing older does not mean having everything figured out. Sometimes it means becoming gentle with the parts of yourself that are still learning. A peaceful afternoon, an honest conversation and the choice to begin again are victories worth noticing.',
  motivation:'You do not have to feel fearless to make progress. Confidence usually arrives after the first uncomfortable step, not before it. Do the small thing today. Give tomorrow a reason to thank you.',
  self:'People will always have opinions about how you should live. Your job is not to earn every person’s approval. Your job is to build a life that feels honest when the room is quiet.',
  relationships:'A healthy relationship does not demand that you become smaller to keep the peace. It gives you room to speak openly, make mistakes and feel safe enough to be yourself.',
  healing:'There will be days when your old life feels close enough to touch. Let the memories visit without asking them to stay. You can honor what happened and still choose a different future.',
  comedy:'Adulthood is a strange place. We celebrate finding a parking spot, get excited about clean bedsheets and spend our weekends recovering from the week. Somehow, that counts as a personality now.'
};
export function enrichLocalPost(post,category,templateId,language='en'){
  const cat=LOCAL_LINES[category]?category:(['breakup','sad'].includes(category)?'healing':'life');
  const fmt=templateFormat(templateId);
  const base=post.headline||'Give yourself room to grow.';
  const detail=post.detail||'';
  const lines=LOCAL_LINES[cat];
  const paragraph=LOCAL_PARA[cat];
  const shortTitle=base.length>90?base.slice(0,86).replace(/\s+\S*$/,'')+'…':base;
  if(language==='hi')return {...post,paragraphs:[{text:detail}],items:[],closing:detail,highlights:[],template:templateId};
  let title=shortTitle;
  let items=[];
  let paragraphs=[];
  let closing='';
  if(['list','numbered','letter'].includes(fmt)){
    title= fmt==='letter'?'Dear self, remember this:':(fmt==='numbered'?'Little wins that count:':(category==='relationships'?'Stop settling for this:':'Small reminders for today:'));
    items=lines.slice(0,fmt==='numbered'?10:(fmt==='letter'?8:6));
    closing=detail||'You deserve a little credit for getting this far.';
  } else if(fmt==='dialogue'){
    title='Someone asked me: “What really matters?”';
    paragraphs=[{text:'I thought about the way we spend our days trying to impress people who barely know us.',highlights:['trying to impress people']}];
    closing='My answer: a peaceful mind, honest love and the courage to be yourself.';
  } else if(fmt==='poem'){
    title='A quiet reminder…';
    paragraphs=[{text:'You can love the memories without returning to what hurt you.'},{text:'You can feel uncertain and still take the next step.'}];
    closing='Give yourself permission to begin again.';
  } else {
    title=base.length>95?'Something worth remembering:':base;
    paragraphs=[{text:paragraph,highlights:[]}];
    closing=detail&&detail!==title?detail:'';
  }
  const highlightSource= title.includes(':')?title.split(':')[0]+':':(title.split(' ').slice(0,Math.min(5,title.split(' ').length)).join(' '));
  const highlighted=paragraphs.length?(paragraphs[0].text.split('.').filter(x=>x.length>20)[0]||'').trim():'';
  return {...post,headline:title,paragraphs,items,closing,highlights:[highlightSource,...(highlighted?[highlighted.slice(0,90)]:[])],template:templateId};
}
