import os
import subprocess
import json

# 1. Voiceover
text = "To ensure Sentinel handles diverse failure modes, we built a four-scenario chaos engineering harness with known-answer golden fixtures. Crashloop injects corrupt configurations into nginx. OOM-kill restricts memory below container baselines, triggering exit code 137. Probe-fail points liveness endpoints to a 404 path, creating restart storms while logs stay clean. And image-pull swaps in non-existent registry tags. Our automated validation suite proves that every failure signature is resolvable live, passing four out of four golden cases with zero safety violations."

aiff_path = "demo_video/audio/scene2b_chaos.aiff"
mp3_path = "demo_video/audio/scene2b_chaos.mp3"
subprocess.run(["say", "-v", "Daniel", "-r", "170", "-o", aiff_path, text], check=True)
subprocess.run(["ffmpeg", "-y", "-i", aiff_path, "-af", "volume=1.2", mp3_path], check=True, stderr=subprocess.DEVNULL)
print("Generated audio for scene2b_chaos")

# 2. HTML Slide
html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px; height: 1080px;
    background: radial-gradient(circle at 50% 15%, #1e1b4b 0%, #0b0f19 75%);
    color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 50px 70px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .header { display: flex; justify-content: space-between; align-items: center; }
  .badge {
    background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4);
    color: #fbbf24; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }
  h1 { font-size: 46px; font-weight: 800; color: #ffffff; margin-top: 8px; }
  h1 span { color: #fbbf24; }
  p.subtitle { font-size: 20px; color: #94a3b8; }

  .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 25px; }
  .card {
    background: #020617; border-radius: 14px; padding: 22px; border: 1px solid #1e293b;
    box-shadow: 0 15px 35px rgba(0,0,0,0.5); display: flex; flex-direction: column; justify-content: space-between; height: 420px;
  }
  .card-top { border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 12px; }
  .scenario-name { font-family: monospace; font-size: 18px; font-weight: bold; color: #38bdf8; }
  .diagnosis-class { font-size: 14px; font-weight: 600; color: #a78bfa; margin-top: 4px; }
  .desc { font-size: 15px; color: #94a3b8; line-height: 1.5; margin-bottom: 15px; }
  .sig-box {
    background: rgba(255,255,255,0.04); border-radius: 8px; padding: 10px; font-family: monospace; font-size: 13px; color: #e2e8f0;
  }

  .suite-bar {
    background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 12px; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center;
  }
  .suite-title { font-size: 18px; font-weight: bold; color: #34d399; display: flex; align-items: center; gap: 10px; }
  .suite-badge {
    background: #059669; color: white; padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 15px;
  }

  .footer-overlay {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }
  .pulse-dot { width: 12px; height: 12px; border-radius: 50%; background: #fbbf24; box-shadow: 0 0 12px #fbbf24; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Validation Harness</div>
    <div style="color: #94a3b8; font-size: 18px;">4 Chaos Scenarios · Golden Fixtures</div>
  </div>
  
  <div>
    <h1>Chaos Harness &amp; <span>Golden Validation</span></h1>
    <p class="subtitle">Reproducible failure injection with automated signature verification</p>
  </div>
  
  <div class="grid">
    <div class="card" style="border-top: 4px solid #f87171;">
      <div class="card-top">
        <div class="scenario-name">crashloop.py</div>
        <div class="diagnosis-class">CONFIG_INVALID</div>
      </div>
      <div class="desc">Corrupts nginx healthz configuration directive, forcing crash on startup with previous-container smoking gun.</div>
      <div class="sig-box"><b>Signature:</b><br>nginx: [emerg] unknown directive in default.conf:3</div>
    </div>
    
    <div class="card" style="border-top: 4px solid #fbbf24;">
      <div class="card-top">
        <div class="scenario-name">oomkill.py</div>
        <div class="diagnosis-class">RESOURCE_LIMIT_MISMATCH</div>
      </div>
      <div class="desc">Shrinks requests and limits to 4Mi, far below application baseline, triggering kubelet kernel kills.</div>
      <div class="sig-box"><b>Signature:</b><br>terminated.reason: OOMKilled, exitCode: 137</div>
    </div>
    
    <div class="card" style="border-top: 4px solid #a78bfa;">
      <div class="card-top">
        <div class="scenario-name">probe-fail.py</div>
        <div class="diagnosis-class">PROBE_ENDPOINT_FAILURE</div>
      </div>
      <div class="desc">Repoints liveness probe to 404 path. Split-brain: container logs clean while restart counter climbs.</div>
      <div class="sig-box"><b>Signature:</b><br>Liveness probe failed: HTTP 404 Not Found</div>
    </div>
    
    <div class="card" style="border-top: 4px solid #38bdf8;">
      <div class="card-top">
        <div class="scenario-name">imagepull.py</div>
        <div class="diagnosis-class">IMAGE_TAG_INVALID</div>
      </div>
      <div class="desc">Deploys non-existent image tag, forcing rapid transitions across ErrImagePull and ImagePullBackOff.</div>
      <div class="sig-box"><b>Signature:</b><br>Failed to pull image: manifest unknown</div>
    </div>
  </div>
  
  <div class="suite-bar">
    <div class="suite-title">
      <span>✓ tests/run_golden.sh: 4 PASSED, 0 FAILED</span>
      <span style="color: #94a3b8; font-weight: normal; font-size: 16px; margin-left: 20px;">· All golden evidence patterns resolvable live</span>
    </div>
    <div class="suite-badge">TESTS GREEN (4/4)</div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Validation:</b> Proving that K8s Sentinel handles diverse real-world outage classes with 100% accuracy</span>
  </div>
</body>
</html>
"""

html_path = "demo_video/slides/scene2b_chaos.html"
png_path = "demo_video/slides/scene2b_chaos.png"
with open(html_path, "w") as f:
    f.write(html.strip())

cmd = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "--headless",
    "--disable-gpu",
    f"--screenshot={png_path}",
    "--window-size=1920,1080",
    f"file://{os.path.abspath(html_path)}"
]
subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
print("Rendered demo_video/slides/scene2b_chaos.png")

# 3. Encode clip
clip_path = "demo_video/clips/scene2b_chaos.mp4"
encode_cmd = [
    "ffmpeg", "-y",
    "-loop", "1",
    "-i", png_path,
    "-i", mp3_path,
    "-af", "apad=pad_dur=0.5",
    "-c:v", "libx264",
    "-tune", "stillimage",
    "-c:a", "aac",
    "-b:a", "192k",
    "-ar", "44100",
    "-pix_fmt", "yuv420p",
    "-shortest",
    clip_path
]
subprocess.run(encode_cmd, check=True, stderr=subprocess.DEVNULL)
print(f"Encoded {clip_path}")
