"""Join scene clips with crossfades and burn in subtitles in the style of the subtitles skill.
Usage: assemble.py --clips <clips-dir> <output.mp4> <scene> [<scene> ...]
Also writes <output>.srt and embeds it as a switchable subtitle track."""
import sys, os, json, subprocess
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
# subtitles: the house style of the subtitles skill (../../subtitles/scripts/captions.py)
here=os.path.dirname(os.path.abspath(__file__))
for p in [os.path.join(here,"..","..","subtitles","scripts"), os.path.join(here,"..","..","..","subtitles","scripts")]:
    if os.path.exists(os.path.join(p,"captions.py")): sys.path.insert(0,p); break
try: from captions import Captions
except ImportError: sys.exit("assemble.py needs the subtitles skill (subtitles/scripts/captions.py) next to demo-video")
cap=Captions(1440,900)
cues=[]
for a,b,s in raw: cues+=cap.split_cue(s,a,b)
cues=cap.hold_until_next(cues)
tmp=out+".subs"; os.makedirs(tmp,exist_ok=True)
for i,c in enumerate(cues): cap.png(c["text"],f"{tmp}/{i}.png")
srt=out[:-4]+".srt"
cap.write_srt(cues,srt)
inp=[]; fc=[]
for n in names: inp+=["-i",f"{C}/{n}.mp4"]
v,a="[0:v]","[0:a]"
for j in range(1,len(names)):
    fc.append(f"{v}[{j}:v]xfade=transition=fade:duration={X}:offset={offs[j]:.3f}[v{j}]"); v=f"[v{j}]"
    fc.append(f"{a}[{j}:a]acrossfade=d={X}[a{j}]"); a=f"[a{j}]"
n=len(names)
for i,c in enumerate(cues):
    s,e=c["start"],c["end"]; inp+=["-i",f"{tmp}/{i}.png"]; fc.append(f"{v}[{n+i}:v]overlay=0:0:enable='gte(t,{s:.3f})*lt(t,{e:.3f})'[s{i}]"); v=f"[s{i}]"
fc.append(f"{v}fade=in:0:15,fade=out:st={total-0.6:.2f}:d=0.6[vo]")
inp+=["-i",srt]
subprocess.run(["ffmpeg","-nostdin","-v","error","-y",*inp,"-filter_complex",";".join(fc),"-map","[vo]","-map",a,"-map",f"{n+len(cues)}:s",
  "-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-c:a","aac","-c:s","mov_text","-metadata:s:s:0","language=eng",out],check=True)
print(out, round(total,1))
