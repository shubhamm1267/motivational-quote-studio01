
"""QuoteCraft: dark motivational quote poster + optional effect Shorts renderer."""
from __future__ import annotations
import base64, io, json, os, random, re, shutil, subprocess
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, features
if __package__:
    from .editorial import render_editorial, TEMPLATES as EDITORIAL_TEMPLATES
else:
    from editorial import render_editorial, TEMPLATES as EDITORIAL_TEMPLATES

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
app=FastAPI(title='QuoteCraft Poster Rendering Worker')

class RenderRequest(BaseModel):
    jobId: str
    post: dict
    brand: str='Quote Craft'
    handle: str='@yourpage'
    style: Literal['midnight','editorial','sunset']='midnight'
    size: Literal['portrait','square']='portrait'
    withVideo: bool=False
    videoSeconds: int=Field(5,ge=5,le=10)
    effectEnabled: bool=False
    effectStyle: Literal['none','reference','softGlow','float']='none'
    imageMode: Literal['commons','illustration','upload']='illustration'
    imageDataUrl: str=''
    iconDataUrl: str=''
    template: str='auto'

THEMES={
 'midnight':{'bg':'#060606','primary':'#fafafa','sub':'#dcdcdc','accent':'#e4c36a'},
 'editorial':{'bg':'#101010','primary':'#ffffff','sub':'#d7d7d7','accent':'#c9c9c9'},
 'sunset':{'bg':'#0b0b0f','primary':'#fff8ef','sub':'#ead9c8','accent':'#d5b06a'}
}
_FONT_CACHE={}

def font_path(hindi=True,bold=True):
    key=(hindi,bold)
    if key in _FONT_CACHE:return _FONT_CACHE[key]
    if os.name=='nt':
        names=['NirmalaB.ttf','Nirmala.ttf','mangalb.ttf','mangal.ttf'] if hindi else ['georgiab.ttf','Georgia.ttf','timesbd.ttf','times.ttf','arialbd.ttf','arial.ttf']
        for name in names:
            p=Path('C:/Windows/Fonts')/name
            if p.exists():_FONT_CACHE[key]=str(p);return str(p)
    else:
        if shutil.which('fc-match'):
            family='Noto Sans Devanagari:style=Bold' if hindi and bold else 'Noto Sans Devanagari' if hindi else 'DejaVu Serif:style=Bold'
            p=subprocess.run(['fc-match','-f','%{file}\n',family],capture_output=True,text=True).stdout.strip().splitlines()[0]
            if Path(p).exists():_FONT_CACHE[key]=p;return p
    raise RuntimeError('Unicode font not found. Install Noto Sans Devanagari or Windows Nirmala UI.')

def get_font(px:int,hindi=True,bold=True):
    opts={'layout_engine':ImageFont.Layout.RAQM} if features.check('raqm') else {}
    return ImageFont.truetype(font_path(hindi,bold),px,**opts)

def clean_text(txt:str,limit:int=340):
    return re.sub(r'\s+',' ',str(txt or '')).strip()[:limit]

def text_width(draw,txt,font):
    return draw.textbbox((0,0),txt,font=font)[2]

def wrap_lines(draw,txt,font,max_width,max_lines=9):
    words=clean_text(txt,520).split(' ')
    if not words:return []
    lines=[]; line=''
    for word in words:
        candidate=(line+' '+word).strip()
        if text_width(draw,candidate,font)<=max_width:
            line=candidate
        else:
            if line:
                lines.append(line); line=word
            else:
                lines.append(word); line=''
    if line: lines.append(line)
    if len(lines)>max_lines:return None
    return lines

def fit_lines(draw,txt,max_width,max_height,initial=76,minsize=28,spacing=1.26,max_lines=8,hindi=True,scale=1):
    for size in range(initial,minsize-1,-2*scale):
        font=get_font(size,hindi,True)
        lines=wrap_lines(draw,txt,font,max_width,max_lines)
        if not lines: continue
        box_height=int(size*spacing*len(lines))
        if box_height<=max_height and all(text_width(draw,l,font)<=max_width for l in lines):
            return font,lines,int(size*spacing)
    raise ValueError('Text too long for poster')

def fit_support_lines(draw,txt,max_width,max_height,hindi=True,scale=1):
    txt=clean_text(txt,180)
    if not txt:return None,[],0
    for size in range(34*scale,19*scale,-2*scale):
        font=get_font(size,hindi,False)
        lines=wrap_lines(draw,txt,font,max_width,4)
        if not lines: continue
        step=int(size*1.28)
        if step*len(lines)<=max_height:
            return font,lines,step
    font=get_font(20*scale,hindi,False)
    lines=wrap_lines(draw,txt[:120],font,max_width,4) or [txt[:120]]
    return font,lines,int(20*scale*1.28)

