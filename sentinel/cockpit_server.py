#!/usr/bin/env python3
"""
K8s Sentinel — Live Interactive Cockpit Server
A dual-mode HTTP backend that serves the Generative UI Web Cockpit and provides
real-time bidirectional bridge to the live Kubernetes cluster via kubectl.
"""

import os
import sys
import json
import subprocess
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATIC_DIR = os.path.join(REPO_ROOT, "artifacts/incident-cockpit")
DEFAULT_PORT = 8085
NAMESPACE = "demo"
DEPLOYMENT = "payments-api"

class CockpitHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/cluster-status":
            self.handle_cluster_status()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/remediate":
            self.handle_remediate()
        elif parsed.path == "/api/chaos":
            self.handle_chaos()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_cluster_status(self):
        try:
            # Query live Kubernetes cluster
            cmd = f"kubectl -n {NAMESPACE} get pods -o json"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if res.returncode != 0:
                self.send_json(200, {
                    "live": False,
                    "error": res.stderr.strip() or "Cluster unreachable",
                    "namespace": NAMESPACE
                })
                return

            data = json.loads(res.stdout)
            items = data.get("items", [])

            # Check ConfigMap status
            cm_cmd = f"kubectl -n {NAMESPACE} get cm nginx-healthz -o json"
            cm_res = subprocess.run(cm_cmd, shell=True, capture_output=True, text=True)
            is_corrupted = False
            if cm_res.returncode == 0:
                cm_data = json.loads(cm_res.stdout)
                conf = cm_data.get("data", {}).get("default.conf", "")
                if "this_directive_does_not_exist" in conf:
                    is_corrupted = True

            pod_list = []
            ready_count = 0
            has_crash = False

            for p in items:
                name = p.get("metadata", {}).get("name", "unknown")
                cs_list = p.get("status", {}).get("containerStatuses") or []
                cs = cs_list[0] if cs_list else {}
                is_ready = bool(cs.get("ready"))
                if is_ready:
                    ready_count += 1
                
                phase = p.get("status", {}).get("phase", "Unknown")
                waiting = cs.get("state", {}).get("waiting", {})
                reason = waiting.get("reason", phase)
                restarts = cs.get("restartCount", 0)

                if reason in ("CrashLoopBackOff", "Error", "ErrImagePull", "ImagePullBackOff"):
                    has_crash = True

                pod_list.append({
                    "name": name,
                    "ready": "1/1" if is_ready else "0/1",
                    "status": reason,
                    "restarts": restarts,
                    "is_ready": is_ready
                })

            self.send_json(200, {
                "live": True,
                "namespace": NAMESPACE,
                "deployment": DEPLOYMENT,
                "replicas_ready": ready_count,
                "replicas_total": len(items),
                "has_crash": has_crash or is_corrupted,
                "config_corrupted": is_corrupted,
                "pods": pod_list
            })
        except Exception as e:
            self.send_json(500, {"live": False, "error": str(e)})

    def handle_remediate(self):
        try:
            # Apply real Kubernetes patch
            patch_cmd = 'kubectl patch configmap nginx-healthz -n demo --type merge -p \'{"data":{"default.conf":"server {\\n    listen 80;\\n\\n    location = /healthz {\\n        return 200 \\"ok\\\\n\\";\\n    }\\n}\\n"}}\''
            subprocess.run(patch_cmd, shell=True, check=True, capture_output=True)
            
            # Restart deployment to roll out clean config
            restart_cmd = f"kubectl rollout restart deploy/{DEPLOYMENT} -n {NAMESPACE}"
            subprocess.run(restart_cmd, shell=True, check=True, capture_output=True)

            self.send_json(200, {
                "success": True,
                "message": "Live Kubernetes remediation applied and deployment restarted!"
            })
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def handle_chaos(self):
        try:
            # Inject chaos scenario on real cluster
            script = os.path.join(REPO_ROOT, "chaos/scenarios/crashloop.py")
            subprocess.run([sys.executable, script], check=True, capture_output=True)
            self.send_json(200, {
                "success": True,
                "message": "CrashLoopBackOff chaos injected into live cluster!"
            })
        except Exception as e:
            self.send_json(500, {"success": False, "error": str(e)})

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

def run(port=DEFAULT_PORT):
    server = HTTPServer(("0.0.0.0", port), CockpitHandler)
    print(f"🚀 K8s Sentinel Live Cockpit Server listening on http://0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Cockpit Server...")
        server.server_close()

if __name__ == "__main__":
    port = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--port" else DEFAULT_PORT
    run(port)
