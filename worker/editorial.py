
"""18 original editorial layouts inspired by user supplied design references.

No reference images / watermarks are copied. Layout, palette and type rendering
are procedural; quoted content is new, with user-controlled brand overlay.
"""
from __future__ import annotations
import hashlib, math, random, re, shutil, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, features

# Each variant changes composition, type sizes, alignment, typography, paper palette,
# and highlight placement; not simply a hue filter over one generic quote card.
TEMPLATES = {
 'comeback':     ('You Can Come Back',  'cloud','statement','top',       'mixed'),
 'beauty':       ('Beauty of Life',     'cloud','essay',    'mid',       'body'),
 'discipline':   ('Discipline Essay',   'cloud','essay',    'mid',       'mixed'),
 'dear_self':    ('Dear Self Letter',   'sand', 'letter',   'top',       'close'),
 'emotions':     ('Feelings Decoder',   'sand', 'list',     'top',       'title'),
 'expectations': ('Expectations List',  'sand', 'list',     'top',       'mixed'),
 'underrated':   ('Everyday Wins',      'cloud','numbered','top',       'title'),
 'book_quote':   ('Book Quote Poem',    'blush','poem',     'mid',       'title'),
 'truth_teller': ('Honest Insight',     'sand', 'essay',    'top',       'title'),
 'thinking':     ('Positive Thinking', 'blush','center',   'mid',       'body'),
 'heart':        ('Heartfelt Essay',    'sand', 'essay',    'top',       'title'),
 'ghosted':      ('Relationship Truth','sand', 'essay',    'top',       'mixed'),
 'blessings':    ('Little Blessings',   'sand', 'essay',    'mid',       'mixed'),
 'hard_truth':   ('Hard Truth Story',   'sand', 'essay',    'top',       'title'),
 'remember':     ('Remember This',     'sand', 'essay',    'top',       'body'),
 'dialogue':     ('Question & Answer',  'blush','dialogue','mid',       'title'),
 'maturity':     ('As You Mature',      'sand', 'essay',    'top',       'title'),
 'wake_up':      ('Wake-Up Reality',    'cloud','list',    'top',       'title'),
}
PALETTES = {
 'cloud': ((244,240,241),(228,222,227),(241,236,238)),
 'sand':  ((244,213,185),(236,202,171),(245,224,200)),
 'blush': ((249,189,170),(244,169,150),(253,202,183)),
}
YELLOW=(246,239,59,255)
# Render feed posts at 2x logical resolution; video artworks remain native 1080x1920.
POST_EXPORT_SCALE=2
INK=(18,17,16,255)

_FONT_PATHS={}
def editorial_font(size:int,bold:bool=False,hindi:bool=False):
    """Uses installed system typefaces. No restricted font files are bundled."""
    key=(bold,hindi)
    if key not in _FONT_PATHS:
        candidates=[]
        if __import__('os').name=='nt':
            names=(['NirmalaB.ttf','Nirmala.ttf','mangal.ttf'] if hindi else
                    (['georgiab.ttf','timesbd.ttf','Georgia.ttf','times.ttf'] if bold else ['Georgia.ttf','times.ttf','georgiab.ttf']))
            candidates=[str(Path('C:/Windows/Fonts')/f) for f in names]
        else:
            families=(['Noto Serif Devanagari','Noto Sans Devanagari'] if hindi else
                (['Liberation Serif:style=Bold','DejaVu Serif:style=Bold','EB Garamond'] if bold else
                 ['Liberation Serif','EB Garamond','DejaVu Serif']))
            if shutil.which('fc-match'):
                for family in families:
                    try:
                        p=subprocess.run(['fc-match','-f','%{file}',family],capture_output=True,text=True,timeout=3).stdout.strip()
                        if p:candidates.append(p)
                    except Exception:pass
        _FONT_PATHS[key]=next((f for f in candidates if Path(f).exists()),'')
    if not _FONT_PATHS[key]:
        raise RuntimeError('An installed serif font is required: Windows Georgia or open-source EB Garamond / Liberation Serif.')
    options={'layout_engine':ImageFont.Layout.RAQM} if features.check('raqm') else {}
    return ImageFont.truetype(_FONT_PATHS[key],size,**options)

