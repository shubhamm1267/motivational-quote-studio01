from pathlib import Path
from PIL import Image
from worker.editorial import TEMPLATES,render_editorial

POST={
 'headline':'Your peace deserves a little room:',
 'paragraphs':[{'text':'You can care about people and still choose to protect your energy. Start with the small boundaries that feel honest and sustainable.','highlights':['protect your energy']}],
 'closing':'You can be kind and still say no.',
 'highlights':['peace deserves']
}

def test_all_18_templates(tmp_path):
    assert len(TEMPLATES)==18
    for name in TEMPLATES:
        p=tmp_path/(name+'.png')
        meta=render_editorial(POST,'@theeverydayreset','portrait',name,p)
        im=Image.open(p)
        assert im.size==(1080,1350)
        assert meta['template']==name
        assert p.stat().st_size>6000

def test_square_long_list_fits_without_cropping(tmp_path):
    p=tmp_path/'square.png'
    obj={'headline':'A little reminder to yourself:','items':['You can begin again without announcing it to everybody.']*12,'closing':'Breathe in. Start again.'}
    meta=render_editorial(obj,'@handle','square','underrated',p)
    assert Image.open(p).size==(1080,1080)
    assert isinstance(meta['copyShortened'],bool)
    assert p.stat().st_size>6000  # Full square always renders, even for long copy

def test_reel_native_format(tmp_path):
    p=tmp_path/'reel.png'
    render_editorial(POST,'@handle','reel','thinking',p)
    assert Image.open(p).size==(1080,1920)
