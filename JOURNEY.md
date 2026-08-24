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

*(entries below are appended as each phase lands)*

<!-- TEMPLATE FOR FUTURE ENTRIES

### Entry N.M — <short title>

**Problem:** <what broke / what was hard>

**Solution:** <what actually fixed it, with command/file references>

**Evolution:** <what changed in the repo/architecture/plan as a result>

-->
