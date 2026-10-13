#!/usr/bin/env python3
"""Word-by-word "karaoke" captions for HyperFrames reels (Ojeda Works house style, 2026-10-13).

The word being spoken lights up NEON YELLOW (with glow + pop); the rest of the group stays white
with a black outline. Words come from whisper.cpp JSON made with:  whisper-cli -ml 1 -sow -oj

  python3 karaoke_captions.py clip.json [--offset 7.3] [--per 3] [--bottom 240] [--prefix k] > caps.html

Prints two blocks: CSS+HTML (paste inside the composition root) and JS (paste into the GSAP timeline,
after `const tl=...`). Several clips: run once per clip with --offset and a different --prefix
(kc1, kc2...). Prefix collisions with other ids break the page (tested 2026-10-13). Fix whisper
spellings (e.g. "Alpastor") in the JSON before running.
"""
import argparse, html, json

ap = argparse.ArgumentParser()
ap.add_argument("json"); ap.add_argument("--offset", type=float, default=0)
ap.add_argument("--per", type=int, default=3, help="words per caption group")
ap.add_argument("--bottom", type=int, default=240); ap.add_argument("--prefix", default="kc", help="UNIQUE per clip; must not match any other id in the page (e.g. kc1, kc2)")
ap.add_argument("--size", type=int, default=86)
a = ap.parse_args()

words = []
for s in json.load(open(a.json))["transcription"]:
    w = s["text"].strip()
    if not w:
        continue
    words.append((w.upper(), s["offsets"]["from"] / 1000 + a.offset, s["offsets"]["to"] / 1000 + a.offset))

groups, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) == a.per or w[0][-1] in ".?!,":
        groups.append(cur); cur = []
if cur:
    groups.append(cur)

p = a.prefix
out = [f"""<style>
.{p}g{{position:absolute;inset:0}}
.{p}g div{{position:absolute;bottom:{a.bottom}px;left:40px;right:40px;text-align:center;font-family:Anton,sans-serif;font-size:{a.size}px;line-height:1.05}}
.{p}w{{display:inline-block;margin:0 .12em;color:#fff;-webkit-text-stroke:5px #000;paint-order:stroke fill;text-shadow:0 6px 0 #000}}
.{p}w.on{{color:#e6ff00;text-shadow:0 0 18px #e6ff00aa,0 0 42px #e6ff0066,0 6px 0 #000}}
</style>"""]
js = []
for gi, g in enumerate(groups):
    start, end = g[0][1], (groups[gi + 1][0][1] if gi + 1 < len(groups) else g[-1][2] + 0.3)
    spans = "".join(f'<span class="{p}w" id="{p}{gi}_{wi}">{html.escape(w[0])}</span>' for wi, w in enumerate(g))
    out.append(f'<div class="{p}g clip" id="{p}{gi}" data-start="{start:.2f}" data-duration="{max(end - start, 0.2):.2f}" data-track-index="9"><div>{spans}</div></div>')
    for wi, w in enumerate(g):
        sel = f"#{p}{gi}_{wi}"
        off = (g[wi + 1][1] if wi + 1 < len(g) else end) 
        js.append(f'tl.set("{sel}",{{className:"{p}w on"}},{w[1]:.2f}).fromTo("{sel}",{{scale:1.25}},{{scale:1,duration:0.18,ease:"back.out(3)"}},{w[1]:.2f}).set("{sel}",{{className:"{p}w"}},{off:.2f});')
print("\n".join(out))
print("<!-- JS -->")
print("\n".join(js))
