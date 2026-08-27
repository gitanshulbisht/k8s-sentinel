# JOURNEY.md — Building K8s Sentinel

> A living log of the Agent Harness Hackathon build: every real problem we hit,
> how we solved it, and how the project evolved because of it.
>
> Format per entry: **Date | Phase** → Problem → Solution → What changed in the project.
> Newest entries at the bottom.

---

## Day 0 — Aug 24, 2026 · Kickoff & Problem Selection

### Entry 0.1 — Picking a problem that forces the harness

**Problem:** The hackathon explicitly rejects "another chat interface around an LLM."
Most participants will wrap an LLM in a UI. How do we stand out on the
"Best Use of TrueForge" track?

**Solution:** Choose a problem where every TrueForge feature is *load-bearing*, not
decorative. Kubernetes incident triage does exactly that:

| TrueForge capability | Why triage genuinely needs it |
|---|---|
| MCP tools | Cluster state lives behind kubectl/Prometheus APIs, not in the model |
| Sandbox | Generated analysis scripts must run somewhere isolated |
| Approvals | Scaling/restarting workloads must never happen without a human |
| Subagents | 20 failing pods = 20 parallel investigations |
| Persistent sessions | Incidents span days; "what did we find yesterday?" must work |
| Skills | Triage playbook is reusable procedure, not one-off prompting |

**Evolution:** Scope locked to *triage* (diagnose + propose fix), not auto-remediate.
The approval gate is the demo centerpiece, not a limitation.

### Entry 0.2 — Docker daemon off by default

**Problem:** `docker info` failed — Docker Desktop wasn't running. (Deliberate:
this machine keeps dev services off unless needed.)

**Solution:** Started Docker Desktop manually (`open -a Docker`). Daemon ready
in ~20s. VM reports 4.8 GB allocatable — this constrains kind sizing later.

**Evolution:** Added infra sizing note: kind control-plane + Prometheus must fit
in ~4.8 GB Docker VM budget on an 8 GB Mac.

---

## Day 1 — Aug 24, 2026 · Foundation & Chaos Harness

### Entry 1.1 — Kubernetes rejected our OOM scenario (API validation as a bug catcher)

**Problem:** `oomkill.py` first attempt failed instantly:

```
The Deployment "payments-api" is invalid:
spec.template.spec.containers[0].resources.requests: Invalid value: "32Mi":
must be less than or equal to memory limit of 4Mi
```

We shrank the *limit* to 4Mi but left *requests* at 32Mi. Kubernetes enforces
`requests ≤ limits`, so the API server refused the patch outright — no incident
injected at all.

**Solution:** Set `requests.memory = limits.memory = 4Mi`. Re-ran: within 60s the
new pod showed `lastState.terminated.reason=OOMKilled, exitCode=137` and events
logged *"container init was OOM-killed (memory limit too low?)"* — exactly the
signature we want the agent to diagnose.

**Evolution:** Lesson recorded for the agent's skill later: when proposing resource
patches, ALWAYS keep requests ≤ limits — the same validation that caught us will
reject naive agent-generated fixes. The findings contract's proposed_fix commands
must respect this invariant.

### Entry 1.2 — Design correction: what CrashLoopBackOff really requires

**Problem:** Original plan broke the app by deleting a configmap key reference.
Reality check: a missing ConfigMap produces `FailedMount` + pods stuck in
`ContainerCreating` — containers never start, so there is no actual *crash loop*
and no previous-container logs. Wrong failure class for the scenario name.

**Solution:** Redesigned `crashloop.py`: corrupt the mounted nginx config instead
(inject `this_directive_does_not_exist` directive). Container starts, nginx hits
`[emerg] unknown directive ... default.conf:3`, exits 1, kubelet retries with
backoff → true CrashLoopBackOff WITH previous-container logs as the smoking gun.
Verified line captured from the live cluster:

```
2026/08/24 14:03:15 [emerg] 1#1: unknown directive "this_directive_does_not_exist"
in /etc/nginx/conf.d/default.conf:3
```

**Evolution:** The demo app gained an nginx-healthz ConfigMap mount specifically so
config corruption can produce genuine crash loops. Scenario difficulty ranking
updated in chaos/README.md.

### Entry 1.3 — The trap scenario behaves exactly as designed

**Result (not a bug — the point):** `probe-fail.py` repoints probes to
`/healthz-deprecated` (404). Live verification showed the split-brain signature:
pods cycling through restarts while the nginx process itself stays perfectly
healthy — logs are CLEAN. An agent that only reads pod logs will find nothing;
it must correlate rising restart counters with the livenessProbe spec and test
the endpoint. This is our hardest golden case and the best demo of multi-tool
reasoning.

### Entry 1.4 — Verification methodology fix (wrong pod, wrong conclusion)

