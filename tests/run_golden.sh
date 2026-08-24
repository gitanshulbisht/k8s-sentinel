#!/usr/bin/env bash
# Golden-case validation suite for K8s Sentinel.
#
# Layer 1 (this script, runnable today): proves each chaos scenario produces
#   exactly the failure signature its golden fixture documents, using the same
#   evidence classes the agent must cite (pod status, events, logs, spec).
# Layer 2 (once the saved agent + model key exist): invokes K8s Sentinel per
#   scenario and diffs its findings JSON against these fixtures.
set -euo pipefail

NS="demo"
DEPLOY="payments-api"
BASE_YAML="$(dirname "$0")/../infra/demo-app/base.yaml"
GOLDEN_DIR="$(dirname "$0")/golden"
TIMEOUT=120

pass=0; fail=0; failed_scenarios=()

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '  \033[1;32mPASS\033[0m %s\n' "$*"; }
bad()  { printf '  \033[1;31mFAIL\033[0m %s\n' "$*"; }

preflight() {
  kubectl -n "$NS" get deploy "$DEPLOY" >/dev/null 2>&1 || {
    echo "Demo app missing. Run: kubectl apply -f infra/demo-app/base.yaml"; exit 1; }
  log "Reverting to clean baseline before suite"
  kubectl apply -f "$BASE_YAML" >/dev/null
  kubectl -n "$NS" rollout status "deploy/$DEPLOY" --timeout=180s >/dev/null
}

wait_for_new_pod_signature() { # $1 = jsonpath condition function name
  local deadline=$((SECONDS + TIMEOUT))
  while (( SECONDS < deadline )); do
    if "$1"; then return 0; fi
    sleep 5
  done
  return 1
}

sig_imagepull() {
  # Match BOTH phases: pods flip ErrImagePull -> ImagePullBackOff rapidly,
  # so polling only for ErrImagePull races the transition.
  kubectl -n "$NS" get pods -o json | grep -qE '"reason": *"(ErrImagePull|ImagePullBackOff)"'
}
sig_oomkill() {
  kubectl -n "$NS" get pods -o json | grep -q '"reason": *"OOMKilled"\|"reason":"OOMKilled"'
}
sig_crashloop() {
  kubectl -n "$NS" get pods -o json | grep -q '"reason": *"CrashLoopBackOff"'
}
sig_probefail() {
  # restart storm on newest pods while probe path is the broken one
  local path restarts
  path=$(kubectl -n "$NS" get deploy "$DEPLOY" -o jsonpath='{.spec.template.spec.containers[0].livenessProbe.httpGet.path}')
  [ "$path" = "/healthz-deprecated" ] || return 1
  restarts=$(kubectl -n "$NS" get pods -l app="$DEPLOY" -o jsonpath='{range .items[*]}{.status.containerStatuses[0].restartCount}{"\n"}{end}' | sort -rn | head -1)
  [ "${restarts:-0}" -ge 2 ]
}

check_fixture_patterns() { # $1=scenario  $2=json-with-required_evidence_patterns
  local scenario="$1" json="$2"
  local pattern probe
  local attempts=0 max_attempts=7   # kubelet emits events async AFTER pod status flips
  local -a missing
  while (( attempts < max_attempts )); do
    missing=()
    while IFS= read -r pattern; do
      probe=""
      case "$scenario" in
        crashloop)  probe=$(kubectl -n "$NS" logs "$(newest_pod)" --previous 2>/dev/null | grep -iE "$pattern" | head -1) ;;
        oomkill)    probe=$(kubectl -n "$NS" get pods -o json | grep -iE "$pattern" | head -1) ;;
        imagepull)  probe=$(kubectl -n "$NS" get events -o json 2>/dev/null | grep -iE "$pattern" | head -1) ;;
        probe-fail) probe=$(kubectl -n "$NS" get deploy "$DEPLOY" -o json | grep -iE "$pattern" | head -1) ;;
      esac
      [ -z "$probe" ] && missing+=("$pattern")
    done < <(echo "$json" | jq -r '.expected.required_evidence_patterns[]')
    [ "${#missing[@]}" -eq 0 ] && return 0
    attempts=$((attempts+1))
    sleep 5
  done
  printf '      unresolved patterns after %ds: %s\n' $((max_attempts*5)) "${missing[*]}"
  return 1
}

newest_pod() {
  kubectl -n "$NS" get pods -l app="$DEPLOY" --sort-by=.status.startTime \
    -o jsonpath='{.items[-1].metadata.name}'
}

run_scenario() { # $1=name $2=script $3=sig_fn
  local name="$1"
  local script="$2"
  local sig="$3"
  local fixture="$GOLDEN_DIR/${name}_expected.json"
  log "Scenario: $name"
  python3 "$script" >/dev/null
  if wait_for_new_pod_signature "$sig"; then
    ok "signature appeared within ${TIMEOUT}s"
  else
    bad "signature NOT observed within ${TIMEOUT}s — live state:"
    kubectl -n "$NS" get pods | sed 's/^/      /' || true
    kubectl -n "$NS" get events --sort-by=.lastTimestamp 2>/dev/null | tail -5 | sed 's/^/      /' || true
    fail=$((fail+1)); failed_scenarios+=("$name"); revert; return
  fi
  if check_fixture_patterns "$name" "$(cat "$fixture")"; then
    ok "all fixture evidence patterns resolvable in live cluster"; pass=$((pass+1))
  else
    bad "fixture evidence patterns not fully resolvable"; fail=$((fail+1)); failed_scenarios+=("$name")
  fi
  revert
}

revert() {
  kubectl apply -f "$BASE_YAML" >/dev/null
  kubectl -n "$NS" rollout status "deploy/$DEPLOY" --timeout=180s >/dev/null
  sleep 3
}

preflight
run_scenario imagepull  "$(dirname "$0")/../chaos/scenarios/imagepull.py" sig_imagepull
run_scenario oomkill    "$(dirname "$0")/../chaos/scenarios/oomkill.py"   sig_oomkill
run_scenario crashloop  "$(dirname "$0")/../chaos/scenarios/crashloop.py" sig_crashloop
run_scenario probe-fail "$(dirname "$0")/../chaos/scenarios/probe-fail.py" sig_probefail

printf '\n\033[1mRESULTS: %d passed, %d failed\033[0m\n' "$pass" "$fail"
if [ "${#failed_scenarios[@]}" -eq 0 ]; then
  printf '\033[1;32mALL GOLDEN SIGNATURES VERIFIED\033[0m\n'
else
  printf '\033[1;31mFAILED: %s\033[0m\n' "${failed_scenarios[*]}"
  exit 1
fi
