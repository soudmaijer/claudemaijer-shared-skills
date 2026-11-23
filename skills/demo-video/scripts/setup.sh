#!/usr/bin/env bash
# Idempotent prerequisite check and install for the demo-video skill (macOS first, Linux works too).
# Safe to run any time: it only installs what is missing, and exits non-zero on any failure.
set -u
TTS="${DEMO_VIDEO_HOME:-$HOME/.local/share/demo-video-tts}"
VENV="$TTS/venv"
NODE_DIR="$TTS/node"
REL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
FAILED=0

ok()   { echo "  OK    $1"; }
fail() { echo "  FAIL  $1"; echo "        fix: $2"; FAILED=1; }
step() { echo; echo "== $1"; }

size_of() { stat -f%z "$1" 2>/dev/null || stat -c%s "$1" 2>/dev/null || echo 0; }
mb()      { echo $(( $(size_of "$1") / 1000000 )); }

step "ffmpeg"
if command -v ffmpeg >/dev/null 2>&1; then ok "$(ffmpeg -version | head -1)"
else fail "ffmpeg not found" "brew install ffmpeg (macOS), or install from https://ffmpeg.org"; fi

step "node and npx"
if command -v node >/dev/null 2>&1 && command -v npx >/dev/null 2>&1; then ok "node $(node --version)"
else fail "node/npx not found" "brew install node (macOS), or install from https://nodejs.org"; fi

step "python with onnxruntime wheels"
PY=""
for v in 3.14 3.13 3.12; do
  if command -v "python$v" >/dev/null 2>&1; then PY="python$v"; break; fi
done
if [ -z "$PY" ] && command -v python3 >/dev/null 2>&1; then
  minor=$(python3 -c 'import sys; print(sys.version_info[0]*100+sys.version_info[1])')
  if [ "$minor" -ge 315 ]; then
    fail "python3 is $(python3 --version 2>&1), too new: onnxruntime has no wheels yet" "brew install python@3.14, then run this script again"
  elif [ "$minor" -ge 312 ]; then PY=python3
  fi
fi
if [ -n "$PY" ]; then ok "$PY ($($PY --version 2>&1))"
elif [ "$FAILED" -eq 0 ] || ! command -v python3 >/dev/null 2>&1; then
  fail "no python 3.12 to 3.14 found" "brew install python@3.14"
fi

step "virtual environment and packages ($VENV)"
if [ -n "$PY" ]; then
  mkdir -p "$TTS"
  if [ ! -x "$VENV/bin/python" ]; then
    "$PY" -m venv "$VENV" && ok "created venv" || fail "could not create venv" "check that $PY has the venv module"
  fi
  if [ -x "$VENV/bin/python" ]; then
    if "$VENV/bin/python" -c "import kokoro_onnx, soundfile, PIL, numpy" 2>/dev/null; then ok "kokoro-onnx soundfile pillow numpy present"
    else
      echo "  installing packages ..."
      if "$VENV/bin/pip" install --quiet kokoro-onnx soundfile pillow numpy; then ok "packages installed"
      else fail "pip install failed" "run $VENV/bin/pip install kokoro-onnx soundfile pillow numpy and read the error"; fi
    fi
  fi
fi

step "Kokoro model files"
fetch() { # name, minimum size in MB
  local f="$TTS/$1"
  if [ -f "$f" ] && [ "$(mb "$f")" -ge "$2" ]; then ok "$1 ($(mb "$f") MB)"; return; fi
  echo "  downloading $1 ..."
  mkdir -p "$TTS"
  if curl -fL --retry 3 -o "$f.part" "$REL/$1" && [ "$(mb "$f.part")" -ge "$2" ]; then mv "$f.part" "$f"; ok "$1 ($(mb "$f") MB)"
  else rm -f "$f.part"; fail "$1 missing or too small" "download $REL/$1 into $TTS"; fi
}
fetch kokoro-v1.0.onnx 300
fetch voices-v1.0.bin 20

step "Playwright and Chromium"
if command -v npx >/dev/null 2>&1; then
  mkdir -p "$NODE_DIR"
  if [ ! -d "$NODE_DIR/node_modules/playwright-core" ]; then
    echo "  installing playwright-core into $NODE_DIR ..."
    (cd "$NODE_DIR" && { [ -f package.json ] || echo '{"private":true}' > package.json; } && npm install --silent playwright-core) \
      && ok "playwright-core installed" || fail "npm install playwright-core failed" "cd $NODE_DIR && npm install playwright-core"
  else ok "playwright-core present"; fi
  if (cd "$NODE_DIR" && node -e "const {chromium}=require('playwright-core');process.exit(require('fs').existsSync(chromium.executablePath())?0:1)") 2>/dev/null; then ok "chromium present"
  else
    echo "  installing chromium ..."
    (cd "$NODE_DIR" && npx -y playwright install chromium) && ok "chromium installed" || fail "chromium install failed" "cd $NODE_DIR && npx -y playwright install chromium"
  fi
fi

step "TTS smoke test (voice af_heart)"
if [ -x "$VENV/bin/python" ] && [ -f "$TTS/voices-v1.0.bin" ]; then
  SMOKE=$(mktemp -d)
  if "$VENV/bin/python" - "$TTS" "$SMOKE/t.wav" <<'PYEOF'
import sys, soundfile as sf
from kokoro_onnx import Kokoro
m, out = sys.argv[1], sys.argv[2]
a, sr = Kokoro(f"{m}/kokoro-v1.0.onnx", f"{m}/voices-v1.0.bin").create("Hello from the demo video skill.", voice="af_heart", speed=1.0, lang="en-us")
assert len(a) > sr, "audio shorter than one second"
sf.write(out, a, sr)
PYEOF
  then ok "one sentence synthesised ($(size_of "$SMOKE/t.wav") bytes)"
  else fail "TTS smoke test failed" "read the error above; check the model files and the venv"; fi
  rm -rf "$SMOKE"
else fail "TTS smoke test skipped" "fix the failures above first"; fi

echo
if [ "$FAILED" -eq 0 ]; then echo "OK: demo-video prerequisites are in place."; exit 0
else echo "NOT READY: fix the FAIL lines above and run this script again."; exit 1; fi
