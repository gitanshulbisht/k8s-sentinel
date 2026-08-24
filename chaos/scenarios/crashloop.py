#!/usr/bin/env python3
"""Chaos scenario: CrashLoopBackOff via corrupted nginx configuration.

Injects an invalid directive into the nginx-healthz ConfigMap. Every replica
fails nginx startup (exit 1) and enters CrashLoopBackOff within ~1 minute.

Diagnosis class the agent should reach: NGINX_CONFIG_INVALID
Key evidence: pod logs contain "nginx: [emerg] unknown directive";
events show BackOff loop; previous-container logs hold the smoking gun.

Revert: kubectl apply -f infra/demo-app/base.yaml
"""
import subprocess
import sys

NAMESPACE = "demo"
CONFIGMAP = "nginx-healthz"

BAD_CONF = """server {
  listen 80;
  this_directive_does_not_exist 42;
  location = /healthz {
    access_log off;
    return 200 "ok\\n";
  }
}
"""


def kubectl(*args, input_text=None):
    cmd = ["kubectl", "-n", NAMESPACE] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, input=input_text)
    if result.returncode != 0:
        print(f"[ERROR] {' '.join(cmd)}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    patch = {"data": {"default.conf": BAD_CONF}}
    import json

    kubectl(
        "patch", "configmap", CONFIGMAP,
        "--type", "merge", "-p", json.dumps(patch),
    )
    # Bounce pods so they pick up the corrupted config immediately.
    kubectl("rollout", "restart", "deployment/payments-api")
    print("[CHAOS] Corrupted nginx config in ConfigMap %s and restarted pods." % CONFIGMAP)
    print("[CHAOS] Expected within ~60s: all replicas in CrashLoopBackOff.")
    print("[CHAOS] Smoking gun: 'nginx: [emerg] unknown directive' in pod logs (--previous).")
    print("[CHAOS] Revert: kubectl apply -f infra/demo-app/base.yaml")


if __name__ == "__main__":
    main()
