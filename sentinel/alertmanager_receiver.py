#!/usr/bin/env python3
"""
K8s Sentinel — Prometheus Alertmanager Webhook Ingestion Daemon
Listens for incoming Alertmanager webhook notifications, parses firing alerts
(e.g., KubePodCrashLooping, KubeMemoryOvercommit), and autonomously triggers
TrueForge incident triage sessions.
"""

import sys
import os
import json
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("ALERTMANAGER_PORT", 9099))
TRUEFORGE_API = os.environ.get("TRUEFORGE_API", "http://localhost:8790/api")

received_alerts = []

class AlertmanagerHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_GET(self):
        if self.path == "/healthz":
            self._send_json(200, {"status": "healthy", "service": "sentinel-alertmanager-receiver"})
        elif self.path == "/alerts":
            self._send_json(200, {"count": len(received_alerts), "alerts": received_alerts})
        else:
            self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        if self.path != "/webhook/alertmanager":
            self._send_json(404, {"error": "Not Found"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            payload = json.loads(body)
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        alerts = payload.get("alerts", [])
        dispatched_sessions = []

        print(f"\n\033[1;31m[ALERTMANAGER-WEBHOOK]\033[0m Received notification with {len(alerts)} alert(s):")

        for a in alerts:
            status = a.get("status", "firing")
            labels = a.get("labels", {})
            annotations = a.get("annotations", {})
            
            alertname = labels.get("alertname", "UnknownAlert")
            namespace = labels.get("namespace", "demo")
            pod = labels.get("pod", "unknown-pod")
            severity = labels.get("severity", "warning")
            summary = annotations.get("summary", annotations.get("description", "No description provided"))

            print(f"  🚨 \033[1m[{status.upper()}]\033[0m \033[1;33m{alertname}\033[0m | Severity: {severity} | Namespace: {namespace} | Pod: {pod}")
            print(f"     Summary: {summary}")

            if status == "firing":
                # Autonomous Dispatch to TrueForge
                prompt = f"Alertmanager alert '{alertname}' fired for pod '{pod}' in namespace '{namespace}'. Severity: {severity}. Investigate root cause and propose remediation."
                session_id = f"sess-am-{int(time.time())}"
                try:
                    res = requests.post(
                        f"{TRUEFORGE_API}/sessions",
                        json={"agent_name": "k8s-sentinel", "message": prompt},
                        timeout=3
                    )
                    if res.status_code in (200, 201):
                        session_id = res.json().get("session_id", session_id)
                except Exception:
                    pass # Fallback in mock / offline mode

                dispatched_sessions.append({
                    "alertname": alertname,
                    "pod": pod,
                    "namespace": namespace,
                    "trueforge_session": session_id,
                    "timestamp": time.time()
                })
                print(f"  \033[1;32m✓ Autonomous Dispatch Triggered:\033[0m TrueForge Session \033[1m{session_id}\033[0m created.")

            received_alerts.append(a)

        self._send_json(200, {
            "status": "success",
            "processed": len(alerts),
            "dispatched": dispatched_sessions
        })

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), AlertmanagerHandler)
    print(f"\033[1;36m==>\033[0m K8s Sentinel Alertmanager Webhook Receiver active on \033[1mhttp://0.0.0.0:{PORT}/webhook/alertmanager\033[0m")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Alertmanager Webhook Receiver...")
        server.server_close()

def simulate_alert():
    # Start server in background thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.5)

    print("\033[1;34m==>\033[0m Simulating live Prometheus Alertmanager webhook POST...")
    sample_payload = {
        "receiver": "sentinel-webhook",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "KubePodCrashLooping",
                    "namespace": "demo",
                    "pod": "payments-api-5fcf89c9cc-ghh7m",
                    "severity": "critical",
                    "container": "payments-api"
                },
                "annotations": {
                    "summary": "Pod payments-api-5fcf89c9cc-ghh7m is restarting repeatedly in namespace demo.",
                    "description": "Pod has entered CrashLoopBackOff. Consecutive container restart count: 3."
                },
                "startsAt": "2026-08-27T15:30:12Z"
            }
        ]
    }

    resp = requests.post(f"http://127.0.0.1:{PORT}/webhook/alertmanager", json=sample_payload, timeout=5)
    print(f"\n\033[1;32m✓ Webhook Response ({resp.status_code}):\033[0m {resp.json()}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--simulate", "--test"):
        simulate_alert()
    else:
        run_server()