**Problem:** When checking crash-loop logs we grabbed pod index `[0]` sorted by
startTime — which selected the *oldest healthy* pod. `kubectl logs --previous`
failed with "previous terminated container not found", which would have looked
like a broken script if we'd trusted the first error message.

**Solution:** Select the NEWEST pod (`items[-1]` with startTime sort) or filter by
restartCount > 0 before reading previous-container logs.

**Evolution:** This exact pitfall goes into the incident-triage skill: "when
investigating a crashing workload, target pods by restartCount desc / newest
startTime, not list order."

### Status at end of Day 1

- kind cluster `sentinel-demo` up on 4.8 GB Docker VM ✓
- Fragile baseline app deployed & health-verified ✓
- All 4 chaos scenarios fire + revert cleanly, signatures confirmed ✓
- Next: TrueForge runtime, MCP connectors, model provider, sandbox.

---

## Day 2 — Aug 24, 2026 (evening) · TrueForge Integration

### Entry 2.1 — No Kubernetes MCP in the connector catalog (risk materialized, fallback worked)

**Problem:** TrueForge's built-in catalog lists 14 SaaS connectors (linear,
notion, sentry, github...) — zero Kubernetes. The hackathon guide's
"connect from catalog" path doesn't exist for our domain.

**Solution:** `kubernetes-mcp-server` (containers/, brew-installable Go binary)
serves **streamable-HTTP MCP natively** — no wrapper needed:

```
kubernetes-mcp-server --port 9236 --bind-address 127.0.0.1 \
  --kubeconfig ~/.kube/config --disable-destructive
```

Verified with a raw JSON-RPC handshake + `tools/list`: 16 tools
(pods_list/get/log/top/run, events_list, resources_get/list, nodes_top...).

**Bonus discovery:** `--disable-destructive` strips every destructive tool at
the MCP layer — defense-in-depth on top of the approval gate.

**Evolution:** Architecture updated: metrics evidence comes from
metrics-server-backed `pods_top`/`nodes_top` instead of a Prometheus MCP for
now (8 GB RAM budget; in-cluster Prometheus deferred). Skill Phase 3 rewritten
to match.

### Entry 2.2 — The Add-MCP dialog fails silently (and how we bypassed it)

**Problem:** Filling TrueForge's "Add MCP server" form and clicking Add did
nothing: no error, console clean, dialog stayed open. Retried after browser
session drops — same silent failure. Meanwhile the API showed the truth:
`GET /api/v1/settings/mcp-servers → {"data":[]}`.

**Solution:** Talked to TrueForge's own API directly. Three Zod validation
errors taught us the exact request shape (each error message = free schema doc):

```
POST /api/v1/settings/mcp-servers
{"manifest":{"type":"remote","name":"kubernetes",
 "url":"http://127.0.0.1:9236/mcp","description":"...",
 "auth":{"type":"header","headers":{"X-Sentinel-Local":"kind-demo"}}}}
```

→ `auth_status: authenticated`. Note: custom remotes REQUIRE ≥1 auth header;
we send a harmless dummy that the k8s MCP ignores.

**Evolution:** UI flakiness is survivable when the product has an honest API.
Also documented in OPERATOR-SETUP.md so judges can reproduce setup via API if
the dialog misbehaves for them too.

### Entry 2.3 — Browser automation vs SPA session drops (workaround)

**Problem:** The TrueForge SPA repeatedly dropped our automation browser's
session ("empty page" snapshots mid-flow), losing dialog state twice.

**Solution:** Re-navigate → wait ~10s for hydration → re-snapshot each time.
For state changes, prefer the API route (Entry 2.2) over click-paths.

### Status at end of Day 2 session

- TrueForge running at :8790 ✓
- kubernetes MCP connector registered & authenticated ✓
- metrics-server installed (`--kubelet-insecure-tls` patched for kind), real
  usage data flowing ✓
- Pending user action: paste OpenRouter key (Settings → Models) + Daytona key
  (Settings → Sandbox providers) — see docs/OPERATOR-SETUP.md

---

## Day 2 (late) — Validation Suite Green

### Entry 3.1 — bash `local` + `set -u` ordering trap

**Problem:** `run_golden.sh` died instantly: `line 79: name: unbound variable`.
Cause: `local name="$1" fixture=".../${name}_expected.json"` on ONE line — bash
expands `$name` while processing the same declaration list, before the earlier
assignment in that same line takes effect under `set -u`.

**Solution:** Split into separate `local` statements per variable.

### Entry 3.2 — Safety check false positive (benign metadata vs functional drift)

**Problem:** First `test_safety.sh` run failed its immutability check — but the
diff showed only rollout bookkeeping (`observedGeneration` bump,
condition `lastUpdateTime`, terminating-replica counters). The actual workload
spec was identical before/after. A test that fails on healthy behavior is worse
than no test.

