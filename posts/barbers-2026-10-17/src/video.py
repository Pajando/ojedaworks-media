import pathlib, subprocess, sys, json
from playwright.sync_api import sync_playwright
D=pathlib.Path(__file__).resolve().parent
L=sys.argv[1]; OUT=D/f"silent-{L}.mp4"; FPS=30
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",args=["--allow-file-access-from-files"])
    pg=b.new_page(viewport={"width":1080,"height":1920})
    pg.goto(f"file://{D}/tiktok.html?l={L}"); pg.wait_for_function("window.__ready===true",timeout=30000)
    total=pg.evaluate("TOTAL"); n=int(round(total*FPS)); print(json.dumps({"total":total,"starts":pg.evaluate("STARTS")}))
    ff=subprocess.Popen(["/opt/homebrew/bin/ffmpeg","-y","-v","error","-f","image2pipe","-framerate",str(FPS),"-c:v","mjpeg","-i","-",
        "-c:v","libx264","-preset","slow","-crf","26","-pix_fmt","yuv420p","-movflags","+faststart",str(OUT)],stdin=subprocess.PIPE)
    for f in range(n):
        pg.evaluate(f"setT({f/FPS})")
        ff.stdin.write(pg.screenshot(type="jpeg",quality=90))
    ff.stdin.close(); ff.wait(); b.close(); print("frames",n)
