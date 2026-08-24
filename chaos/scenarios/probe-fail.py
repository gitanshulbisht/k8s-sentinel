#!/usr/bin/env python3
"""Chaos scenario: Liveness probe failure -> restart storm.

Repoints the liveness (and readiness) probe to a path that returns 404.
The app itself stays healthy — nginx keeps serving — but kubelet kills
and restarts every container every ~15s. Classic "app fine, config lies"
failure that punishes agents that only read pod logs.

Diagnosis class the agent must reach: PROBE_ENDPOINT_FAILURE
Key evidence: restarts climbing while logs stay clean; probe config in
the live deployment spec points at /healthz-deprecated; GET on that path
returns 404.

Revert: kubectl apply -f infra/demo-app/base.yaml
"""
import json
import subprocess
import sys

NAMESPACE = "demo"
DEPLOYMENT = "payments-api"


def kubectl(*args):
    cmd = ["kubectl", "-n", NAMESPACE] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {' '.join(cmd)}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "api",
                            "livenessProbe": {
                                "httpGet": {"path": "/healthz-deprecated", "port": "http"},
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5,
                                "failureThreshold": 3,
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/healthz-deprecated", "port": "http"},
                                "initialDelaySeconds": 3,
                                "periodSeconds": 5,
                            },
                        }
                    ]
                }
            }
        }
    }
    kubectl(
        "patch", "deployment", DEPLOYMENT,
        "--type", "strategic", "-p", json.dumps(patch),
    )
    print("[CHAOS] Probes repointed to /healthz-deprecated (returns 404).")
    print("[CHAOS] Expected: restart storm (~1 kill per 15s per replica), clean app logs.")
    print("[CHAOS] Revert: kubectl apply -f infra/demo-app/base.yaml")


if __name__ == "__main__":
    main()
