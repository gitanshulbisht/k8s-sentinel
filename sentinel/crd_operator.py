#!/usr/bin/env python3
"""
K8s Sentinel — Native Kubernetes CRD Operator & Controller
Manages `IncidentRemediation` custom resources (sentinel.sre.io/v1alpha1),
allowing operators to inspect and approve remediations natively via kubectl.
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime, timezone

CRD_GROUP = "sentinel.sre.io"
CRD_VERSION = "v1alpha1"
CRD_KIND = "IncidentRemediation"
CRD_PLURAL = "incidentremediations"

def run_cmd(cmd, check=True):
    return subprocess.run(cmd, shell=True, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def publish_incident_cr(incident_id, workload, root_cause_class, smoking_gun, patch_cmd, severity="SEV-2", mttr="6.14s", namespace="demo"):
    cr_name = incident_id.lower().replace("_", "-")
    
    cr_manifest = {
        "apiVersion": f"{CRD_GROUP}/{CRD_VERSION}",
        "kind": CRD_KIND,
        "metadata": {
            "name": cr_name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/managed-by": "k8s-sentinel",
                "sentinel.sre.io/workload": workload.replace("/", "-")
            }
        },
        "spec": {
            "incidentId": incident_id,
            "severity": severity,
            "targetWorkload": workload,
            "rootCauseClass": root_cause_class,
            "smokingGun": smoking_gun,
            "proposedPatch": patch_cmd,
            "approvalStatus": "PendingApproval",
            "mttrSeconds": mttr
        }
    }

    manifest_json = json.dumps(cr_manifest)
    p = subprocess.Popen(["kubectl", "apply", "-f", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate(input=manifest_json)
    
    if p.returncode == 0:
        print(f"\033[1;32m✓ Published Kubernetes Custom Resource:\033[0m {CRD_KIND}/{cr_name} in namespace '{namespace}'")
        # Update initial status
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        status_patch = json.dumps({"status": {"phase": "Triaged", "observedGeneration": 1}})
        run_cmd(f"kubectl -n {namespace} patch {CRD_PLURAL} {cr_name} --subresource=status --type merge -p '{status_patch}'", check=False)
        return cr_name
    else:
        print(f"\033[1;31m✕ Failed to publish CR:\033[0m {err}")
        return None

def list_incidents(namespace="demo"):
    print(f"\n\033[1;36m==>\033[0m Querying Native Kubernetes CRD: \033[1mIncidentRemediation\033[0m (`kubectl get incidents -n {namespace}`)\n")
    res = run_cmd(f"kubectl -n {namespace} get incidents -o wide", check=False)
    if res.returncode == 0 and res.stdout.strip():
        print(res.stdout)
    else:
        print(f"No incident custom resources currently active in namespace '{namespace}'.")

def reconcile_incidents(namespace="demo"):
    """
    Controller loop: watches for `approvalStatus == Approved` and applies remediation.
    """
    res = run_cmd(f"kubectl -n {namespace} get {CRD_PLURAL} -o json", check=False)
    if res.returncode != 0 or not res.stdout.strip():
        return

    data = json.loads(res.stdout)
    items = data.get("items", [])

    for item in items:
        name = item["metadata"]["name"]
        spec = item.get("spec", {})
        status = item.get("status", {})
        
        approval = spec.get("approvalStatus")
        phase = status.get("phase", "Detected")

        if approval == "Approved" and phase != "Remediated":
            print(f"\n\033[1;32m[CRD-CONTROLLER]\033[0m Reconciling Approved Incident: \033[1m{name}\033[0m")
            print(f"  • Workload: {spec.get('targetWorkload')}")
            print(f"  • Patch:    {spec.get('proposedPatch')}")

            # Execute patch
            patch_cmd = spec.get("proposedPatch")
            if patch_cmd:
                print("  • Executing patch command on cluster...")
                run_cmd(patch_cmd, check=False)

            # Trigger rollout restart
            workload = spec.get("targetWorkload", "deploy/payments-api")
            run_cmd(f"kubectl -n {namespace} rollout restart {workload}", check=False)

            # Update status
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            patch_body = json.dumps({
                "spec": {"approvalStatus": "Applied"},
                "status": {"phase": "Remediated", "remediatedAt": now_str}
            })
            run_cmd(f"kubectl -n {namespace} patch {CRD_PLURAL} {name} --subresource=status --type merge -p '{json.dumps({'status': {'phase': 'Remediated', 'remediatedAt': now_str}})}'", check=False)
            run_cmd(f"kubectl -n {namespace} patch {CRD_PLURAL} {name} --type merge -p '{json.dumps({'spec': {'approvalStatus': 'Applied'}})}'", check=False)

            print(f"  \033[1;32m✓ Incident Reconciled & Remediated:\033[0m Phase set to \033[1mRemediated\033[0m\n")

def approve_incident_via_cr(cr_name, namespace="demo"):
    print(f"\033[1;34m==>\033[0m Approving incident CR \033[1m{cr_name}\033[0m via Kubernetes API...")
    patch_body = json.dumps({"spec": {"approvalStatus": "Approved"}})
    res = run_cmd(f"kubectl -n {namespace} patch {CRD_PLURAL} {cr_name} --type merge -p '{patch_body}'")
    if res.returncode == 0:
        print(f"  \033[1;32m✓ CR Patched to Approved:\033[0m Reconciling controller...")
        reconcile_incidents(namespace)
    else:
        print(f"  \033[1;31m✕ Failed to patch CR:\033[0m {res.stderr}")

def seed_sample_cr():
    publish_incident_cr(
        incident_id="INC-20260827-CRASHLOOP-DEMO",
        workload="deployment/payments-api",
        root_cause_class="CONFIG_INVALID",
        smoking_gun='nginx: [emerg] unknown directive "this_directive_does_not_exist" in /etc/nginx/conf.d/default.conf:3',
        patch_cmd='kubectl patch configmap nginx-healthz -n demo --type merge -p \'{"data":{"default.conf":"server { listen 80; location = /healthz { return 200 \\"ok\\\\n\\"; } }"}}\'',
        severity="SEV-2",
        mttr="6.14s",
        namespace="demo"
    )

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "list":
        list_incidents()
    elif sys.argv[1] == "seed":
        seed_sample_cr()
        list_incidents()
    elif sys.argv[1] == "approve":
        cr_name = sys.argv[2] if len(sys.argv) > 2 else "inc-20260827-crashloop-demo"
        approve_incident_via_cr(cr_name)
    elif sys.argv[1] == "reconcile":
        reconcile_incidents()
    else:
        print("Usage: python3 sentinel/crd_operator.py [list|seed|approve <name>|reconcile]")

if __name__ == "__main__":
    main()
