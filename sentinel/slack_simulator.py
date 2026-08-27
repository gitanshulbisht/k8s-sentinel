#!/usr/bin/env python3
"""
K8s Sentinel — Slack Block-Kit Incident & Approval Card Simulator
Generates Slack Block-Kit JSON payloads and terminal previews
for SRE incident war rooms with interactive approval action buttons.
"""

import sys
import json
import os

def generate_slack_block_kit(incident_id="INC-20260827-CRASHLOOP-DEMO"):
    payload = {
        "text": f"🚨 [SEV-2 ALERT] Incident Detected: {incident_id}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 K8s Sentinel — Autonomous Incident Triage Alert",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident_id}`"},
                    {"type": "mrkdwn", "text": "*Severity:*\n`SEV-2 (High)`"},
                    {"type": "mrkdwn", "text": "*Service:*\n`payments-api (Namespace: demo)`"},
                    {"type": "mrkdwn", "text": "*Autonomous MTTR:*\n`6.14 seconds`"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Root Cause Isolated (Confidence: 96%):*\nConfigMap `nginx-healthz` contained unrecognized directive `this_directive_does_not_exist 42;` at `/etc/nginx/conf.d/default.conf:3`, preventing container startup."
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Proposed Surgical Remediation (`mutating: true`):*\n```kubectl patch configmap nginx-healthz -n demo --type merge -p '{\"data\":{\"default.conf\":\"server { listen 80; location = /healthz { return 200 \\\"ok\\\\n\\\"; } }\"}}'\nkubectl rollout restart deployment/payments-api -n demo```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🛡️ *Human Approval Gate:* Execution is paused. Cluster state drift = `0 Bytes`."
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✓ Approve & Apply Patch", "emoji": True},
                        "style": "primary",
                        "value": "approve_remediation",
                        "action_id": "btn_approve"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✕ Reject", "emoji": True},
                        "style": "danger",
                        "value": "reject_remediation",
                        "action_id": "btn_reject"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 Open Incident Cockpit", "emoji": True},
                        "url": "http://localhost:8790",
                        "action_id": "btn_cockpit"
                    }
                ]
            }
        ]
    }
    return payload

def print_terminal_slack_card(payload):
    print("\n\033[1;35m" + "━"*75 + "\033[0m")
    print("\033[1;37m💬 SLACK WAR ROOM INCIDENT CARD SIMULATOR (#incident-payments-sev2)\033[0m")
    print("\033[1;35m" + "━"*75 + "\033[0m")
    print(" 🚨 \033[1;31mK8s Sentinel — Autonomous Incident Triage Alert\033[0m")
    print(" ─────────────────────────────────────────────────────────────────────────")
    print("  \033[1mIncident ID:\033[0m  INC-20260827-CRASHLOOP-DEMO    | \033[1mSeverity:\033[0m   SEV-2 (High)")
    print("  \033[1mService:\033[0m      payments-api (namespace: demo) | \033[1mMTTR:\033[0m       6.14 seconds")
    print(" ─────────────────────────────────────────────────────────────────────────")
    print("  \033[1mRoot Cause Isolated (Confidence: 96.0%):\033[0m")
    print("  ConfigMap 'nginx-healthz' contained unrecognized directive")
    print("  \033[1;33mthis_directive_does_not_exist 42;\033[0m at /etc/nginx/conf.d/default.conf:3")
    print(" ─────────────────────────────────────────────────────────────────────────")
    print("  \033[1mProposed Remediation:\033[0m")
    print("  \033[2mkubectl patch configmap nginx-healthz -n demo ...\033[0m")
    print("  \033[2mkubectl rollout restart deployment/payments-api -n demo\033[0m")
    print(" ─────────────────────────────────────────────────────────────────────────")
    print("  \033[1;33m🛡️ Human Approval Gate Engaged: Pre-approval drift = 0 Bytes\033[0m")
    print("\n  [ \033[1;32m✓ Approve & Apply Patch\033[0m ]   [ \033[1;31m✕ Reject\033[0m ]   [ \033[1;34m📊 Open Cockpit\033[0m ]")
    print("\033[1;35m" + "━"*75 + "\033[0m\n")

def main():
    payload = generate_slack_block_kit()
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(payload, indent=2))
    else:
        print_terminal_slack_card(payload)
        out_file = os.path.join(os.path.dirname(__file__), "../artifacts/slack_incident_card.json")
        with open(out_file, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"✓ Saved Slack Block-Kit JSON: artifacts/slack_incident_card.json")

if __name__ == "__main__":
    main()
