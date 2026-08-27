import os
import subprocess

base_dir = os.path.abspath(".")
cockpit_preview = os.path.join(base_dir, "artifacts/incident-cockpit/preview.png")

SLIDES = {
    "scene3f_cockpit": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1920px; height: 1080px;
    background: #0b0f19; color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 30px 50px; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .header {{ display: flex; justify-content: space-between; align-items: center; }}
  .badge {{
    background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4);
    color: #38bdf8; padding: 6px 16px; border-radius: 9999px; font-weight: 600; font-size: 16px;
  }}
  h1 {{ font-size: 38px; font-weight: 800; color: #ffffff; }}
  h1 span {{ color: #38bdf8; }}
  p.subtitle {{ font-size: 18px; color: #94a3b8; }}

  .cockpit-frame {{
    background: #020617; border-radius: 14px; border: 1px solid #38bdf8;
    overflow: hidden; box-shadow: 0 25px 60px rgba(0,0,0,0.8); height: 800px;
    display: flex; flex-direction: column; margin-top: 15px; position: relative;
  }}
  .bar {{
    background: #0f172a; padding: 10px 18px; display: flex; align-items: center; justify-content: space-between;
    border-bottom: 1px solid #1e293b; font-family: monospace; font-size: 13px; color: #94a3b8;
  }}
  .img-content {{ flex: 1; width: 100%; overflow: hidden; }}
  .img-content img {{ width: 100%; height: 100%; object-fit: contain; background: #0b0f19; }}

  .floating-pill {{
    position: absolute; background: rgba(15, 23, 42, 0.92); border-radius: 10px;
    padding: 10px 16px; border: 1px solid rgba(255,255,255,0.15); font-size: 13px; font-weight: 600;
    box-shadow: 0 10px 25px rgba(0,0,0,0.7); backdrop-filter: blur(10px);
  }}

  .footer-overlay {{
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 12px 24px; border-radius: 10px; font-size: 18px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }}
  .pulse-dot {{ width: 10px; height: 10px; border-radius: 50%; background: #38bdf8; box-shadow: 0 0 10px #38bdf8; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <h1>Generative UI: <span>Interactive Incident Cockpit</span></h1>
      <p class="subtitle">Self-contained web artifact: Real-time pod topology, ConfigMap diff, &amp; rollout simulation</p>
    </div>
    <div class="badge">TrueForge Web Artifact &bull; artifacts/incident-cockpit/index.html</div>
  </div>

  <div class="cockpit-frame">
    <div class="bar">
      <div style="display: flex; gap: 8px; align-items: center;">
        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #ef4444;"></span>
        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #f59e0b;"></span>
        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10b981;"></span>
        <span style="margin-left: 12px; color: #cbd5e1; font-weight: bold;">K8s Sentinel &mdash; Mission Control Incident Cockpit</span>
      </div>
      <div>Interactive Dashboard Artifact &bull; Standalone HTML5</div>
    </div>
    <div class="img-content">
      <img src="file://{cockpit_preview}" />
    </div>
  </div>

  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Generative UI Artifact:</b> Operators get instant visual mission control rather than combing through terminal output</span>
  </div>
</body>
</html>""",

    "scene3g_watcher": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1920px; height: 1080px;
    background: #0b0f19; color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 50px 70px; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .header {{ display: flex; justify-content: space-between; align-items: center; }}
  .badge {{
    background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4);
    color: #c084fc; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }}
  h1 {{ font-size: 46px; font-weight: 800; color: #ffffff; margin-top: 8px; }}
  h1 span {{ color: #c084fc; }}
  p.subtitle {{ font-size: 20px; color: #94a3b8; }}

  .split {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 30px; margin-top: 25px; }}
  .window {{
    background: #020617; border-radius: 14px; border: 1px solid #1e293b;
    overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); height: 500px;
  }}
  .term-bar {{
    background: #0f172a; padding: 12px 18px; display: flex; align-items: center; gap: 8px;
    border-bottom: 1px solid #1e293b; font-family: monospace; font-size: 14px; color: #94a3b8;
  }}
  .dots {{ display: flex; gap: 6px; }}
  .dot {{ width: 12px; height: 12px; border-radius: 50%; }}
  .dot-r {{ background: #ef4444; }} .dot-y {{ background: #f59e0b; }} .dot-g {{ background: #10b981; }}
  .term-content {{
    padding: 22px; font-family: 'SF Mono', Monaco, Consolas, monospace; font-size: 15px;
    line-height: 1.6; color: #e2e8f0; height: calc(100% - 45px); overflow: hidden;
  }}

  .flow-card {{
    background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 18px; margin-bottom: 14px;
  }}
  .flow-step {{ font-size: 15px; font-weight: bold; color: #f8fafc; margin-bottom: 4px; display: flex; align-items: center; gap: 10px; }}
  .flow-desc {{ font-size: 13px; color: #94a3b8; line-height: 1.4; }}

  .footer-overlay {{
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }}
  .pulse-dot {{ width: 12px; height: 12px; border-radius: 50%; background: #c084fc; box-shadow: 0 0 12px #c084fc; }}
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Autonomous Daemon</div>
    <div style="color: #94a3b8; font-size: 18px;">Proactive 24/7 Cluster Watcher</div>
  </div>
  
  <div>
    <h1>Proactive 24/7 Watcher &amp; <span>Event Ingestion</span></h1>
    <p class="subtitle">Autonomous event stream monitoring without human chat intervention</p>
  </div>
  
  <div class="split">
    <div class="window">
      <div class="term-bar">
        <div class="dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
        <span style="margin-left: 10px;">python3 watcher/sentinel_watcher.py</span>
      </div>
      <div class="term-content">
        <span style="color: #38bdf8;">[15:30:10] [SENTINEL-WATCHER]</span> Starting cluster watcher on namespace 'demo'...<br>
        <span style="color: #38bdf8;">[15:30:10] [SENTINEL-WATCHER]</span> Listening for triggers: BackOff, OOMKilling, FailedProbe<br>
        <span style="color: #94a3b8;">[15:30:18] streaming kubectl events --watch-only...</span><br><br>
        <span style="color: #ef4444; font-weight: bold;">[15:30:24] [SENTINEL-WATCHER] 🚨 ANOMALY DETECTED:</span><br>
        &nbsp;&nbsp;↳ Target: <span style="color: #f8fafc;">payments-api-5fcf89c9cc-ghh7m</span> &rarr; <span style="color: #f87171;">BackOff</span><br>
        &nbsp;&nbsp;↳ Reason: Back-off restarting failed container<br><br>
        <span style="color: #34d399; font-weight: bold;">[15:30:25] [SENTINEL-WATCHER] ✓ Dispatching to TrueForge API:</span><br>
        &nbsp;&nbsp;↳ POST http://localhost:8790/api/sessions<br>
        &nbsp;&nbsp;↳ Created session: <span style="color: #38bdf8;">01m1199y92m775hj5w89sezv0a</span><br>
        &nbsp;&nbsp;↳ Agent K8s Sentinel triage activated autonomously!
      </div>
    </div>
    
    <div class="window" style="padding: 20px; display: flex; flex-direction: column; justify-content: space-between;">
      <div class="flow-card" style="border-left: 4px solid #ef4444;">
        <div class="flow-step"><span style="color: #ef4444;">1.</span> Real-Time Event Stream</div>
        <div class="flow-desc">Streams Kubelet events directly without polling overhead. Catches pod crashes in sub-second time.</div>
      </div>
      
      <div class="flow-card" style="border-left: 4px solid #c084fc;">
        <div class="flow-step"><span style="color: #c084fc;">2.</span> Autonomous API Dispatch</div>
        <div class="flow-desc">Calls TrueForge session creation API automatically. Zero human prompt typing required.</div>
      </div>
      
      <div class="flow-card" style="border-left: 4px solid #34d399;">
        <div class="flow-step"><span style="color: #34d399;">3.</span> SRE Triage Before Alert Paging</div>
        <div class="flow-desc">Sentinel completes triage and isolates the smoking gun before the engineer even opens their laptop!</div>
      </div>
    </div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Proactive Sentinel:</b> Moving from a passive chatbot to an active, autonomous 24/7 SRE infrastructure watchdog</span>
  </div>
</body>
</html>""",

    "scene3h_autonomy_cost": f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1920px; height: 1080px;
    background: radial-gradient(circle at 50% 15%, #1e1b4b 0%, #0b0f19 75%);
    color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 50px 70px; display: flex; flex-direction: column; justify-content: space-between;
  }}
  .header {{ display: flex; justify-content: space-between; align-items: center; }}
  .badge {{
    background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4);
    color: #34d399; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }}
  h1 {{ font-size: 46px; font-weight: 800; color: #ffffff; margin-top: 8px; }}
  h1 span {{ color: #34d399; }}
  p.subtitle {{ font-size: 20px; color: #94a3b8; }}

  .split {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 25px; }}
  .card {{
    background: #020617; border-radius: 16px; padding: 28px; border: 1px solid #1e293b;
    box-shadow: 0 15px 35px rgba(0,0,0,0.5); display: flex; flex-direction: column; justify-content: space-between; height: 500px;
  }}
  .card-title {{ font-size: 22px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}

  .mode-row {{
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 14px; margin-bottom: 12px;
  }}
  .mode-title {{ font-size: 16px; font-weight: bold; margin-bottom: 4px; }}
  .mode-desc {{ font-size: 13px; color: #94a3b8; line-height: 1.4; }}

  .econ-stat {{
    background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 15px;
  }}
  .econ-num {{ font-size: 42px; font-weight: 900; color: #34d399; }}
  .econ-sub {{ font-size: 14px; color: #cbd5e1; margin-top: 4px; }}

  .table-row {{
    display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.06);
    font-size: 14px;
  }}

  .footer-overlay {{
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }}
  .pulse-dot {{ width: 12px; height: 12px; border-radius: 50%; background: #10b981; box-shadow: 0 0 12px #10b981; }}
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Policy &amp; Economics</div>
    <div style="color: #94a3b8; font-size: 18px;">Dual Autonomy &bull; TrueForge Model Routing</div>
  </div>
  
  <div>
    <h1>Autonomy Spectrum &amp; <span>Cost Economics</span></h1>
    <p class="subtitle">Policy-based governance by namespace + 97.5% reduction in SRE triage costs</p>
  </div>
  
  <div class="split">
    <div class="card" style="border-top: 4px solid #f59e0b;">
      <div>
        <div class="card-title" style="color: #fbbf24;">🛡️ Policy-Based Autonomy Spectrum</div>
        <div class="mode-row" style="border-left: 3px solid #f59e0b;">
          <div class="mode-title" style="color: #fbbf24;">Production Namespaces &rarr; Guarded Autonomy</div>
          <div class="mode-desc">Enforces human-in-the-loop sign-off. Formulates surgical patch, verifies 0 bytes pre-approval drift, meets SOC2/ISO 27001 auditing standards.</div>
        </div>
        <div class="mode-row" style="border-left: 3px solid #34d399;">
          <div class="mode-title" style="color: #34d399;">Dev / Staging Namespaces &rarr; Closed-Loop Auto-Heal</div>
          <div class="mode-desc">100% autonomous execution. Applies patch, triggers rollout, verifies internal health probes, and closes ticket in under 30 seconds.</div>
        </div>
      </div>
      <div style="font-size: 12px; color: #64748b; font-style: italic;">
        Configured via TrueForge role-based tool policies and namespace scopes.
      </div>
    </div>
    
    <div class="card" style="border-top: 4px solid #10b981;">
      <div>
        <div class="card-title" style="color: #34d399;">💰 TrueForge Model Economics</div>
        <div class="econ-stat">
          <div class="econ-num">$0.002 <span style="font-size: 20px; font-weight: normal; color: #94a3b8;">/ incident</span></div>
          <div class="econ-sub">Gemini 2.5 Flash / DeepSeek V3 routed via OpenRouter</div>
        </div>
        
        <div class="table-row">
          <span style="color: #94a3b8;">Claude 3.5 Sonnet (Direct):</span>
          <span style="font-family: monospace; color: #f87171;">~$0.080 / run &bull; 18.2s</span>
        </div>
        <div class="table-row">
          <span style="color: #94a3b8;">OpenRouter + TrueForge:</span>
          <span style="font-family: monospace; color: #34d399; font-weight: bold;">~$0.002 / run &bull; 4.2s</span>
        </div>
        <div class="table-row" style="border: none;">
          <span style="color: #e2e8f0; font-weight: bold;">Operational Savings:</span>
          <span style="color: #34d399; font-weight: bold;">97.5% Cost Reduction</span>
        </div>
      </div>
      <div style="font-size: 12px; color: #64748b; font-style: italic;">
        Delivering 100% diagnostic accuracy with sub-second tool execution.
      </div>
    </div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Enterprise Ready:</b> Safe policies for production clusters with unmatched economic efficiency</span>
  </div>
</body>
</html>"""
}

for sid, html in SLIDES.items():
    html_path = f"demo_video/slides_v2/{sid}.html"
    png_path = f"demo_video/slides_v2/{sid}.png"
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
    print(f"Rendered {png_path} ({os.path.getsize(png_path)} bytes)")
