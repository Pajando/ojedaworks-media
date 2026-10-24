#!/usr/bin/python3
# Flash-cut reel, 2026-10-23. Usage: /usr/bin/python3 build.py en|es
# Cuts land on the chorus beat (122 BPM, beat 1 at 0.42s, measured from the jingle).
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont

LANG = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
FUT = '/System/Library/Fonts/Supplemental/Futura.ttc'
F = lambda s, i=4: ImageFont.truetype(FUT, s, index=i)   # 4 = Condensed ExtraBold
NEON, WHITE, INK = (230, 255, 0), (255, 255, 255), (10, 10, 12)
JINGLE = os.path.expanduser('~/ojedaworks-media/brand/jingle/ojeda-works-chorus-16s.m4a')
TOTAL = 16.1
B = lambda k: round(0.42 + 0.4918 * k, 3)   # beat k

# (end time, kind, source, start-in-clip)
SHOTS = [
    (B(1),  'still', 'styled/s1.png', None),   # blue spotlight, night
    (B(3),  'clip',  'flow/t2.mp4', 2.6),
    (B(4),  'still', 'styled/s3.png', None),   # film negative
    (B(6),  'clip',  'flow/t2.mp4', 3.7),
    (B(7),  'still', 'styled/s2.png', None),   # x-ray
    (B(9),  'clip',  'flow/t2.mp4', 5.0),
    (B(10), 'still', 'styled/s4.png', None),   # blueprint
    (B(12), 'clip',  'flow/t2.mp4', 6.6),
    (B(14), 'clip',  'flow/t1.mp4', 0.6),      # typing, head down
    (B(15), 'still', 'styled/s5b.png', None),  # halftone made locally from t1 at 2.5s (AI s5 had a grin + melted hand)
    (B(17), 'clip',  'flow/t1.mp4', 1.9),      # looks up to camera; smile starts ~3.2s, logo from ~4.5s
    (B(18), 'still', 'styled/s6.png', None),   # point cloud
    (B(20), 'clip',  'flow/t1.mp4', 6.62),
    (TOTAL, 'end',   'styled/s6.png', None),
]

TXT = {
 'en': [(0.0, B(6), [('11 PM.', 190, NEON)], 0.0),
        (0.5, B(6), [('11 PM.', 190, NEON), ('SOMEONE NEEDS', 120, WHITE), ('WHAT YOU SELL.', 120, WHITE)], 0.0),
        (B(6), B(9), [('THEY SEARCH.', 150, WHITE)], 0.0),
        (B(9), B(12), [('THEY SEARCH.', 150, WHITE), ('THEY ASK AI.', 150, NEON)], 0.0),
        (B(12), B(15), [('WHO SHOWS UP?', 170, NEON)], 0.0),
        (B(15), B(20), [("I MAKE SURE", 150, WHITE), ("IT'S YOU.", 190, NEON)], 0.0),
        (B(20), TOTAL, [('OJEDA WORKS', 190, WHITE), ('ojedaworks.com', 96, NEON)], 0.0)],
 'es': [(0.0, B(6), [('11 DE LA NOCHE.', 150, NEON)], 0.0),
        (0.5, B(6), [('11 DE LA NOCHE.', 150, NEON), ('ALGUIEN NECESITA', 112, WHITE), ('LO QUE VENDES.', 112, WHITE)], 0.0),
        (B(6), B(9), [('BUSCAN.', 160, WHITE)], 0.0),
        (B(9), B(12), [('BUSCAN.', 160, WHITE), ('LE PREGUNTAN', 130, NEON), ('A LA IA.', 130, NEON)], 0.0),
        (B(12), B(15), [('¿QUIÉN SALE?', 170, NEON)], 0.0),
        (B(15), B(20), [('YO ME ASEGURO', 140, WHITE), ('QUE SEAS TÚ.', 170, NEON)], 0.0),
        (B(20), TOTAL, [('OJEDA WORKS', 190, WHITE), ('ojedaworks.com', 96, NEON)], 0.0)],
}
TAG = {'en': 'AI AVATAR', 'es': 'AVATAR IA'}[LANG]

