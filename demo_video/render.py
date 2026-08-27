import os
import subprocess

html_files = {
    'scene1_intro': """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px; height: 1080px;
    background: radial-gradient(circle at 50% 20%, #1e293b 0%, #0b0f19 80%);
    color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 60px 80px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .header { display: flex; justify-content: space-between; align-items: center; }
  .badge {
    background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4);
    color: #38bdf8; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
    letter-spacing: 0.05em; text-transform: uppercase;
  }
  .hackathon-badge {
    background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4);
    color: #c084fc; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }
  .hero { margin-top: 10px; }
  h1 { font-size: 56px; font-weight: 800; letter-spacing: -0.02em; color: #ffffff; }
  h1 span { background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  p.tagline { font-size: 24px; color: #94a3b8; margin-top: 10px; font-style: italic; }
  
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; margin-top: 30px; }
  .card {
    background: rgba(15, 23, 42, 0.75); border-radius: 20px; padding: 35px;
    backdrop-filter: blur(12px); box-shadow: 0 20px 40px rgba(0,0,0,0.5);
  }
  .card.bad { border: 1px solid rgba(239, 68, 68, 0.35); }
  .card.good { border: 1px solid rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.05); }
  .card-title { font-size: 26px; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
  .card.bad .card-title { color: #f87171; }
  .card.good .card-title { color: #34d399; }
  
  ul { list-style: none; }
  li { font-size: 20px; margin-bottom: 16px; display: flex; align-items: flex-start; gap: 14px; line-height: 1.4; color: #cbd5e1; }
  
  .footer-overlay {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }
  .pulse-dot { width: 12px; height: 12px; border-radius: 50%; background: #38bdf8; box-shadow: 0 0 12px #38bdf8; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">K8s Sentinel</div>
    <div class="hackathon-badge">Agent Harness Hackathon · WeMakeDevs × TrueFoundry</div>
  </div>
  
  <div class="hero">
    <h1>Autonomous Kubernetes <span>Incident Triage Agent</span></h1>
    <p class="tagline">&ldquo;An agent that investigates your cluster instead of telling you what to investigate.&rdquo;</p>
  </div>
  
  <div class="grid">
    <div class="card bad">
      <div class="card-title">⚠️ The 3 AM On-Call Problem (Raw LLMs)</div>
      <ul>
        <li>❌ <b>Advice, Not Action:</b> &ldquo;Here are 10 things you could check...&rdquo;</li>
        <li>❌ <b>No Direct Tools:</b> Cannot inspect live pods, logs, or metrics safely</li>
        <li>❌ <b>Unsafe Code:</b> Generated diagnostic scripts run directly on host</li>
        <li>❌ <b>Stateless:</b> Loses context on disconnect; hallucinations bypass safety</li>
      </ul>
    </div>
    
    <div class="card good">
      <div class="card-title">🛡️ The Solution: K8s Sentinel on TrueForge</div>
      <ul>
        <li>✅ <b>Live Cluster Investigation:</b> Deep queries via Kubernetes MCP connector</li>
        <li>✅ <b>Daytona Isolated Sandbox:</b> Python correlation scripts run in quarantine</li>
        <li>✅ <b>Human Approval Gate:</b> Zero premature mutating commands executed</li>
        <li>✅ <b>SQLite Incident Memory:</b> Persistent sessions survive restarts</li>
      </ul>
    </div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Phase 1: Introduction</b> &mdash; Bridging the gap from advisory chatbots to autonomous, safe SRE action</span>
  </div>
</body>
</html>""",

    'scene2_arch': """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px; height: 1080px;
    background: radial-gradient(circle at 50% 15%, #172554 0%, #0b0f19 75%);
    color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 60px 80px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .header { display: flex; justify-content: space-between; align-items: center; }
  .badge {
    background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4);
    color: #38bdf8; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }
  h1 { font-size: 50px; font-weight: 800; color: #ffffff; margin-top: 10px; }
  h1 span { background: linear-gradient(135deg, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  p.subtitle { font-size: 22px; color: #94a3b8; margin-top: 6px; }

  .arch-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 30px; }
  .arch-card {
    background: rgba(15, 23, 42, 0.85); border-radius: 18px; padding: 28px;
    border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 15px 35px rgba(0,0,0,0.5);
    display: flex; flex-direction: column; justify-content: space-between; height: 480px;
  }
  .card-1 { border-top: 5px solid #38bdf8; }
  .card-2 { border-top: 5px solid #818cf8; }
  .card-3 { border-top: 5px solid #c084fc; }
  .card-4 { border-top: 5px solid #34d399; }
  
  .arch-icon { font-size: 38px; margin-bottom: 15px; }
  .arch-title { font-size: 22px; font-weight: 700; color: #f8fafc; margin-bottom: 12px; }
  .arch-desc { font-size: 16px; color: #94a3b8; line-height: 1.5; margin-bottom: 18px; }
  
  .tag-list { display: flex; flex-direction: column; gap: 8px; }
  .tag {
    background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px;
    font-size: 14px; font-family: monospace; color: #cbd5e1; border: 1px solid rgba(255,255,255,0.05);
  }

  .footer-overlay {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }
  .pulse-dot { width: 12px; height: 12px; border-radius: 50%; background: #60a5fa; box-shadow: 0 0 12px #60a5fa; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Architecture Overview</div>
    <div style="color: #94a3b8; font-size: 18px;">TrueForge Harness · Daytona · Kind · Qodo</div>
  </div>
  
  <div>
    <h1>Why TrueForge Is <span>Load-Bearing</span></h1>
    <p class="subtitle">A complete runtime ecosystem designed specifically for mission-critical SRE operations</p>
  </div>
  
  <div class="arch-grid">
    <div class="arch-card card-1">
      <div>
        <div class="arch-icon">⚙️</div>
        <div class="arch-title">TrueForge Harness</div>
        <div class="arch-desc">Single-process Node runtime orchestrating tools, subagents, and sessions.</div>
      </div>
      <div class="tag-list">
        <div class="tag">Dynamic Subagents</div>
        <div class="tag">SQLite Session Store</div>
        <div class="tag">SKILL.md Playbook</div>
      </div>
    </div>
    
    <div class="arch-card card-2">
      <div>
        <div class="arch-icon">🔌</div>
        <div class="arch-title">Kubernetes MCP</div>
        <div class="arch-desc">Streamable HTTP MCP connector providing live cluster introspection.</div>
      </div>
      <div class="tag-list">
        <div class="tag">pods_get / resources_get</div>
        <div class="tag">events_list / logs</div>
        <div class="tag">--disable-destructive</div>
      </div>
    </div>
    
    <div class="arch-card card-3">
      <div>
        <div class="arch-icon">📦</div>
        <div class="arch-title">Daytona Sandbox</div>
        <div class="arch-desc">Isolated code execution container connected via NATS bridge.</div>
      </div>
      <div class="tag-list">
        <div class="tag">Zero Host Network Access</div>
        <div class="tag">Generated Python Scripts</div>
        <div class="tag">Automated Quarantine</div>
      </div>
    </div>
    
    <div class="arch-card card-4">
      <div>
        <div class="arch-icon">🚦</div>
        <div class="arch-title">Human Approval Gate</div>
        <div class="arch-desc">Runtime-enforced barrier intercepting all state-mutating actions.</div>
      </div>
      <div class="tag-list">
        <div class="tag">Plan Text Only</div>
        <div class="tag">mutating: true Flagging</div>
        <div class="tag">Guarded by Qodo Review</div>
      </div>
    </div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Phase 2: Architecture</b> &mdash; Defense-in-depth safety: Read-only MCP + Remote Sandbox + Human Approval Gate</span>
  </div>
</body>
</html>""",

    'scene3a_demo_discovery': """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px; height: 1080px;
    background: #0b0f19; color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 50px 70px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .header { display: flex; justify-content: space-between; align-items: center; }
  .badge {
    background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4);
    color: #f87171; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }
  h1 { font-size: 46px; font-weight: 800; color: #ffffff; margin-top: 8px; }
  h1 span { color: #38bdf8; }
  p.subtitle { font-size: 20px; color: #94a3b8; }

  .split { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 25px; }
  .terminal-window {
    background: #020617; border-radius: 14px; border: 1px solid #1e293b;
    overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); height: 500px;
  }
  .term-bar {
    background: #0f172a; padding: 12px 18px; display: flex; align-items: center; gap: 8px;
    border-bottom: 1px solid #1e293b; font-family: monospace; font-size: 14px; color: #94a3b8;
  }
  .dots { display: flex; gap: 6px; }
  .dot { width: 12px; height: 12px; border-radius: 50%; }
  .dot-r { background: #ef4444; } .dot-y { background: #f59e0b; } .dot-g { background: #10b981; }
  .term-content {
    padding: 20px; font-family: 'SF Mono', Monaco, Consolas, monospace; font-size: 16px;
    line-height: 1.6; color: #e2e8f0; height: calc(100% - 45px); overflow: hidden;
  }
  .text-red { color: #f87171; }
  .text-green { color: #34d399; }
  .text-yellow { color: #fbbf24; }
  .text-cyan { color: #38bdf8; }

  .footer-overlay {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }
  .pulse-dot { width: 12px; height: 12px; border-radius: 50%; background: #ef4444; box-shadow: 0 0 12px #ef4444; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Live Demo · Step 1</div>
    <div style="color: #94a3b8; font-size: 18px;">Cluster: sentinel-demo (kind)</div>
  </div>
  
  <div>
    <h1>Chaos Injection &amp; <span>Discovery Phase</span></h1>
    <p class="subtitle">Injecting real CrashLoopBackOff into payments-api deployment</p>
  </div>
  
  <div class="split">
    <div class="terminal-window">
      <div class="term-bar">
        <div class="dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
        <span style="margin-left: 10px;">bash &mdash; chaos/scenarios/crashloop.py</span>
      </div>
      <div class="term-content">
        <span class="text-cyan">$</span> python3 chaos/scenarios/crashloop.py<br>
        <span class="text-yellow">[CHAOS]</span> Corrupted nginx config in ConfigMap nginx-healthz<br>
        <span class="text-yellow">[CHAOS]</span> Triggering pod rolling restart...<br>
        <span class="text-yellow">[CHAOS]</span> Expected within ~60s: all replicas in CrashLoopBackOff.<br><br>
        <span class="text-cyan">$</span> kubectl -n demo get pods<br>
        NAME &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; READY &nbsp; STATUS &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; RESTARTS<br>
        payments-api-5fcf89c9cc-ghh7m &nbsp; <span class="text-red">0/1 &nbsp;&nbsp; CrashLoopBackOff &nbsp; 2 (14s ago)</span><br>
        payments-api-76bfc8b48c-cv5n8 &nbsp; 1/1 &nbsp;&nbsp; Running &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0<br>
        payments-api-76bfc8b48c-mr8fz &nbsp; 1/1 &nbsp;&nbsp; Running &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 0
      </div>
    </div>
    
    <div class="terminal-window">
      <div class="term-bar">
        <div class="dots"><div class="dot dot-r"></div><div class="dot dot-y"></div><div class="dot dot-g"></div></div>
        <span style="margin-left: 10px;">TrueForge Agent Session &mdash; 01m1199y92m775hj5w89sezv0a</span>
      </div>
      <div class="term-content">
        <span class="text-cyan">User Prompt:</span><br>
        &ldquo;Investigate: payments pods are crash-looping in namespace demo.&rdquo;<br><br>
        <span class="text-green">Agent Autonomous Action [Phase 1 - DISCOVER]:</span><br>
        <span class="text-yellow">&rarr; MCP Tool Call:</span> kubernetes.resources_list(kind=&ldquo;ConfigMap&rdquo;, namespace=&ldquo;demo&rdquo;)<br>
        &nbsp;&nbsp;&bull; Found ConfigMaps: app-config, nginx-healthz<br><br>
        <span class="text-yellow">&rarr; MCP Tool Call:</span> kubernetes.pods_get(name=&ldquo;payments-api-5fcf89c9cc-ghh7m&rdquo;)<br>
        &nbsp;&nbsp;&bull; status: ContainerStatuses.state = Waiting(CrashLoopBackOff)<br>
        &nbsp;&nbsp;&bull; lastTermination: ExitCode 1 (Container failed on start)
      </div>
    </div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Live Execution:</b> TrueForge discovers the crash-looping pod and begins multi-hop MCP introspection</span>
  </div>
</body>
</html>""",

    'scene3b_demo_sandbox': """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px; height: 1080px;
    background: #0b0f19; color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 50px 70px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .header { display: flex; justify-content: space-between; align-items: center; }
  .badge {
    background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4);
    color: #c084fc; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }
  h1 { font-size: 46px; font-weight: 800; color: #ffffff; margin-top: 8px; }
  h1 span { color: #f43f5e; }
  p.subtitle { font-size: 20px; color: #94a3b8; }

  .split { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 25px; }
  .box {
    background: #020617; border-radius: 14px; border: 1px solid #1e293b;
    overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); height: 500px; padding: 25px;
  }
  .box-title { font-size: 22px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
  .code-block {
    background: #0f172a; padding: 20px; border-radius: 10px; border: 1px solid #334155;
    font-family: monospace; font-size: 16px; line-height: 1.6; color: #cbd5e1;
  }
  .smoking-gun {
    background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.5);
    color: #fca5a5; padding: 4px 8px; border-radius: 4px; font-weight: bold;
  }
  .highlight-box {
    background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 15px; border-radius: 10px; margin-top: 15px; font-size: 16px; color: #e2e8f0; line-height: 1.5;
  }

  .footer-overlay {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }
  .pulse-dot { width: 12px; height: 12px; border-radius: 50%; background: #f43f5e; box-shadow: 0 0 12px #f43f5e; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Live Demo · Step 2</div>
    <div style="color: #94a3b8; font-size: 18px;">Daytona Remote Sandbox Isolation</div>
  </div>
  
  <div>
    <h1>Sandbox Analysis &amp; <span>Smoking Gun Found</span></h1>
    <p class="subtitle">Correlating event logs in Daytona and isolating the invalid ConfigMap key</p>
  </div>
  
  <div class="split">
    <div class="box">
      <div class="box-title" style="color: #c084fc;">📦 Daytona Remote Sandbox</div>
      <div class="code-block">
        <b>NATS Transport:</b> Connected to sandbox.bridge<br>
        <b>Isolation Check:</b> Code runs inside isolated container<br>
        <b>Action:</b> Python script parsed pod event history<br><br>
        <span style="color: #94a3b8;"># Quarantine Boundary Verified:</span><br>
        Host Kind Cluster (<span style="color: #38bdf8;">127.0.0.1:57595</span>) is unreachable from Daytona container.<br>
        <span style="color: #34d399;">✓ Untrusted execution completely isolated from host.</span>
      </div>
      <div class="highlight-box">
        <b>Phase 4 (Sandboxed Execution):</b> When correlation is needed, Sentinel generates analysis code that runs off-host.
      </div>
    </div>
    
    <div class="box">
      <div class="box-title" style="color: #f87171;">🎯 The Smoking Gun (Located by Agent)</div>
      <div class="code-block">
        <span style="color: #94a3b8;"># Kubernetes MCP query: resources_get(nginx-healthz)</span><br>
        server {<br>
        &nbsp;&nbsp;listen 80;<br>
        &nbsp;&nbsp;<span class="smoking-gun">this_directive_does_not_exist 42;  &larr; LINE 3 ERROR</span><br>
        &nbsp;&nbsp;location = /healthz {<br>
        &nbsp;&nbsp;&nbsp;&nbsp;return 200 &ldquo;ok\n&rdquo;;<br>
        &nbsp;&nbsp;}<br>
        }
      </div>
      <div class="highlight-box" style="border-color: rgba(239, 68, 68, 0.4);">
        <b>Agent Diagnosis:</b> Nginx fails startup with <i>[emerg] unknown directive</i>, causing probe failure and CrashLoopBackOff.
      </div>
    </div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Live Execution:</b> Daytona container quarantines script execution while Sentinel isolates root cause</span>
  </div>
</body>
</html>""",

    'scene3c_demo_approval': """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    width: 1920px; height: 1080px;
    background: #0b0f19; color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    padding: 50px 70px; display: flex; flex-direction: column; justify-content: space-between;
  }
  .header { display: flex; justify-content: space-between; align-items: center; }
  .badge {
    background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4);
    color: #34d399; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }
  h1 { font-size: 46px; font-weight: 800; color: #ffffff; margin-top: 8px; }
  h1 span { color: #34d399; }
  p.subtitle { font-size: 20px; color: #94a3b8; }

  .split { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 30px; margin-top: 25px; }
  .box {
    background: #020617; border-radius: 14px; border: 1px solid #1e293b;
    overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.6); height: 500px; padding: 25px;
  }
  .box-title { font-size: 22px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
  .code-block {
    background: #0f172a; padding: 18px; border-radius: 10px; border: 1px solid #334155;
    font-family: monospace; font-size: 15px; line-height: 1.5; color: #cbd5e1;
  }
  .gate-badge {
    background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; color: #fbbf24;
    padding: 4px 10px; border-radius: 6px; font-size: 14px; font-weight: bold;
  }

  .footer-overlay {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }
  .pulse-dot { width: 12px; height: 12px; border-radius: 50%; background: #10b981; box-shadow: 0 0 12px #10b981; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Live Demo · Step 3</div>
    <div style="color: #94a3b8; font-size: 18px;">TrueForge Approval Gate &amp; SQLite Persistence</div>
  </div>
  
  <div>
    <h1>Approval Gate &amp; <span>Cross-Session Recall</span></h1>
    <p class="subtitle">Safe gated remediation and instant SQLite memory without re-queries</p>
  </div>
  
  <div class="split">
    <div class="box">
      <div class="box-title" style="color: #f59e0b;">
        <span>🚦 Human Approval Gate</span>
        <span class="gate-badge">REQUIRES_APPROVAL</span>
      </div>
      <div class="code-block">
        <span style="color: #38bdf8;"># Proposed Fix formulated by Sentinel:</span><br>
        kubectl patch configmap nginx-healthz -n demo --type merge \\<br>
        &nbsp;&nbsp;-p '{"data":{"default.conf":"server { listen 80; ... }"}}'<br><br>
        kubectl rollout restart deployment/payments-api -n demo<br><br>
        <span style="color: #34d399;">✓ Zero mutation executed pre-approval</span><br>
        <span style="color: #94a3b8;">State diff before vs after: 0 bytes drifted until operator confirms.</span>
      </div>
      <p style="color: #94a3b8; margin-top: 15px; font-size: 15px;">
        TrueForge strictly enforces approval gates on all mutating verbs. The agent proposes the fix; the human decides.
      </p>
    </div>
    
    <div class="box">
      <div class="box-title" style="color: #38bdf8;">🧠 SQLite Cross-Session Recall</div>
      <div class="code-block">
        <span style="color: #38bdf8;">User Follow-up Turn:</span><br>
        &ldquo;In one sentence, what was the exact root cause?&rdquo;<br><br>
        <span style="color: #34d399;">Agent Verbatim Recall (Zero MCP queries):</span><br>
        &ldquo;The payments-api pods were crash-looping because the nginx-healthz ConfigMap contained invalid directive 'this_directive_does_not_exist 42;' in default.conf:3...&rdquo;
      </div>
      <p style="color: #94a3b8; margin-top: 15px; font-size: 15px;">
        Reconstructed directly from SQLite (<code>turn</code> and <code>thread_context_log</code>). Full incident memory persists across sessions!
      </p>
    </div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Verified Invariant:</b> No unauthorized changes to production + permanent SRE incident memory</span>
  </div>
</body>
</html>""",

    'scene4_learnings': """<!DOCTYPE html>
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
    background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.4);
    color: #c084fc; padding: 8px 18px; border-radius: 9999px; font-weight: 600; font-size: 18px;
  }
  h1 { font-size: 46px; font-weight: 800; color: #ffffff; margin-top: 8px; }
  h1 span { background: linear-gradient(135deg, #a78bfa, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  p.subtitle { font-size: 20px; color: #94a3b8; }

  .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; margin-top: 25px; }
  .card {
    background: rgba(15, 23, 42, 0.85); border-radius: 16px; padding: 25px;
    border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 15px 35px rgba(0,0,0,0.5);
  }
  .card-icon { font-size: 32px; margin-bottom: 12px; }
  .card-title { font-size: 20px; font-weight: 700; color: #f8fafc; margin-bottom: 10px; }
  .card-text { font-size: 15px; color: #94a3b8; line-height: 1.5; }

  .cta-banner {
    background: linear-gradient(90deg, rgba(56, 189, 248, 0.1), rgba(139, 92, 246, 0.1));
    border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 14px; padding: 18px 30px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .cta-text { font-size: 20px; font-weight: 600; color: #ffffff; }
  .cta-link { font-family: monospace; color: #38bdf8; font-size: 20px; }

  .footer-overlay {
    background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(255,255,255,0.1);
    padding: 16px 28px; border-radius: 14px; font-size: 20px; font-weight: 500;
    color: #e2e8f0; display: flex; align-items: center; gap: 12px;
  }
  .pulse-dot { width: 12px; height: 12px; border-radius: 50%; background: #c084fc; box-shadow: 0 0 12px #c084fc; }
</style>
</head>
<body>
  <div class="header">
    <div class="badge">Takeaways &amp; Conclusion</div>
    <div style="color: #94a3b8; font-size: 18px;">Q Branch Track (Qodo) · Double-O Track (TrueForge)</div>
  </div>
  
  <div>
    <h1>Key Learnings &amp; <span>Production Standards</span></h1>
    <p class="subtitle">Real problems solved while building autonomous infrastructure agents</p>
  </div>
  
  <div class="grid">
    <div class="card" style="border-top: 4px solid #38bdf8;">
      <div class="card-icon">🛡️</div>
      <div class="card-title">Sandbox Quarantine</div>
      <div class="card-text">
        Daytona ensures generated correlation scripts run off-host. Untrusted code cannot touch cluster loopback networks or API server credentials directly.
      </div>
    </div>
    
    <div class="card" style="border-top: 4px solid #f59e0b;">
      <div class="card-icon">⏱️</div>
      <div class="card-title">Handling Timing Races</div>
      <div class="card-text">
        K8s events arrive asynchronously after pod status changes. Hardened retry loops and multi-phase status matching eliminate flakiness in validation.
      </div>
    </div>
    
    <div class="card" style="border-top: 4px solid #10b981;">
      <div class="card-icon">✅</div>
      <div class="card-title">Guarded by Qodo</div>
      <div class="card-text">
        All PRs reviewed with full repo context. Enforced ShellCheck POSIX standards, Bash set -euo pipefail safety, and zero-secrets hygiene.
      </div>
    </div>
  </div>
  
  <div class="cta-banner">
    <div class="cta-text">Explore the complete source code &amp; live test suites:</div>
    <div class="cta-link">github.com/gitanshulbisht/k8s-sentinel</div>
  </div>
  
  <div class="footer-overlay">
    <div class="pulse-dot"></div>
    <span><b>Conclusion:</b> Built with TrueForge by TrueFoundry · Quality Guarded by Qodo · Thank you!</span>
  </div>
</body>
</html>"""
}

for name, html in html_files.items():
    html_path = f'demo_video/slides/{name}.html'
    png_path = f'demo_video/slides/{name}.png'
    with open(html_path, 'w') as f:
        f.write(html.strip())
    cmd = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '--headless',
        '--disable-gpu',
        f'--screenshot={png_path}',
        '--window-size=1920,1080',
        f'file://{os.path.abspath(html_path)}'
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    print(f'Rendered {png_path} ({os.path.getsize(png_path)} bytes)')