def paper_background(size,kind,seed):
    # Low-frequency handmade-paper texture; deterministic and fast enough for a worker.
    w,h=size
    a,b,c=PALETTES[kind]
    sm=Image.new('RGB',(max(1,w//10),max(1,h//10)))
    p=sm.load(); r=random.Random(seed)
    for yy in range(sm.height):
        for xx in range(sm.width):
            t=yy/max(1,sm.height-1)
            base=[round(a[i]*(1-t)+c[i]*t) for i in range(3)]
            n=r.randint(-13,13)
            p[xx,yy]=tuple(max(0,min(255,v+n)) for v in base)
    sm=sm.resize(size,Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(11))
    # Slightly uneven warm parchment tint / light-corner airbrush, not a flat solid.
    haze=Image.new('RGBA',size,(255,255,255,0))
    hd=ImageDraw.Draw(haze,'RGBA')
    hd.ellipse((-w//3,-h//5,int(w*.9),int(h*.65)),fill=(255,255,255,14))
    haze=haze.filter(ImageFilter.GaussianBlur(95))
    return Image.alpha_composite(sm.convert('RGBA'),haze).convert('RGB')

def clean(s,limit=600):
    return re.sub(r'\s+',' ',str(s or '')).strip()[:limit]

def highlight_flags(s, phrases):
    mask=[False]*len(s)
    for phrase in phrases:
        phrase=clean(phrase,105)
        if len(phrase)<3: continue
        start=0
        while True:
            idx=s.casefold().find(phrase.casefold(),start)
            if idx<0:break
            for j in range(idx,min(len(s),idx+len(phrase))):mask[j]=True
            start=idx+len(phrase)
    return mask

def text_width(draw,tx,font):
    return draw.textlength(tx,font=font)

def wrapped_tokens(draw,s,font,width,phrases):
    s=clean(s,1350)
    # Word index is kept so highlight rectangles are precisely aligned with marked spans.
    flags=highlight_flags(s,phrases)
    words=[]
    for m in re.finditer(r'\S+',s):
        word=m.group()
        if text_width(draw,word,font)>width:
            raise ValueError('A word is too wide for the available layout')
        words.append((word,any(flags[m.start():m.end()])))
    lines=[];line=[]; content=''
    for word,hl in words:
        candidate=(content+' '+word).strip()
        if text_width(draw,candidate,font)>width and line:
            lines.append(line);line=[];content=''
        line.append((word,hl));content=(content+' '+word).strip()
    if line:lines.append(line)
    return lines

def paint_line(d,line,x,y,font,sz,alignment='left',accent=True):
    """Full-glyph-height highlighter, drawn *behind* the complete marked words.

    Pillow positions a font's top differently from the nominal font size.
    Using fixed y + 0.2 * font_size rectangles clipped descenders and made
    highlighted words look only half covered. Use actual text bounds instead.
    """
    text=' '.join(word for word,_ in line)
    if not text:
        return
    total=text_width(d,text,font)
    if alignment=='center':
        x-=total/2
    # Sample includes high capitals/accents and below-baseline glyphs. The full
    # height is constant for all highlights in one line to avoid jagged blocks.
    bbox=d.textbbox((0,0),'ÁÉAjgpqy',font=font)
    pad=max(2,round(sz*.055))
    top=round(y+bbox[1]-pad)
    bottom=round(y+bbox[3]+pad)
    space=text_width(d,' ',font)
    cx=x
    run_start=None
    run_end=None
    if accent:
        for word,marked in line:
            right=cx+text_width(d,word,font)
            if marked:
                if run_start is None:
                    run_start=cx
                run_end=right
            elif run_start is not None:
                d.rectangle((round(run_start-pad),top,round(run_end+pad),bottom),fill=YELLOW)
                run_start=None
                run_end=None
            cx=right+space
        if run_start is not None:
            d.rectangle((round(run_start-pad),top,round(run_end+pad),bottom),fill=YELLOW)
    d.text((round(x),round(y)),text,font=font,fill=INK,stroke_width=0)

def render_textblock(d,lines,x,y,font,size,line_step,alignment='left'):
    for line in lines:
        paint_line(d,line,x,y,font,size,alignment)
        y+=line_step
    return y

def normalized_post(post,template_id):
    """Renderer accepts legacy headline/detail plus rich Gemini JSON fields."""
    title=clean(post.get('headline') or 'A small reminder',250)
    desc=clean(post.get('detail'),300)
    raw=post.get('paragraphs',[])
    if not isinstance(raw,list):raw=[]
    paragraphs=[]
    for obj in raw[:6]:
        if isinstance(obj,dict):
            text=clean(obj.get('text'),420)
            h=obj.get('highlights',[])
            ph=[clean(x,100) for x in h[:4]] if isinstance(h,list) else []
        else:text=clean(obj,420);ph=[]
        if text:paragraphs.append((text,ph))
    items=post.get('items',[])
    if not isinstance(items,list):items=[]
    items=[clean(obj,140) for obj in items[:12] if isinstance(obj,str) and clean(obj)]
    quote=clean(post.get('closing') or desc,230)
    highs=post.get('highlights',[])
    if not isinstance(highs,list):highs=[]
    highs=[clean(x,110) for x in highs[:8] if isinstance(x,str)]
    # Permit Gemini to specify literal target highlights: title or body.
    if not paragraphs and desc: paragraphs=[(desc,[])]
    return title,paragraphs,items,quote,highs

def choose_template(requested='auto',post=None):
    if requested in TEMPLATES:return requested
    if post and post.get('template') in TEMPLATES:return post['template']
    return random.choice(list(TEMPLATES))

def compute_layout(d,blocks,x,width,bounds_h,position,centered,hindi,scale=1):
    """Fit all text segments AS A GROUP, avoiding cutoffs and overlaps."""
    title,paras,items,closing,highs=blocks
    fmt=position
    title_hi=[p for p in highs if p.casefold() in title.casefold()]
    kind=fmt
    if kind in ('numbered','list','letter') and not items:
        items=[p[0] for p in paras] if paras else ([closing] if closing else [])
        paras=[]
    elif kind not in ('numbered','list','letter') and not paras and items:
        paras=[(' '.join(items),[])]
        items=[]
    title_candidates=[int(n*scale) for n in (78,74,70,66,62,58,54,50,46,42)]
    if len(title)>82:title_candidates=title_candidates[2:]
    if hindi:title_candidates=[int(x*.88) for x in title_candidates]
    for tit_sz in title_candidates:
        font_t=editorial_font(tit_sz,True,hindi)
        try:title_lines=wrapped_tokens(d,title,font_t,width,title_hi)
        except ValueError:continue
        if len(title_lines)>5:continue
        paragraph_sizes=([n*scale for n in range(43,25,-2)] if not hindi else [n*scale for n in range(37,23,-2)])
        if len(items)>8: paragraph_sizes=[n*scale for n in (35,33,31,29,27,25)]
        for body_sz in paragraph_sizes:
            bodyfont=editorial_font(body_sz,False,hindi)
            try:
                paragraph_lines=[wrapped_tokens(d,t,bodyfont,width,[*hi,*highs]) for t,hi in paras]
                list_lines=[wrapped_tokens(d,t,bodyfont,width-55*scale,highs) for t in items]
                endfont=editorial_font(max(27*scale,body_sz-scale),False,hindi)
                endlines=wrapped_tokens(d,closing,endfont,width,highs) if closing and (not paras or closing not in [p[0] for p in paras]) else []
            except ValueError:continue
            if any(len(ls)>7 for ls in paragraph_lines) or any(len(ls)>4 for ls in list_lines):continue
            body_step=int(body_sz*1.31)
            title_step=int(tit_sz*1.14)
            tp=title_step*len(title_lines)
            bp=sum(body_step*len(lines)+round(body_sz*.40) for lines in paragraph_lines)
            lp=sum(body_step*len(lines)+int(body_sz*.28) for lines in list_lines)
            extra=body_step*len(endlines)+int(body_sz*.28) if endlines else 0
            total=tp+round(body_sz*.9)+bp+lp+extra
            if total<=bounds_h:
                return (font_t,tit_sz,title_lines,title_step,bodyfont,body_sz,paragraph_lines,list_lines,endfont,endlines,body_step,total)
    raise ValueError(f'Text does not fit reference template: reduce length ({len(title)} title chars, {sum(len(p[0]) for p in paras)} paragraph chars, {len(items)} items).')

def render_editorial(post,handle,size,template_id,output_path,icon_paster=None,icon=None):
    tpl=choose_template(template_id,post)
    label,paper,kind,placement,accent=TEMPLATES[tpl]
    # Post images: true 2x font rendering, not upscaled 1080px pixels.
    # Reels: 1080x1920 native frame to avoid excessive encoder memory on Render.
    scale=1 if size=='reel' else POST_EXPORT_SCALE
    bw,bh={'portrait':(1080,1350),'square':(1080,1080),'reel':(1080,1920)}.get(size,(1080,1350))
    w,h=bw*scale,bh*scale
    # Stable per-template seed; different textures between samples, no source image baked in.
    seed=int(hashlib.sha256((tpl+str(post.get('headline',''))).encode()).hexdigest()[:8],16)
    im=paper_background((w,h),paper,seed)
    d=ImageDraw.Draw(im,'RGBA')
    x=130*scale if kind not in ('center','dialogue') else 165*scale
    width=w-2*x
    align='center' if kind in ('center','dialogue','poem') else 'left'
    if align=='center':x=w//2
    # Existing corner handle and bottom-center uploaded logo remain the branding.
    handle=clean(handle,40)
    if handle:
        hf=editorial_font(23*scale,False,False)
        d.text((66*scale,68*scale),handle,font=hf,fill=(71,65,62,156))
    logo_space=(190 if icon is not None else 100)*scale
    y_top=(240 if size=='reel' else (155 if size=='portrait' else 130))*scale
    content_h=min(h-y_top-logo_space-54*scale, 1300*scale if size=='reel' else h)
    title,paras,items,closing,highs=normalized_post(post,tpl)
    # Never draw beyond the output canvas. Attempt a sequence of readable fits.
    # On very short square canvases, omit secondary text with an explicit warning.
    shortened=False
    for retry in range(18):
        try:
            fit=compute_layout(d,(title,paras,items,closing,highs),x,width,content_h,kind,align=='center',bool(re.search('[\u0900-\u097F]',title+closing)),scale)
            break
        except ValueError:
            if len(items)>4:
                items=items[:-1]
            elif len(paras)>1:
                paras=paras[:-1]
            elif len(paras)==1 and len(paras[0][0])>110:
                para,marks=paras[0]
                para=para[:max(105,int(len(para)*.84))].rsplit(' ',1)[0].rstrip(',;: ')+'.'
                paras=[(para,marks)]
            elif closing:
                closing=''
            elif len(title)>85:
                title=title[:85].rsplit(' ',1)[0]+'…'
            else:
                raise
            shortened=True
    else:
        raise ValueError('Poster copy is too long for a readable layout')
    ft,ts,tls,tstep,fb,bs,pls,ils,fc,cls,bstep,total=fit
    y= (y_top+max(10*scale,(content_h-total)//2)) if placement=='mid' else y_top
    if placement=='top' and total>content_h*.82:
        y+=18*scale
    # Background highlights exactly behind the selected words, not the entire paragraph.
    y=render_textblock(d,tls,x,y,ft,ts,tstep,align)
    y+=round(bs*.9)
    if kind in ('list','numbered','letter') and items:
        if not ils:ils=[wrapped_tokens(d,s,fb,width-55*scale,highs) for s in items]
        for idx,lines in enumerate(ils):
            prefix=(f'{idx+1}. ' if kind=='numbered' else '– ')
            pf=fb
            indent=text_width(d,prefix,pf)
            left=x if align=='left' else w//2-width//2
            d.text((round(left),round(y)),prefix,font=pf,fill=INK)
            # wrap list text with hanging indentation; no text may collide with prefix
            yy=render_textblock(d,lines,left+indent,y,fb,bs,bstep,'left')
            y=yy+int(bs*.3)
    else:
        for lines in pls:
            y=render_textblock(d,lines,x,y,fb,bs,bstep,align)
            y+=int(bs*.42)
    if cls:
        y+=int(bs*.28)
        render_textblock(d,cls,x,y,fc,max(27*scale,bs-scale),bstep,align)
    if icon is not None and icon_paster is not None:
        # Reuses unchanged bottom-center uploaded icon positioning logic.
        icon_paster(im,icon,'editorial')
    # If icon is absent, no replacement/foreign brand watermark is fabricated.
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    im.save(output_path,optimize=True)
    return {'template':tpl,'family':paper,'format':kind,'layout':label,'copyShortened':shortened,'resolution':[w,h]}