def make_texture(size,theme):
    w,h=size
    bg=Image.new('RGB',size,THEMES[theme]['bg'])
    px=bg.load()
    random.seed(w*h)
    for y in range(h):
        for x in range(w):
            noise=random.randint(-10,10)
            base=max(0,min(255,9+noise + int(20*(1-abs((x-w/2)/(w/2))*0.38)) + int(16*(1-abs((y-h/2)/(h/2))*0.34))))
            if theme=='editorial': rgb=(base+10,base+10,base+10)
            elif theme=='sunset': rgb=(base+7,base+4,base)
            else: rgb=(base,base,base)
            px[x,y]=rgb
    bg=bg.filter(ImageFilter.GaussianBlur(0.35))
    vignette=Image.new('L',size,0)
    vd=ImageDraw.Draw(vignette)
    for i in range(18):
        margin=int(i*14)
        alpha=max(0,145-i*8)
        vd.rectangle((margin,margin,w-margin,h-margin),outline=alpha,width=24)
    bg=Image.composite(Image.new('RGB',size,(0,0,0)),bg,vignette)
    return bg

def decode_icon(dataurl:str):
    if not dataurl: return None
    if not dataurl.startswith(('data:image/png;base64,','data:image/jpeg;base64,','data:image/webp;base64,')):
        raise ValueError('Invalid icon upload')
    raw=base64.b64decode(dataurl.split(',',1)[1],validate=True)
    if len(raw)>3_000_000: raise ValueError('Icon exceeds 3 MB')
    im=Image.open(io.BytesIO(raw)); im.load()
    return im.convert('RGBA')

def circle_crop_icon(icon:Image.Image, diameter:int)->Image.Image:
    fitted=ImageOps.fit(icon,(diameter,diameter),method=Image.Resampling.LANCZOS,centering=(0.5,0.5)).convert('RGBA')
    mask=Image.new('L',(diameter,diameter),0)
    md=ImageDraw.Draw(mask)
    md.ellipse((0,0,diameter-1,diameter-1),fill=255)
    fitted.putalpha(mask)
    return fitted

def paste_uploaded_icon(base:Image.Image, icon:Image.Image, theme:str):
    # Same bottom-center placement and existing framing; proportional at 2x photo export.
    w,h=base.size
    scale=w/1080
    t=THEMES[theme]
    diameter=round((82 if h/w>1.15 else 74)*scale)
    rim=round(8*scale)
    outer=diameter+rim*2
    framed=Image.new('RGBA',(outer,outer),(0,0,0,0))
    fd=ImageDraw.Draw(framed)
    fd.ellipse((0,0,outer-1,outer-1),fill=(0,0,0,220),outline=t['accent'],width=max(2,round(2*scale)))
    circ=circle_crop_icon(icon,diameter)
    framed.paste(circ,(rim,rim),circ)
    x=(w-outer)//2
    # Keep the original 160px/148px relative bottom margin.
    y=h-round((160 if h/w>1.15 else 148)*scale)
    base.paste(framed,(x,y),framed)

