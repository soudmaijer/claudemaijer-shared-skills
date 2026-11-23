"""Join scene clips with crossfades and burn in film-style subtitles.
Usage: assemble.py --clips <clips-dir> <output.mp4> <scene> [<scene> ...]
Also writes <output>.srt and embeds it as a switchable subtitle track."""
import sys, os, json, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
X=0.6
args=sys.argv[1:]
if len(args)<4 or args[0]!="--clips": sys.exit(__doc__)
C, out, names = args[1], args[2], args[3:]
meta=[json.load(open(f"{C}/{n}.cues.json")) for n in names]
# global cue times: each next clip starts X earlier because of the crossfade
raw=[]; off=0.0; offs=[]
for m in meta:
    offs.append(off); raw += [(c["start"]+off, c["end"]+off, c["text"]) for c in m["cues"]]; off += m["duration"]-X
total=off+X
# subtitle rules: left aligned at x=180, at most 1080 px wide (75% of the frame), one line whenever the text fits,
# otherwise split at a natural break into consecutive one-line cues, two balanced lines only when no sensible break exists;
# on screen 0.83 to 7 s, at most 20 characters per second
LEFT=180; MAXW=1080
def load_font(size=42):
    """Helvetica Neue Medium on macOS; a similar sans-serif elsewhere."""
    candidates=[("/System/Library/Fonts/HelveticaNeue.ttc",10),
        ("/System/Library/Fonts/Helvetica.ttc",0),
        ("C:/Windows/Fonts/arialbd.ttf",0),("C:/Windows/Fonts/arial.ttf",0),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",0),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",0)]
    for path,idx in candidates:
        if os.path.exists(path):
            try: return ImageFont.truetype(path,size,index=idx)
            except OSError: continue
    return ImageFont.load_default(size)
font=load_font()
fits=lambda t: font.getlength(t)<=MAXW
BREAKS=[". ","? ","! ",": ","; ",", "," and "," or "," which "]
def split_once(t):
    """Best natural break: both parts at least 15 characters, as balanced as possible, strong breaks preferred."""
    best=None
    for rank,b in enumerate(BREAKS):
        i=t.find(b)
        while i!=-1:
            cut=i+len(b.rstrip()) if b.strip() in ".?!:;," else i+1
            l,r=t[:cut].strip(),t[cut:].strip()
            if len(l)>=15 and len(r)>=15:
                score=abs(len(l)-len(r))+(0 if rank<6 else 25)
                if best is None or score<best[0]: best=(score,l,r)
            i=t.find(b,i+1)
    return best
def pieces(t):
    if fits(t): return [t]
    sp=split_once(t)
    return pieces(sp[1])+pieces(sp[2]) if sp else [t]
def lines_of(t):
    if fits(t): return [t]
    w=t.split(); cands=[]
    for i in range(1,len(w)):
        l,r=" ".join(w[:i])," ".join(w[i:])
        if fits(l) and fits(r): cands.append((abs(len(l)-len(r)),l,r))
    return list(min(cands)[1:]) if cands else textwrap.wrap(t,60)
cues=[]
for a,b,s in raw:
    ps=pieces(s); n=sum(len(p) for p in ps); t=a; seg=[]
    for p in ps:
        d=(b-a)*len(p)/n; seg.append([t,t+d,p]); t+=d
    i=0
    while i<len(seg):
        a2,b2,p=seg[i]
        if (b2-a2<0.83 or len(p)/(b2-a2)>20) and i+1<len(seg) and len(lines_of(p+" "+seg[i+1][2]))<=2:
            seg[i:i+2]=[[a2,seg[i+1][1],p+" "+seg[i+1][2]]]; continue
        i+=1
    for a2,b2,p in seg: cues.append((a2,min(b2,a2+7),lines_of(p)))
tmp=out+".subs"; os.makedirs(tmp,exist_ok=True)
for i,(a,b,ls) in enumerate(cues):
    y=900-56-len(ls)*58
    sh=Image.new("RGBA",(1440,900),(0,0,0,0)); ds=ImageDraw.Draw(sh)
    img=Image.new("RGBA",(1440,900),(0,0,0,0)); d=ImageDraw.Draw(img)
    for ln in ls:
        # semi-transparent dark box behind each line, like TV subtitles
        x0,y0,x1,y1=d.textbbox((LEFT,y),ln,font=font)
        ds.rounded_rectangle((x0-14,y0-9,x1+14,y1+11),radius=6,fill=(0,0,0,130))
        d.text((LEFT,y),ln,font=font,fill="white",stroke_width=1,stroke_fill=(0,0,0,200)); y+=58
    sh.alpha_composite(img); sh.save(f"{tmp}/{i}.png")
def ts(t): return f"{int(t//3600):02}:{int(t%3600//60):02}:{int(t%60):02},{int(round(t%1*1000)):03}"
srt=out[:-4]+".srt"
open(srt,"w").write("\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n"+"\n".join(s)+"\n" for i,(a,b,s) in enumerate(cues)))
inp=[]; fc=[]
for n in names: inp+=["-i",f"{C}/{n}.mp4"]
v,a="[0:v]","[0:a]"
for j in range(1,len(names)):
    fc.append(f"{v}[{j}:v]xfade=transition=fade:duration={X}:offset={offs[j]:.3f}[v{j}]"); v=f"[v{j}]"
    fc.append(f"{a}[{j}:a]acrossfade=d={X}[a{j}]"); a=f"[a{j}]"
n=len(names)
for i,(s,e,_) in enumerate(cues):
    inp+=["-i",f"{tmp}/{i}.png"]; fc.append(f"{v}[{n+i}:v]overlay=0:0:enable='gte(t,{s:.3f})*lt(t,{e:.3f})'[s{i}]"); v=f"[s{i}]"
fc.append(f"{v}fade=in:0:15,fade=out:st={total-0.6:.2f}:d=0.6[vo]")
inp+=["-i",srt]
subprocess.run(["ffmpeg","-nostdin","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[vo]","-map",a,"-map",f"{n+len(cues)}:s",
  "-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-c:a","aac","-c:s","mov_text","-metadata:s:s:0","language=eng",out],check=True)
print(out, round(total,1))