out = os.path.join(HERE, 'build', LANG); os.makedirs(out, exist_ok=True)
run = lambda a: subprocess.run(a, check=True)

# 1. segments
segs, t0 = [], 0.0
for i, (t1, kind, src, ss) in enumerate(SHOTS):
    n = round(t1 * FPS) - round(t0 * FPS)
    p = os.path.join(out, f'seg{i:02d}.mp4'); segs.append(p)
    enc = ['-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-frames:v', str(n), p]
    if kind == 'clip':
        run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-i', os.path.join(HERE, src),
             '-vf', f'scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS}'] + enc)
    else:
        z = '1.06' if kind == 'still' else '1.12'
        dark = ',eq=brightness=-0.10' if kind == 'end' else ''
        run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-i', os.path.join(HERE, src), '-vf',
             f"scale={W*2}:{H*2}:flags=lanczos,zoompan=z='1+({z}-1)*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},"
             f"setsar=1,fade=in:st=0:d=0.1:color=white{dark}"] + enc)
    t0 = t1

lst = os.path.join(out, 'list.txt')
open(lst, 'w').write(''.join(f"file '{s}'\n" for s in segs))
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', os.path.join(out, 'cut.mp4')])

# 2. text cards (full-frame PNGs). Block centred on y=1330, nothing below 1650.
def card(lines, path):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fonts = []
    for txt, size, col in lines:
        f = F(size)
        while d.textlength(txt, font=f) > W - 120: size -= 4; f = F(size)
        fonts.append((txt, f, col, size))
    gap = 14
    hs = [f.getbbox(t)[3] - f.getbbox(t)[1] for t, f, c, s in fonts]
    y = 1330 - (sum(hs) + gap * (len(hs) - 1)) / 2
    for (txt, f, col, size), h in zip(fonts, hs):
        x = (W - d.textlength(txt, font=f)) / 2
        d.text((x, y - f.getbbox(txt)[1]), txt, font=f, fill=col, stroke_width=max(6, size // 16), stroke_fill=INK)
        y += h + gap
    assert y < 1650, (lines, y)
    # small label, top right
    tf = F(40, 2); tw = d.textlength(TAG, font=tf)
    d.rounded_rectangle((W - 60 - tw - 36, 120, W - 60, 184), 14, fill=(10, 10, 12, 170))
    d.text((W - 60 - tw - 18, 128), TAG, font=tf, fill=WHITE)
    im.save(path)

cards = []
for k, (a, b, lines, _) in enumerate(TXT[LANG]):
    p = os.path.join(out, f'txt{k}.png'); card(lines, p); cards.append((a, b, p))

# Lines that stack (hook line 2, second "search" line) replace the earlier card for their window.
inputs, fc, last = [], '', '[0:v]'
for k, (a, b, p) in enumerate(cards):
    inputs += ['-loop', '1', '-framerate', str(FPS), '-t', str(TOTAL), '-i', p]
    nxt = [c for c in cards[k + 1:] if c[0] < b]
    end = min([b] + [c[0] for c in nxt])
    fc += f"{last}[{k+1}:v]overlay=0:0:enable='between(t,{a},{end - 0.001})'[v{k}];"
    last = f'[v{k}]'
fc = fc.rstrip(';')
final = os.path.join(HERE, f'flash-cut-{LANG}.mp4')
run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(out, 'cut.mp4')] + inputs +
    ['-i', JINGLE, '-filter_complex', fc + f";[{len(cards)+1}:a]afade=out:st={TOTAL-0.4}:d=0.4[a]",
     '-map', last, '-map', '[a]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
     '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-t', str(TOTAL), final])
print(final)
