# Chaos Harness — Reproducible Failure Scenarios

One-command, idempotent failure injection against the `sentinel-demo` kind
cluster. Each script prints what it broke and how to revert.

All scenarios revert with the same canonical command:

```bash
kubectl apply -f infra/demo-app/base.yaml
```

## Prerequisites

- kind cluster `sentinel-demo` running (`kind create cluster --name sentinel-demo --config infra/kind-config.yaml`)
- Demo app healthy (`kubectl apply -f infra/demo-app/base.yaml`, pods 3/3 Running)

## Scenarios

### crashloop.py — CrashLoopBackOff

```bash
python3 chaos/scenarios/crashloop.py
watch kubectl -n demo get pods     # all replicas -> CrashLoopBackOff within ~60s
```

Mechanism: patches ConfigMap `nginx-healthz` with an invalid nginx directive
(`this_directive_does_not_exist`) and restarts the rollout. nginx exits 1 at
startup; kubelet backs off and retries.

Smoking gun for the agent: `nginx: [emerg] unknown directive` in **previous**
container logs; `BackOff` events.

| Field | Value |
|---|---|
| Diagnosis class | `NGINX_CONFIG_INVALID` |
| Difficulty | Medium — requires previous-container logs |

### oomkill.py — OOMKilled loop

```bash
python3 chaos/scenarios/oomkill.py
kubectl -n demo get pods -w       # RESTARTS climbing, STATUS flipping to OOMKilled
```

Mechanism: shrinks memory limit from 128Mi → 4Mi via strategic merge patch.
Kernel OOM-kills each container shortly after start (exit code 137).

| Field | Value |
|---|---|
| Diagnosis class | `RESOURCE_LIMIT_MISMATCH` |
| Difficulty | Easy-medium — visible in `describe pod` lastState |

### probe-fail.py — Liveness restart storm

```bash
python3 chaos/scenarios/probe-fail.py
kubectl -n demo get pods -w      # RESTARTS +1 every ~15s per replica, logs CLEAN
```

Mechanism: repoints liveness+readiness probes to `/healthz-deprecated`,
which returns 404. The app is actually healthy — the probe config is lying.
This is the trap scenario for log-only debugging.

| Field | Value |
|---|---|
| Diagnosis class | `PROBE_ENDPOINT_FAILURE` |
| Difficulty | Hard — logs are clean; agent must inspect probe spec + hit the endpoint |

### imagepull.py — ImagePullBackOff

```bash
python3 chaos/scenarios/imagepull.py
kubectl -n demo get pods          # ImagePullBackOff within ~20s
```

Mechanism: sets image to `nginx:1.27-tagdoesnotexist`. No container starts.
Deliberately shallow — tests whether the agent reports fast instead of
over-investigating.

| Field | Value |
|---|---|
| Diagnosis class | `IMAGE_TAG_INVALID` |
| Difficulty | Trivial — one describe away |

## Revert & Verify

```bash
kubectl apply -f infra/demo-app/base.yaml
kubectl -n demo rollout status deployment/payments-api   # "successfully rolled out"
kubectl -n demo get pods                                  # 3/3 Running, RESTARTS frozen
```

Note: restart counters do not reset on revert (they're pod-lifetime counters).
Fresh counters come from new pods after `rollout restart` if you need a clean slate.
