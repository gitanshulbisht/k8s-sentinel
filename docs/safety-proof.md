# Safety Proof — Recorded Evidence

Layer-1 verification results (toolchain-level, agent-independent).
Recorded: 2026-08-24, cluster `sentinel-demo`, kubernetes-mcp-server v0.0.66.

## Check 1 — No destructive tools exposed to the agent

`tests/test_safety.sh` performs a full MCP handshake against the live server
and inspects `tools/list`:

```
==> Check 1: MCP tool surface contains no destructive verbs
  PASS no delete/apply/patch/scale/rollout/create/replace tools exposed
  PASS pods_run present (needed for in-pod endpoint tests)

==> Check 2: cluster state immutable across a full chaos cycle
  PASS state identical before vs after scenario+revert

SAFETY CHECKS: 0 failure(s)
```

Mechanism: the MCP server runs with `--disable-destructive`, which removes
every tool annotated `destructiveHint=true` at the protocol layer — the agent
structurally cannot reach mutation through its tool surface, independent of
prompt-level behavior.

Tool inventory observed (16 tools, all read/diagnostic or sandboxed-exec):
configuration_contexts_list, configuration_view, events_list, namespaces_list,
nodes_log, nodes_stats_summary, nodes_top, pods_get, pods_list,
pods_list_in_namespace, pods_log, pods_run, pods_top, projects_list,
resources_get, resources_list.

## Check 2 — Functional state immutability across a chaos cycle

Snapshot = deployment container spec (image/resources/probes/volumes),
spec.replicas, configmap payloads, readyReplicas. Taken before a full
crashloop injection → revert cycle and compared after recovery: identical.

Note on methodology: the first version of this check diffed full YAML and
false-failed on benign rollout bookkeeping (`observedGeneration`,
condition `lastUpdateTime`). Fixed by comparing functional state only.
See JOURNEY.md Entry 3.2.

## Layer 2 (pending) — Agent-level approval gate

Once the saved K8s Sentinel agent has a model provider configured, this file
will also record: for each scenario, a "fix it" request produces proposed_fix
JSON with all-mutating commands flagged, zero cluster changes pre-approval
(state diff empty), and successful gated remediation after manual approval.
