"""Narration and muxing for demo scenes (full-frame clips, no subtitles).

  scene.py narrate <scenes.json> --out <clips-dir> [--map pronunciation.json] [--voice af_heart] [--lang en-us] [id ...]
      Kokoro audio per scene: <clips-dir>/<id>.wav and <id>.cues.json (cue times relative to the clip).
  scene.py mux <id> <recording.webm> <offset_s> --out <clips-dir>
      Trim the recording to the scene length and add its audio: <clips-dir>/<id>.mp4

The pronunciation map is a JSON object {"written term": "spoken form"}. Default: pronunciation.json
next to scenes.json, otherwise none. Subtitles keep the written term; only the voice uses the spoken form.
Models and tools live in $DEMO_VIDEO_HOME (default ~/.local/share/demo-video-tts), set up by setup.sh / setup.ps1.
"""
import sys, os, json, argparse, subprocess

SR = 24000
LEAD, GAP, TAIL = 0.9, 0.9, 0.8
MODELS = os.path.expanduser(os.environ.get("DEMO_VIDEO_HOME", "~/.local/share/demo-video-tts"))


def load_map(scenes_file, explicit):
    path = explicit or os.path.join(os.path.dirname(os.path.abspath(scenes_file)), "pronunciation.json")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def spoken(text, say):
    for written, said in sorted(say.items(), key=lambda kv: -len(kv[0])):  # longest first: APIs before API
        text = text.replace(written, said)
    return text


def narrate(scenes_file, out, map_file, only, voice, lang):
    import numpy as np, soundfile as sf
    from kokoro_onnx import Kokoro
    say = load_map(scenes_file, map_file)
    os.makedirs(out, exist_ok=True)
    kokoro = Kokoro(f"{MODELS}/kokoro-v1.0.onnx", f"{MODELS}/voices-v1.0.bin")
    for sc in json.load(open(scenes_file)):
        if only and sc["id"] not in only:
            continue
        parts = [np.zeros(int(LEAD * SR), np.float32)]
        t, cues = LEAD, []
        for s in sc["sents"]:
            s = s if isinstance(s, str) else s["text"]
            a, _ = kokoro.create(spoken(s, say), voice=voice, speed=1.0, lang=lang)
            d = len(a) / SR
            cues.append({"start": round(t, 3), "end": round(t + d, 3), "text": s})
            parts += [a.astype(np.float32), np.zeros(int(GAP * SR), np.float32)]
            t += d + GAP
        dur = t - GAP + TAIL
        audio = np.concatenate(parts)[:int(dur * SR)]
        audio = np.pad(audio, (0, int(dur * SR) - len(audio)))
        sf.write(f"{out}/{sc['id']}.wav", audio, SR)
        json.dump({"duration": round(dur, 3), "cues": cues}, open(f"{out}/{sc['id']}.cues.json", "w"), indent=1)
        print(sc["id"], round(dur, 1), flush=True)


def mux(name, src, off, out):
    dur = json.load(open(f"{out}/{name}.cues.json"))["duration"]
    vf = f"fps=30,scale=1440:900,setsar=1,tpad=stop_mode=clone:stop_duration=3,trim=duration={dur:.3f},setpts=PTS-STARTPTS"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{float(off):.3f}", "-i", src, "-i", f"{out}/{name}.wav",
                    "-vf", vf, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-c:a", "aac", "-t", f"{dur:.3f}", f"{out}/{name}.mp4"], check=True)
    print("mux", name, round(dur, 1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("narrate"); n.add_argument("scenes"); n.add_argument("--out", required=True)
    n.add_argument("--map"); n.add_argument("--voice", default="af_heart"); n.add_argument("--lang", default="en-us")
    n.add_argument("ids", nargs="*")
    m = sub.add_parser("mux"); m.add_argument("id"); m.add_argument("recording"); m.add_argument("offset")
    m.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "narrate":
        narrate(a.scenes, a.out, a.map, a.ids, a.voice, a.lang)
    else:
        mux(a.id, a.recording, a.offset, a.out)
