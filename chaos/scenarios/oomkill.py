#!/usr/bin/env python3
"""Chaos scenario: OOMKill loop via undersized memory limit.

Shrinks the container memory limit far below nginx's runtime footprint.
The kernel OOM-kills each container shortly after start -> repeated
OOMKilled statuses with rising restart counters.

Diagnosis class the agent should reach: RESOURCE_LIMIT_MISMATCH
Key evidence: pod status lastState.terminated.reason == OOMKilled,
exit code 137, restart rate climbing in metrics.

Revert: kubectl apply -f infra/demo-app/base.yaml
"""
import json
import subprocess
import sys

NAMESPACE = "demo"
DEPLOYMENT = "payments-api"
# nginx:alpine idles around 6-10 MiB; 4 Mi guarantees OOM across arch variance.
TINY_LIMIT_MI = 4


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
                            "resources": {
                                "requests": {"cpu": "50m", "memory": f"{TINY_LIMIT_MI}Mi"},
                                "limits": {"cpu": "250m", "memory": f"{TINY_LIMIT_MI}Mi"},
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
    print(f"[CHAOS] Memory limit dropped to {TINY_LIMIT_MI}Mi on {DEPLOYMENT}.")
    print("[CHAOS] Expected within ~30s: OOMKilled loop (exit 137), restarts climbing.")
    print("[CHAOS] Revert: kubectl apply -f infra/demo-app/base.yaml")


if __name__ == "__main__":
    main()
