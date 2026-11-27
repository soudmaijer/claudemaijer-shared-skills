"""Burned-in captions in a short-cue streaming style, plus a matching .srt.

Import it from a video build script:

    from captions import Captions, srt_time
    cap = Captions(width=1920, height=1080)       # sizes scale with the frame height
    cues = cap.split_cue(sentence, start, end)    # short cues, timed by character share
    cues = cap.hold_until_next(cues)              # a cue stays until the next one starts
    cap.png(text, "cap_001.png")                  # transparent full-frame overlay for ffmpeg
    lines = cap.lines(text)                       # the same line breaks for the .srt
    cap.write_srt(cues, "video.srt")

Or run it on its own:

    python captions.py --image frame.png --cues cues.json --out out.mp4 [--srt out.srt] [--font <path>]

cues.json is a list of {"start": s, "end": s, "text": "..."}; long texts are split into short cues.
Needs Pillow; the command line also needs ffmpeg (no libass required).
Font: --font or $CAPTIONS_FONT, otherwise the first bold sans-serif found on macOS, Windows or Linux.
"""
import argparse
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

MAX_CUE = 60        # characters per cue
MAX_LINE = 42       # characters per line, two lines at most
BOX_ALPHA = 80      # line box: black at 80 of 255 (about 30% opacity)

# (path, index in a .ttc collection); the first that exists is used.
FONT_CANDIDATES = [
    ("/System/Library/Fonts/Helvetica.ttc", 1),                       # macOS: Helvetica Bold
    ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),         # macOS
    ("C:/Windows/Fonts/arialbd.ttf", 0),                              # Windows: Arial Bold
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0),      # Debian/Ubuntu
    ("/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", 0),    # Fedora
    ("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 0),                  # Arch
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 0),
]


def load_font(size, path=None):
    path = path or os.environ.get("CAPTIONS_FONT")
    candidates = [(path, 0)] if path else FONT_CANDIDATES
    for p, index in candidates:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=index)
            except OSError:
                continue
    sys.stderr.write("captions: no bold sans-serif font found, set --font or CAPTIONS_FONT\n")
    return ImageFont.load_default(size)


def srt_time(x):
    ms = int(round(x * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


class Captions:
    def __init__(self, width=1920, height=1080, font_path=None):
        self.w, self.h = width, height
        self.k = height / 1080                     # every size below is for 1080p
        self.font = load_font(round(44 * self.k), font_path)

    def lines(self, text):
        """One line if it fits; otherwise two lines of about equal rendered width."""
        f = self.font
        if f.getlength(text) <= f.getlength("x" * MAX_LINE):
            return [text]
        words = text.split()
        best = None
        for i in range(1, len(words)):
            a, b = " ".join(words[:i]), " ".join(words[i:])
            diff = abs(f.getlength(a) - f.getlength(b))
            if best is None or diff < best[0]:
                best = (diff, [a, b])
        return best[1] if best else [text]

    @staticmethod
    def split_cue(text, start, end):
        """Split one spoken sentence (or a few) into short cues, timed by character share.
        A new sentence always starts a new cue; then split at , ; : and last on words."""
        parts = re.split(r"(?<=[.!?,;:])\s+", text.strip())
        chunks = []
        for part in parts:
            joinable = chunks and not chunks[-1].endswith((".", "!", "?"))
            if joinable and len(chunks[-1]) + 1 + len(part) <= MAX_CUE:
                chunks[-1] += " " + part
            elif len(part) <= MAX_CUE:
                chunks.append(part)
            else:
                cur = ""
                for word in part.split():
                    if cur and len(cur) + 1 + len(word) > MAX_CUE:
                        chunks.append(cur)
                        cur = word
                    else:
                        cur = (cur + " " + word).strip()
                if cur:
                    chunks.append(cur)
        total = sum(len(c) for c in chunks)
        out, t = [], start
        for c in chunks:
            d = (end - start) * len(c) / total
            out.append({"start": t, "end": t + d, "text": c})
            t += d
        return out

    @staticmethod
    def hold_until_next(cues, max_gap=2.0):
        """A cue stays until the next one starts (no flicker in pauses), unless the gap is long."""
        for a, b in zip(cues, cues[1:]):
            if b["start"] - a["end"] <= max_gap:
                a["end"] = b["start"]
        return cues

    def png(self, text, path):
        """Transparent full-frame PNG: bottom centre, a tight box per line. Returns the top y of the text block."""
        k, f = self.k, self.font
        lines = self.lines(text)
        lh, pad_y, bottom = 52 * k, 18 * k, 44 * k
        y0 = self.h - bottom - (lh * len(lines) + 2 * pad_y)
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i, line in enumerate(lines):
            lw = f.getlength(line)
            lx, ly = (self.w - lw) / 2, y0 + pad_y + i * lh
            d.rectangle((lx - 14 * k, ly - 4 * k, lx + lw + 14 * k, ly + lh - 2 * k), fill=(0, 0, 0, BOX_ALPHA))
            d.text((lx, ly + 3 * k), line, font=f, fill=(255, 255, 255, 255),
                   stroke_width=max(1, round(k)), stroke_fill=(0, 0, 0, 255))
        im.save(path)
        return y0

    def write_srt(self, cues, path):
        blocks = [f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n" + "\n".join(self.lines(c["text"])) + "\n"
                  for i, c in enumerate(cues, 1)]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(blocks))

    def overlay_filter(self, first_input, cues, base="[0:v]"):
        """ffmpeg filter_complex that overlays caption PNG inputs first_input.. on base. Returns (filter, last label)."""
        chain, prev = [], base
        for i, c in enumerate(cues):
            label = f"[cap{i}]"
            chain.append(f"{prev}[{first_input + i}:v]overlay=0:0:enable='between(t,{c['start']:.3f},{c['end']:.3f})'{label}")
            prev = label
        return ";".join(chain), prev


def main():
    ap = argparse.ArgumentParser(description="Burn captions onto a still image or a video.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--image", help="still picture used as the background")
    src.add_argument("--video", help="video to caption")
    ap.add_argument("--cues", required=True, help="JSON list of {start, end, text}")
    ap.add_argument("--out", required=True)
    ap.add_argument("--srt", help="default: <out>.srt")
    ap.add_argument("--font")
    a = ap.parse_args()

    raw = json.load(open(a.cues, encoding="utf-8"))
    bg = a.image or a.video
    if a.image:
        w, h = Image.open(bg).size
    else:
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                "-of", "csv=p=0", bg], capture_output=True, text=True, check=True).stdout
        w, h = map(int, probe.strip().split(",")[:2])
    cap = Captions(w, h, a.font)
    cues = []
    for c in raw:
        cues += cap.split_cue(c["text"], c["start"], c["end"])
    cues = cap.hold_until_next(cues)

    tmp = os.path.splitext(a.out)[0] + ".captions"
    os.makedirs(tmp, exist_ok=True)
    inputs = ["-loop", "1", "-framerate", "30", "-t", f"{cues[-1]['end'] + 0.5:.3f}", "-i", bg] if a.image else ["-i", bg]
    for i, c in enumerate(cues):
        p = os.path.join(tmp, f"{i:04d}.png")
        cap.png(c["text"], p)
        inputs += ["-i", p]
    fc, last = cap.overlay_filter(1, cues)
    audio = [] if a.image else ["-map", "0:a?", "-c:a", "copy"]
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", last, *audio,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", a.out], check=True)
    cap.write_srt(cues, a.srt or os.path.splitext(a.out)[0] + ".srt")
    print(a.out, len(cues), "cues")


if __name__ == "__main__":
    main()
