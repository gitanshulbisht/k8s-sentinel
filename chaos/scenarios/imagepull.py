#!/usr/bin/env python3
"""Chaos scenario: ImagePullBackOff via nonexistent image tag.

Swaps the deployment image to a tag that does not exist in the registry.
Every pod sticks in ImagePullBackOff; no container ever starts.

Deliberately the *shallowest* scenario: the agent must resist over-
investigating. The answer sits in describe output; good triage reports it
in one step instead of spawning parallel dives.

Diagnosis class the agent should reach: IMAGE_TAG_INVALID
Key evidence: events "Failed to pull image ... not found"; pod status
waiting.reason == ImagePullBackOff.

Revert: kubectl apply -f infra/demo-app/base.yaml
"""
import json
import subprocess
import sys

NAMESPACE = "demo"
DEPLOYMENT = "payments-api"
BAD_IMAGE = "nginx:1.27-tagdoesnotexist"


def kubectl(*args):
    cmd = ["kubectl", "-n", NAMESPACE] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {' '.join(cmd)}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    patch = {"spec": {"template": {"spec": {"containers": [
        {"name": "api", "image": BAD_IMAGE}
    ]}}}}
    kubectl(
        "patch", "deployment", DEPLOYMENT,
        "--type", "strategic", "-p", json.dumps(patch),
    )
    print(f"[CHAOS] Image set to {BAD_IMAGE}.")
    print("[CHAOS] Expected within ~20s: ImagePullBackOff on all replicas.")
    print("[CHAOS] Revert: kubectl apply -f infra/demo-app/base.yaml")


if __name__ == "__main__":
    main()
