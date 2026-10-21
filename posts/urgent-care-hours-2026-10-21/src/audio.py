import json, subprocess, sys, wave, re
import numpy as np
SR=48000; FF="/opt/homebrew/bin/ffmpeg"
J="/Users/alejandroojeda/ojedaworks-media/brand/jingle/"
LIB="/Users/alejandroojeda/ojedaworks-media/tools/sfx/lib/"
L=sys.argv[1]; T=json.load(open(f"timing-{L}.json"))
rng=np.random.default_rng(7)
def dec(p):
    raw=subprocess.run([FF,"-v","error","-i",p,"-f","f32le","-ac","2","-ar",str(SR),"-"],capture_output=True).stdout
    return np.frombuffer(raw,dtype="<f4").reshape(-1,2).copy()
def lufs(a):
    subprocess.run([FF,"-v","error","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-","/tmp/_l.wav"],input=a.astype("<f4").tobytes())
    o=subprocess.run([FF,"-hide_banner","-i","/tmp/_l.wav","-af","ebur128","-f","null","-"],capture_output=True,text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS",o)[-1])
def env(n,a,d): t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-t/d)
def st(x): return np.stack([x,x],1)
def bp(x,lo,hi):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X[(f<lo)|(f>hi)]=0; return np.fft.irfft(X,len(x))
def tear():  # ripping paper: band-passed noise with random crackle amplitude, 0.35 s
    n=int(.35*SR); x=bp(rng.standard_normal(n),900,7000)
    crack=np.repeat(rng.uniform(.2,1,n//240+1),240)[:n]
    e=np.minimum(1,np.arange(n)/(.02*SR))*np.linspace(1,.15,n)
    y=x*crack*e; return st(y/np.abs(y).max()*.6)
def flip():  # paper flip: short airy swish + soft snap
    n=int(.22*SR); x=bp(rng.standard_normal(n),400,4000)*np.sin(np.linspace(0,np.pi,n))**2
    s=bp(rng.standard_normal(int(.02*SR)),1500,6000)*env(int(.02*SR),.0005,.004)
    y=x*.5; k=int(.16*SR); y[k:k+len(s)]+=s*1.2; return st(y/np.abs(y).max()*.5)
def scratch(): # pen stroke ~0.4 s: noise modulated by stroke speed
    n=int(.4*SR); t=np.arange(n)/SR; x=bp(rng.standard_normal(n),2000,9000)
    m=(0.5+0.5*np.sin(2*np.pi*14*t))**2*np.sin(np.pi*t/.4)
    y=x*m; return st(y/np.abs(y).max()*.35)
def clack(): # steel clip: metallic click with short ring
    n=int(.25*SR); t=np.arange(n)/SR
    y=(np.sin(2*np.pi*2350*t)+.6*np.sin(2*np.pi*3710*t)+.4*np.sin(2*np.pi*5230*t))*env(n,.0003,.03)
    y+=bp(rng.standard_normal(n),1000,8000)*env(n,.0002,.006)*1.5
    return st(y/np.abs(y).max()*.7)
def libfx(name):
    with wave.open(LIB+name+".wav") as w: pcm=np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").reshape(-1,2)
    return pcm.astype(np.float32)/32768
total=T["total"]; N=int(total*SR); end=T["endtag"]
mix=np.zeros((N,2),np.float32)
# --- bed: chorus looped with 1 s crossfades, until slides end
ch=dec(J+"ojeda-works-chorus-16s.m4a"); xf=int(1.0*SR)
bed=ch.copy()
while len(bed)<int(end*SR)+SR:
    r=np.linspace(0,1,xf)[:,None]; tail=bed[-xf:]*(1-r)+ch[:xf]*r
    bed=np.concatenate([bed[:-xf],tail,ch[xf:]])
bed=bed[:int(end*SR)]
fo=int(.8*SR); bed[-fo:]*=np.linspace(1,0,fo)[:,None]
g=10**((-20-lufs(bed))/20); bed*=g
mix[:len(bed)]+=bed
# --- end tag at full level
et=dec(J+"ojeda-works-endtag-6s.m4a"); k=int(end*SR); m=min(len(et),N-k); mix[k:k+m]+=et[:m]
# --- sfx
def put(sig,t,gain=1.0):
    i=int(t*SR); m=min(len(sig),N-i)
    if m>0: mix[i:i+m]+=sig[:m]*gain
put(clack(),0.02,.9)
for t in T["tears"]: put(tear(),t-0.03,.8)
for t in T["flips"]: put(flip(),t,.9)
tick=libfx("tick")
for t in T["checks"]: put(scratch(),t,.8); put(tick,t+0.38,.5)
pk=np.abs(mix).max(); lim=10**(-1.5/20)
if pk>lim: mix*=lim/pk
print("bed gain dB %.1f"%(20*np.log10(g)),"peak dBFS %.2f"%(20*np.log10(np.abs(mix).max())))
subprocess.run([FF,"-v","error","-y","-f","f32le","-ar",str(SR),"-ac","2","-i","-",f"mix-{L}.wav"],input=mix.astype("<f4").tobytes())
