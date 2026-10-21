import pathlib, sys, json, subprocess
from playwright.sync_api import sync_playwright
D=pathlib.Path(__file__).resolve().parent
POSTS=D.parent.parent
OUTS={"en":POSTS/"urgent-care-hours-2026-10-21","es":POSTS/"urgent-care-hours-es-2026-10-21"}
langs=sys.argv[1:] or ["en","es"]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    pg=b.new_page(viewport={"width":1080,"height":1350})
    for l in langs:
        for s in range(1,8):
            pg.goto(f"file://{D}/slides.html?l={l}&s={s}")
            pg.wait_for_function("window.__ready===true",timeout=30000)
            pg.wait_for_timeout(250)
            r=pg.evaluate("REPORT")[s-1]
            print(l,s,"OVERFLOW" if r["overflow"] else "ok",r["sizes"])
            png=OUTS[l]/f"slide{s}.png"
            pg.screenshot(path=str(png))
            subprocess.run(["/opt/homebrew/bin/ffmpeg","-y","-v","error","-i",str(png),"-q:v","2",str(OUTS[l]/f"slide{s}.jpg")])
    b.close()
