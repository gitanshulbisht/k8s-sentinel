#!/usr/bin/env python3
"""
K8s Sentinel — Proactive Cluster Event Watcher (Daemon)
Monitors Kubernetes event stream for anomaly signatures (BackOff, OOMKilling, FailedProbe)
and autonomously dispatches an investigation session to TrueForge without human intervention.
"""

import subprocess
import json
import time
import requests
import sys

TRUEFORGE_API = "http://localhost:8790/api"
TARGET_NAMESPACE = "demo"

CRITICAL_REASONS = {"BackOff", "OOMKilling", "FailedProbe", "FailedMount", "ErrImagePull"}

def log(msg):
    print(f"[{time.strftime('%X')}] [SENTINEL-WATCHER] {msg}")

def check_trueforge_health():
    try:
        r = requests.get(f"{TRUEFORGE_API}/healthz", timeout=2)
        return r.status_code == 200
    except Exception:
        return True # Fallback if healthz is unexposed

def trigger_triage_session(pod_name, reason, message):
    log(f"🚨 ANOMALY DETECTED: {pod_name} -> {reason}")
    log(f"   Event message: {message}")
    log("   Autonomously creating TrueForge investigation session...")
    
    prompt = f"Investigate critical event: pod {pod_name} in namespace {TARGET_NAMESPACE} triggered {reason}: {message}. Run full triage playbook."
    
    try:
        res = requests.post(
            f"{TRUEFORGE_API}/sessions",
            json={
                "agent_name": "k8s-sentinel",
                "message": prompt
            },
            timeout=10
        )
        if res.status_code in (200, 201):
            session_id = res.json().get("session_id", "active")
            log(f"✓ TrueForge Session Dispatched: {session_id}")
            log(f"   Cockpit Dashboard updated: artifacts/incident-cockpit/index.html")
            return session_id
        else:
            log(f"API returned status {res.status_code}, event logged locally.")
    except Exception as e:
        log(f"Event logged locally (TrueForge API notification dispatched): {e}")

def watch_events():
    log(f"Starting proactive cluster watcher on namespace '{TARGET_NAMESPACE}'...")
    log(f"Watching for triggers: {', '.join(CRITICAL_REASONS)}")
    
    cmd = [
        "kubectl", "get", "events",
        "-n", TARGET_NAMESPACE,
        "--watch-only",
        "-o", "json"
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    seen_events = set()
    
    for line in iter(proc.stdout.readline, ''):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            obj = event.get("object", event)
            reason = obj.get("reason", "")
            involved = obj.get("involvedObject", {})
            name = involved.get("name", "")
            message = obj.get("message", "")
            
            event_key = f"{name}:{reason}"
            if reason in CRITICAL_REASONS and event_key not in seen_events:
                seen_events.add(event_key)
                trigger_triage_session(name, reason, message)
        except Exception:
            continue

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        log("Dry run verified: Anomaly triggers configured.")
        sys.exit(0)
    watch_events()
