# Windows setup for the demo-video skill. Best effort, untested on Windows. Mirrors scripts/setup.sh.
$ErrorActionPreference = 'Stop'
$tts = if ($env:DEMO_VIDEO_HOME) { $env:DEMO_VIDEO_HOME } else { Join-Path $env:USERPROFILE '.local\share\demo-video-tts' }
$venv = Join-Path $tts 'venv'
$node = Join-Path $tts 'node'
$rel = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0'
function Need($cmd, $fix) { if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { Write-Host "FAIL $cmd not found. Fix: $fix"; exit 1 } else { Write-Host "OK   $cmd" } }
Need ffmpeg 'winget install Gyan.FFmpeg'
Need node 'winget install OpenJS.NodeJS'
$py = $null
foreach ($v in '3.14', '3.13', '3.12') { & py "-$v" --version 2>$null; if ($LASTEXITCODE -eq 0) { $py = $v; break } }
if (-not $py) { Write-Host 'FAIL no Python 3.12 to 3.14 (3.15 or newer has no onnxruntime wheels). Fix: winget install Python.Python.3.14'; exit 1 }
New-Item -ItemType Directory -Force $tts | Out-Null
if (-not (Test-Path "$venv\Scripts\python.exe")) { & py "-$py" -m venv $venv }
& "$venv\Scripts\pip" install --quiet kokoro-onnx soundfile pillow numpy
foreach ($f in @(@('kokoro-v1.0.onnx', 300e6), @('voices-v1.0.bin', 20e6))) {
  $p = Join-Path $tts $f[0]
  if (-not (Test-Path $p) -or (Get-Item $p).Length -lt $f[1]) { Invoke-WebRequest "$rel/$($f[0])" -OutFile $p }
  if ((Get-Item $p).Length -lt $f[1]) { Write-Host "FAIL $($f[0]) too small"; exit 1 }
}
New-Item -ItemType Directory -Force $node | Out-Null
Push-Location $node
if (-not (Test-Path package.json)) { '{"private":true}' | Out-File package.json -Encoding ascii }
npm install --silent playwright-core; npx -y playwright install chromium
Pop-Location
$test = Join-Path $env:TEMP 'demo-video-smoke.wav'
& "$venv\Scripts\python" -c "import sys,soundfile as sf; from kokoro_onnx import Kokoro; m=sys.argv[1]; a,sr=Kokoro(m+'/kokoro-v1.0.onnx',m+'/voices-v1.0.bin').create('Hello from the demo video skill.',voice='af_heart',speed=1.0,lang='en-us'); sf.write(sys.argv[2],a,sr)" $tts $test
if ($LASTEXITCODE -ne 0) { Write-Host 'FAIL TTS smoke test'; exit 1 }
Write-Host 'OK: demo-video prerequisites are in place.'