def draw_poster(post,brand,handle,style,size,directory,icon:Image.Image|None=None):
    scale=2  # Full-resolution image export, including the legacy dark template.
    bw,bh=(1080,1350) if size=='portrait' else (1080,1080)
    w,h=bw*scale,bh*scale
    # Background is an intentionally soft texture; type is natively rasterized at 2x.
    image=make_texture((bw,bh),style).resize((w,h),Image.Resampling.BICUBIC)
    d=ImageDraw.Draw(image,'RGBA')
    t=THEMES[style]
    handle_text=clean_text(handle,40)
    d.text((70*scale,72*scale),handle_text,font=get_font(28*scale,False,False),fill=(230,230,230,185))
    quote=clean_text(post.get('headline',''),280)
    detail=clean_text(post.get('detail',''),140)
    eyebrow=clean_text(post.get('eyebrow',''),28)
    hindi=bool(re.search('[\u0900-\u097F]',quote+detail+eyebrow))
    top_reserved=170*scale
    bottom_reserved=(220 if icon is not None else 120)*scale
    available_h=h-top_reserved-bottom_reserved
    max_quote_h=int(available_h*0.7)
    max_detail_h=max(54*scale, available_h-max_quote_h-40*scale)
    qfont, qlines, qstep = fit_lines(d, quote, w-170*scale, max_quote_h, initial=(78 if not hindi else 72)*scale, minsize=30*scale, max_lines=8, hindi=hindi,scale=scale)
    dfont, dlines, dstep = fit_support_lines(d, detail, w-220*scale, max_detail_h, hindi=hindi,scale=scale)
    eb_font=get_font(24*scale,False,False) if eyebrow else None
    eb_gap=58*scale if eyebrow else 0
    detail_gap=24*scale if dlines else 0
    block_h=(qstep*len(qlines)) + detail_gap + (dstep*len(dlines)) + eb_gap
    y=top_reserved + max(0,(available_h-block_h)//2)
    if eyebrow:
        d.text((w//2,y),eyebrow.upper(),font=eb_font,fill=(228,228,228,210),anchor='mm')
        y+=eb_gap
    for line in qlines:
        d.text((w//2,y),line,font=qfont,fill=t['primary'],anchor='ma')
        y+=qstep
    if dlines:
        y+=detail_gap
        for line in dlines:
            d.text((w//2,y),line,font=dfont,fill=(222,222,222,215),anchor='ma')
            y+=dstep
    if icon is not None:
        paste_uploaded_icon(image,icon,style)
    file=directory/'poster.png'
    image.save(file,optimize=True)
    return file

def make_smoke_overlay(path:Path):
    w,h=1080,1920
    img=Image.new('RGBA',(w,h),(0,0,0,0))
    dr=ImageDraw.Draw(img,'RGBA')
    random.seed(17)
    for _ in range(18):
        x=random.randint(-120,w-90)
        y=random.randint(0,h)
        ww=random.randint(180,420)
        hh=random.randint(105,270)
        alpha=random.randint(14,32)
        dr.ellipse((x,y,x+ww,y+hh),fill=(255,255,255,alpha))
    for _ in range(12):
        x=random.randint(-60,w-150)
        y=random.randint(h-420,h-60)
        ww=random.randint(270,570)
        hh=random.randint(75,180)
        alpha=random.randint(18,38)
        dr.ellipse((x,y,x+ww,y+hh),fill=(245,245,245,alpha))
    img=img.filter(ImageFilter.GaussianBlur(42))
    img.save(path)

def make_glow_overlay(path:Path, style:str):
    w,h=1080,1920
    img=Image.new('RGBA',(w,h),(0,0,0,0))
    d=ImageDraw.Draw(img,'RGBA')
    accent=THEMES[style]['accent']
    rgb=tuple(int(accent[i:i+2],16) for i in (1,3,5))
    d.ellipse((-120,60,360,540),fill=(*rgb,28))
    d.ellipse((750,1380,1290,1920),fill=(*rgb,24))
    img=img.filter(ImageFilter.GaussianBlur(66))
    img.save(path)

def prepare_shorts_frame(poster_path:Path,out_dir:Path):
    poster=Image.open(poster_path).convert('RGB')
    canvas=Image.new('RGB',(1080,1920),(8,8,8))
    fitted=ImageOps.contain(poster,(1080,1920),method=Image.Resampling.LANCZOS)
    x=(1080-fitted.width)//2
    y=(1920-fitted.height)//2
    canvas.paste(fitted,(x,y))
    frame_path=out_dir/'shorts_frame.png'
    canvas.save(frame_path)
    return frame_path

def render_video_shorts(poster_path:Path, duration:int, out_dir:Path, effect_style:str='none', theme_style:str='midnight'):
    if not shutil.which('ffmpeg'):
        raise RuntimeError('FFmpeg not found in PATH. Install FFmpeg to export MP4 videos.')
    frame_path=prepare_shorts_frame(poster_path,out_dir)
    out_mp4=out_dir/'reel.mp4'
    if effect_style=='none':
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',str(frame_path),'-t',str(duration),'-r','30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out_mp4)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    else:
        smoke=out_dir/'smoke.png'; glow=out_dir/'glow.png'
        make_smoke_overlay(smoke); make_glow_overlay(glow,theme_style)
        if effect_style=='reference':
            filt=(
                "[0:v]trim=duration={d},setpts=PTS-STARTPTS[tmp1];"
                "[tmp1][1:v]overlay=x='0':y='7*sin(t*0.7)':format=auto[tmp2];"
                "[tmp2][2:v]overlay=0:0:format=auto,eq=contrast=1.01:brightness=0.005:saturation=1.01,format=yuv420p[v]"
            ).format(d=duration)
        elif effect_style=='softGlow':
            filt=(
                "[0:v]trim=duration={d},setpts=PTS-STARTPTS[tmp1];"
                "[tmp1][2:v]overlay=0:0[tmp2];"
                "[tmp2]eq=contrast=1.02:brightness=0.01:saturation=1.03,format=yuv420p[v]"
            ).format(d=duration)
        else:  # float
            filt=(
                "[0:v]trim=duration={d},setpts=PTS-STARTPTS[tmp1];"
                "[tmp1][1:v]overlay=x='0':y='6*sin(t*1.2)':format=auto[tmp2];"
                "[tmp2][2:v]overlay=0:0,format=yuv420p[v]"
            ).format(d=duration)
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
             '-loop','1','-i',str(frame_path),
             '-loop','1','-i',str(smoke),
             '-loop','1','-i',str(glow),
             '-filter_complex',filt,
             '-map','[v]','-t',str(duration),'-r','30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out_mp4)]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    if result.returncode!=0:
        raise RuntimeError('FFmpeg video render failed: '+result.stderr[-800:])
    if not out_mp4.exists() or out_mp4.stat().st_size<8000:
        raise RuntimeError('MP4 render failed or file is too small.')
    return out_mp4

def render(payload:RenderRequest):
    if not re.fullmatch(r'[0-9a-f-]{36}',payload.jobId):
        raise ValueError('Invalid job id')
    folder=OUT/payload.jobId
    folder.mkdir(exist_ok=True)
    warnings=[]
    icon=decode_icon(payload.iconDataUrl) if payload.iconDataUrl else None
    template_id=payload.template
    if template_id != 'classic_dark':
        # Unknown or missing choice fails over to a known non-dark reference template.
        if template_id not in EDITORIAL_TEMPLATES: template_id='comeback'
        poster_path=folder/'poster.png'
        details=render_editorial(payload.post,payload.handle,payload.size,template_id,poster_path,paste_uploaded_icon,icon)
    else:
        details={'template':'classic_dark','format':'quote','layout':'Original Dark Poster'}
        poster_path=draw_poster(payload.post,payload.brand,payload.handle,payload.style,payload.size,folder,icon)
    if details.get('copyShortened'):
        warnings.append('Some secondary copy was shortened to keep the poster readable without clipping. Choose portrait for long lists.')
    assets={'poster':f'/output/{payload.jobId}/poster.png','credits':f'/output/{payload.jobId}/credits.txt','metadata':f'/output/{payload.jobId}/metadata.json'}
    chosen_effect = payload.effectStyle if payload.effectEnabled else 'none'
    if payload.withVideo:
        reel_art=poster_path
        if template_id != 'classic_dark':
            # Reflow the exact text/highlights on native 9:16 paper, not black bars.
            reel_art=folder/'reel_artwork.png'
            render_editorial(payload.post,payload.handle,'reel',template_id,reel_art,paste_uploaded_icon,icon)
        render_video_shorts(reel_art,payload.videoSeconds,folder,chosen_effect,payload.style)
        assets['reel']=f'/output/{payload.jobId}/reel.mp4'

    # Python 3.11-compatible: compute the language BEFORE interpolating it in an f-string.
    # Avoid backslashes inside f-string expressions (PEP 701 support begins in Python 3.12).
    post_headline = payload.post.get('headline', '')
    post_language = 'Hindi' if re.search(r'[\u0900-\u097F]', post_headline) else 'English'

    credits=(
        f"POST TYPE: motivational quote poster\n"
        f"BRAND: {payload.brand}\n"
        f"HANDLE: {payload.handle}\n"
        f"STYLE: {payload.style}\n"
        f"TEMPLATE: {details['template']}\n"
        f"LANGUAGE: {post_language}\n"
        f"VIDEO REQUESTED: {'yes' if payload.withVideo else 'no'}\n"
        f"VIDEO LENGTH: {payload.videoSeconds if payload.withVideo else 0}s\n"
        f"ICON UPLOADED: {'yes' if payload.iconDataUrl else 'no'}\n"
        f"EFFECT: {chosen_effect}\n\n"
        "This output is intended as an original design. Review text before publishing.\n"
    )
    (folder/'credits.txt').write_text(credits,encoding='utf-8')
    (folder/'metadata.json').write_text(json.dumps({'post':payload.post,'brand':payload.brand,'handle':payload.handle,'style':payload.style,'withVideo':payload.withVideo,'videoSeconds':payload.videoSeconds,'effect':chosen_effect,'template':details,'warnings':warnings},ensure_ascii=False,indent=2),encoding='utf-8')
    license_data={'kind':'original_quote_design','creator':'QuoteCraft Studio procedural renderer','license':'Original project artwork','filePage':''}
    return {'assets':assets,'warnings':warnings,'license':license_data,'image':'original_quote_design'}

@app.get('/health')
def health():
    try: font=font_path(True)
    except Exception as exc: font='ERROR: '+str(exc)
    return {'ok':True,'ffmpeg':bool(shutil.which('ffmpeg')),'hindiFont':font,'raqm':bool(features.check('raqm'))}

@app.post('/render')
def render_endpoint(payload:RenderRequest):
    try:
        return render(payload)
    except (ValueError,RuntimeError) as exc:
        raise HTTPException(422,detail=str(exc)) from exc
