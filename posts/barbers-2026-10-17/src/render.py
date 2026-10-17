import pathlib, sys
from playwright.sync_api import sync_playwright
D=pathlib.Path(__file__).resolve().parent
POSTS=D.parent.parent
OUTS={"en":POSTS/"barbers-2026-10-17","es":POSTS/"barbers-es-2026-10-17"}
CHECK="""(()=>{const out=[];const sl=document.querySelector('.slide.on');const box=sl.querySelector('.in').getBoundingClientRect();
 sl.querySelectorAll('.in *').forEach(e=>{if(!e.childElementCount&&!e.textContent.trim())return;const r=e.getBoundingClientRect();if(r.width==0)return;
   if(r.right>box.right+2||r.left<box.left-2||r.bottom>1106||r.top<box.top-2)out.push('oob:'+(e.textContent||e.tagName).trim().slice(0,24)+' '+Math.round(r.left)+','+Math.round(r.right)+','+Math.round(r.bottom))});
 sl.querySelectorAll('.src,.tag').forEach(e=>{const r=e.getBoundingClientRect();if(r.bottom>1200||r.right>1062)out.push('chip:'+e.textContent+' '+Math.round(r.right)+','+Math.round(r.bottom))});
 const a=sl.querySelector('.src'),b=sl.querySelector('.tag');if(a){const ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();if(ra.left<rb.right+10)out.push('chip overlap')}
 sl.querySelectorAll('.ln').forEach(l=>out.push('fs:'+parseInt(l.style.fontSize)+' '+l.textContent.trim().slice(0,18)));
 return out})()"""
langs=sys.argv[1:] or ["en","es"]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    pg=b.new_page(viewport={"width":1080,"height":1350})
    for l in langs:
        for s in range(1,7):
            pg.goto(f"file://{D}/slides.html?l={l}&s={s}")
            pg.wait_for_function("window.__ready===true",timeout=30000)
            pg.wait_for_timeout(300)
            r=pg.evaluate(CHECK)
            print(l,s,[x for x in r if not x.startswith('fs:')] or 'OK', [x for x in r if x.startswith('fs:')])
            pg.screenshot(path=str(OUTS[l]/f"slide{s}.png"))
    b.close()
