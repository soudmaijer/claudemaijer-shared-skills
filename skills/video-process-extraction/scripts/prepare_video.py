"""Prepare a screen recording for analysis: transcript (SRT + TXT) and frames.

Usage:
    python prepare_video.py VIDEO [--out DIR] [--lang nl] [--threshold 0.01]
                            [--min-gap 2] [--max-gap 15]
                            [--model large-v3-turbo] [--vocab FILE]
    python prepare_video.py --check

Works on Windows, macOS and Linux. Needs: pip install faster-whisper pillow
"""

import argparse
import sys
from pathlib import Path


def check_dependencies():
    missing = []
    for module, package in (("faster_whisper", "faster-whisper"), ("av", "av"), ("PIL", "pillow")):
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        print("MISSING: " + " ".join(missing))
        print(f"Install with: {Path(sys.executable).name} -m pip install " + " ".join(missing))
        return False
    print("OK: all dependencies are installed")
    return True


def format_timestamp(seconds, separator=","):
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def changed_fraction(thumb_a, thumb_b):
    """Fraction of pixels that differ visibly between two small grayscale images."""
    from PIL import ImageChops

    diff = ImageChops.difference(thumb_a, thumb_b).point(lambda value: 255 if value > 25 else 0)
    return diff.histogram()[255] / (diff.width * diff.height)


def extract_frames(video, frames_dir, threshold, min_gap, max_gap):
    """Save a frame when the screen changes, at most every min_gap s and at least every max_gap s.

    threshold 0 means fixed sampling: one frame every max_gap seconds.
    """
    import av

    frames_dir.mkdir(parents=True, exist_ok=True)
    index_lines = []
    last_time = None
    last_thumb = None
    count = 0
    with av.open(str(video)) as container:
        stream = container.streams.video[0]
        for frame in container.decode(stream):
            if frame.time is None:
                continue
            if last_time is not None and frame.time - last_time < min_gap:
                continue
            image = frame.to_image()
            thumb = image.convert("L").resize((320, 180))
            if last_time is None:
                reason = "start"
            elif frame.time - last_time >= max_gap:
                reason = "max-gap"
            elif threshold > 0 and changed_fraction(thumb, last_thumb) >= threshold:
                reason = "change"
            else:
                continue
            count += 1
            name = f"f_{count:03d}.jpg"
            image.save(frames_dir / name, quality=80)
            index_lines.append(f"{name}\t{format_timestamp(frame.time, '.')[:8]}\t{reason}")
            last_time, last_thumb = frame.time, thumb
    (frames_dir / "index.tsv").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Frames: {count} written to {frames_dir}")


def transcribe(video, out_dir, lang, model_name, vocab):
    from faster_whisper import WhisperModel

    prompt = vocab.read_text(encoding="utf-8").replace("\n", " ") if vocab else None
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, info = model.transcribe(
        str(video), language=lang, initial_prompt=prompt, vad_filter=True
    )
    srt_lines, txt_lines = [], []
    for number, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        srt_lines += [
            str(number),
            f"{format_timestamp(segment.start)} --> {format_timestamp(segment.end)}",
            text,
            "",
        ]
        txt_lines.append(f"[{format_timestamp(segment.start, '.')[:8]}] {text}")
        print(f"\r  transcribed up to {format_timestamp(segment.end, '.')[:8]}", end="")
    print()
    (out_dir / "transcript.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    (out_dir / "transcript.txt").write_text("\n".join(txt_lines) + "\n", encoding="utf-8")
    print(f"Transcript: {len(txt_lines)} segments, language {info.language}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", nargs="?", type=Path)
    parser.add_argument("--out", type=Path, help="output folder (default: next to the video)")
    parser.add_argument("--lang", default="nl", help="spoken language (default: nl)")
    parser.add_argument("--threshold", type=float, default=0.01,
                        help="fraction of changed pixels that triggers a frame; 0 = fixed interval (default: 0.01)")
    parser.add_argument("--min-gap", type=float, default=2, help="minimum seconds between frames (default: 2)")
    parser.add_argument("--max-gap", type=float, default=15,
                        help="maximum seconds without a frame; the interval in fixed mode (default: 15)")
    parser.add_argument("--model", default="large-v3-turbo", help="whisper model (default: large-v3-turbo)")
    parser.add_argument("--vocab", type=Path, help="text file with domain terms for the speech model")
    parser.add_argument("--skip-transcript", action="store_true")
    parser.add_argument("--skip-frames", action="store_true")
    parser.add_argument("--check", action="store_true", help="only check the dependencies")
    args = parser.parse_args()

    if not check_dependencies():
        sys.exit(1)
    if args.check:
        return
    if not args.video or not args.video.is_file():
        parser.error("give the path to an existing video file")

    out_dir = args.out or args.video.with_suffix("")
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.skip_frames:
        extract_frames(args.video, out_dir / "frames", args.threshold, args.min_gap, args.max_gap)
    if not args.skip_transcript:
        transcribe(args.video, out_dir, args.lang, args.model, args.vocab)
    print(f"Done: {out_dir}")


if __name__ == "__main__":
    main()