**Solution:** Snapshot now compares FUNCTIONAL state only: container spec
(image/resources/probes/volumes via jsonpath+json normalization), spec
replicas, configmap payloads, readyReplicas. Re-run: clean PASS.

**Evolution:** Same lesson as Entry 1.4 — verify you're measuring the right
thing before trusting a red signal.

### Status after validation suite

```
tests/run_golden.sh   → RESULTS: 4 passed, 0 failed — ALL GOLDEN SIGNATURES VERIFIED
tests/test_safety.sh  → SAFETY CHECKS: 0 failure(s)
```

Every chaos scenario provably produces its documented evidence signature, every
fixture pattern is resolvable in the live cluster, and the agent-facing tool
surface is provably non-destructive.

---

### Entry 3.3 — Two timing races the first green run hid (found by re-verification)

**Problem:** The golden suite passed 4/4 on its first run — then FAILED on a
fresh re-run. `imagepull` broke twice in different ways:
1. *Signature race:* pods flip `ErrImagePull → ImagePullBackOff` within
  seconds; polling only for `ErrImagePull` loses the race ~50% of the time.
2. *Evidence-availability race:* kubelet emits Warning events asynchronously
   AFTER pod status flips. Checking events once, immediately after the status
   signature appears, sees an empty event list intermittently.

The uncomfortable lesson: a suite that passes once proves nothing about
flakiness. Only the second run exposed both races.

**Solution:**
- Signature matcher now accepts BOTH phases:
  `"reason": "(ErrImagePull|ImagePullBackOff)"`.
- Evidence resolution became a retry loop (7 × 5s) that only passes when ALL
  fixture patterns resolve; on exhaustion it prints exactly which patterns
  never appeared and dumps live pods/events.

**Evolution:** The suite now tests evidence *availability*, not just existence,
and failure output is self-diagnosing. Both fixes verified by two consecutive
full-suite runs post-change.

---

---

## Day 3 — Aug 27, 2026 · Live Agent Execution, Sandbox & Persistence Proof

### Entry 4.1 — Daytona remote sandbox execution & network boundary

**Problem:** In session `01m1199y92m775hj5w89sezv0a`, the agent called Daytona sandbox `exec` to generate and run a Python script (`/tmp/patch_k8s.py`). The script attempted to connect directly to `https://127.0.0.1:57595` and failed with `Connection refused`.

**Result & Analysis:** This was a textbook demonstration of container quarantine. The Daytona sandbox runs on isolated remote infrastructure connected via a NATS bridge. It has zero network route into the host machine's internal loopback interface where the kind API server is bound. Generated untrusted code is physically isolated from the host.

**Evolution:** All live cluster inspections must travel through the authorized `kubernetes-mcp-server` channel rather than raw socket connections from the sandbox container. The skill directs cluster queries to MCP tools and reserves sandbox execution for data correlation.

---

### Entry 4.2 — Layer-2 Approval Gate verified live

**Problem:** Proving that an LLM agent doesn't prematurely mutate live Kubernetes workloads when given a crash-loop incident.

**Solution:** In turn `01m1199y9bsjqej6w0c98cd4bp.local`, the agent accurately identified the corrupted directive `this_directive_does_not_exist 42;` in ConfigMap `nginx-healthz`. Instead of mutating the cluster, the agent generated the corrected YAML and exact `kubectl patch` / `kubectl rollout restart` commands, stopped at the approval gate, and presented the plan for operator approval. Functional cluster state pre-approval remained 100% immutable.

---

### Entry 4.3 — SQLite-backed cross-turn persistence verified

**Problem:** Stateless LLM applications lose context once a turn completes or if a user returns hours later.

**Solution:** We created a follow-up turn in session `01m1199y92m775hj5w89sezv0a` asking: *"In one sentence, what was the exact root cause of the incident we just investigated?"* The agent retrieved full incident context directly from TrueForge's SQLite database (`turn` and `thread_context_log` tables) and answered verbatim with the exact ConfigMap key, file path, and syntax error without repeating any diagnostic tool queries.

---

### Status at end of Day 3

- Kind cluster `sentinel-demo` up and healthy ✓
- Kubernetes MCP server streaming tools with `--disable-destructive` ✓
- TrueForge runtime active at :8790 ✓
- OpenRouter model provider + Daytona sandbox provider configured & verified ✓
- Golden validation suite: 4/4 passed ✓
- Safety suite: 0 failures ✓
- Live agent triage & root-cause isolation verified ✓
- Approval-gate safety verified (Layer 2) ✓
- Session persistence verified ✓
- Qodo audit log (`docs/qodo-log.md`) & Blog submission draft (`blog/post.md`) published ✓

