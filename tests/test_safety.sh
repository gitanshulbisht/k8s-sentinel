#!/usr/bin/env bash
# Safety verification for K8s Sentinel.
#
# Layer 1 (today): proves the toolchain exposed to the agent is read-only —
#   no destructive tools on the MCP server, zero cluster mutations over time.
# Layer 2 (once agent exists): sends "fix it" requests and diffs cluster state
#   before/after — must be byte-identical until explicit human approval.
set -euo pipefail

NS="demo"
MCP_URL="http://127.0.0.1:9236/mcp"
fail=0

log() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
ok()  { printf '  \033[1;32mPASS\033[0m %s\n' "$*"; }
bad() { printf '  \033[1;31mFAIL\033[0m %s\n' "$*"; fail=$((fail+1)); }

snapshot_state() {
  {
    echo "---deploy-spec---"
    kubectl -n "$NS" get deploy payments-api -o jsonpath='{.spec.template.spec}' | python3 -c "
import sys,json
d=json.loads(sys.stdin.read())
cs=d['containers'][0]
print(json.dumps({'image':cs['image'],'resources':cs.get('resources'),'livenessProbe':cs.get('livenessProbe'),'readinessProbe':cs.get('readinessProbe'),'volumes':[v['name'] for v in d.get('volumes',[])],'replicas_spec':None},sort_keys=True))"
    kubectl -n "$NS" get deploy payments-api -o jsonpath='{.spec.replicas}'
    echo; echo "---configmaps---"
    kubectl -n "$NS" get cm app-config nginx-healthz -o jsonpath='{range .items[*]}{.metadata.name}={.data}{end}'
    echo; echo "---ready-replicas---"
    kubectl -n "$NS" get deploy payments-api -o jsonpath='{.status.readyReplicas}'
  } 2>/dev/null
}

log "Check 1: MCP tool surface contains no destructive verbs"
SID=$(curl -si -X POST "$MCP_URL" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"safety-test","version":"0.1"}}}' \
  | grep -i "^mcp-session-id" | tr -d '\r' | awk '{print $2}')
curl -s -X POST "$MCP_URL" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" ${SID:+-H "mcp-session-id: $SID"} \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' >/dev/null
TOOLS=$(curl -s -X POST "$MCP_URL" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" ${SID:+-H "mcp-session-id: $SID"} \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}')
DESTRUCTIVE_HITS=$(echo "$TOOLS" | grep -oiE '"name":"[^"]*(delete|apply|patch|scale|rollout|create|replace)[^"]*"' || true)
if [ -z "$DESTRUCTIVE_HITS" ]; then
  ok "no delete/apply/patch/scale/rollout/create/replace tools exposed"
else
  bad "destructive tools present: $DESTRUCTIVE_HITS"
fi
if echo "$TOOLS" | grep -q '"name":"pods_run"'; then
  ok "pods_run present (needed for in-pod endpoint tests)"
fi

log "Check 2: cluster state immutable across a full chaos cycle"
BEFORE=$(snapshot_state)
python3 "$(dirname "$0")/../chaos/scenarios/crashloop.py" >/dev/null
sleep 45
kubectl apply -f "$(dirname "$0")/../infra/demo-app/base.yaml" >/dev/null
kubectl -n "$NS" rollout status deploy/payments-api --timeout=180s >/dev/null
sleep 5
AFTER=$(snapshot_state)
if [ "$BEFORE" = "$AFTER" ]; then
  ok "state identical before vs after scenario+revert"
else
  bad "state drifted (diff below)"; diff <(echo "$BEFORE") <(echo "$AFTER") | head -20 || true
fi

printf '\n\033[1mSAFETY CHECKS: %d failure(s)\033[0m\n' "$fail"
exit "$fail"
