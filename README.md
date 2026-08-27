# K8s Sentinel — Autonomous Kubernetes Incident Triage Agent

> **An agent that investigates your cluster instead of telling you what to investigate.**
>
> Built for the [Agent Harness Hackathon](https://www.wemakedevs.org/blogs/agent-harness-hackathon-kick-off)
> (WeMakeDevs × TrueFoundry, Aug 24–30 2026) on **TrueForge**, TrueFoundry's open-source
> agent harness, with **Qodo** guarding code quality across every pull request.

**Build status:** 🚧 Active hackathon development · [JOURNEY.md](JOURNEY.md) documents every problem we hit and how the project evolved.

---

## Table of Contents

1. [The Problem](#the-problem)
2. [What K8s Sentinel Does](#what-k8s-sentinel-does)
3. [Architecture](#architecture)
4. [Why TrueForge Is Load-Bearing Here](#why-trueforge-is-load-bearing-here)
5. [Repository Layout](#repository-layout)
6. [Quickstart](#quickstart)
7. [Chaos Scenarios](#chaos-scenarios)
8. [The Findings Contract](#the-findings-contract)
9. [Safety Model](#safety-model)
10. [Validation Strategy](#validation-strategy)
11. [Code Quality Process (Qodo)](#code-quality-process-qodo)
12. [Hardware & Resource Notes](#hardware--resource-notes)
13. [Roadmap](#roadmap)

---

## The Problem

When a production Kubernetes incident hits, the on-call engineer's reality looks like this:

```
kubectl get pods -A                    → 47 pods, 6 not Ready
kubectl describe pod api-7d9f-x2m4n    → wall of events, nothing obvious
kubectl logs --previous ...            → 3,000 lines, tail means nothing
prometheus graph                       → which metric? over what window?
GPT/Claude chat                        → "here's what you could check..."  ← advice, not action
```

LLMs are excellent at *explaining* what someone should do next. They are not,
out of the box, systems that can **do the work**: hold tool credentials, query live
systems, correlate evidence from multiple sources, execute analysis code safely,
and stop at the exact line where a human must decide.

K8s Sentinel closes that gap for one high-value workflow: **incident triage**.

## What K8s Sentinel Does

Give it an incident report — *"payments-api is CrashLooping in namespace prod"* — and it autonomously runs a full investigation:

1. **DISCOVER** — queries the cluster via MCP tools: lists pods, events, and workload health in the target namespace.
2. **PARALLEL-DIVE** — spawns one subagent per failing pod; each pulls logs (`--previous` included), `describe` output, and recent events.
3. **CORRELATE** — queries Prometheus metrics (CPU, memory, restart rate) around the incident window.
4. **SANDBOXED ANALYSIS** — generates Python analysis scripts on demand and executes them inside a Daytona sandbox to correlate events with metric anomalies. Generated code never touches the host.
5. **SYNTHESIZE** — produces ranked root-cause hypotheses, each backed by concrete evidence references (real event names, pod states, metric series).
6. **PROPOSE** — emits an exact remediation plan as commands, with every mutating command flagged `REQUIRES_APPROVAL`.
7. **STOP** — waits for explicit human approval before any state-changing action. This is a feature, not a limitation.

Output is a structured JSON findings document ([schema below](#the-findings-contract)) — parseable by humans at 3 AM and by CI pipelines alike.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        TRUEFORGE HARNESS (local)                     │
│                      npx @truefoundry/trueforge                      │
│                                                                      │
│  ┌──────────────┐   ┌──────────────────────────────────────────┐    │
│  │ Saved Agent: │   │            SKILL: incident-triage        │    │
│  │ K8s Sentinel ├─►│  DISCOVER → PARALLEL-DIVE → CORRELATE →  │    │
│  └──────┬───────┘   │  SANDBOX-ANALYSIS → SYNTHESIZE → PROPOSE │    │
│         │           └──────────────────────────────────────────┘    │
│         │                                                            │
│  ┌──────┴───────────────────────────────┐                           │
│  │        ORCHESTRATION LAYER           │                           │
│  │  dynamic subagents · approvals gate  │                           │
│  │  persistent sessions (SQLite)        │                           │
│  └──┬──────────┬──────────┬────────────┬┘                           │
└─────┼──────────┼──────────┼────────────┼─────────────────────────────┘
      │MCP       │MCP       │sandbox API │subagents
      ▼          ▼          ▼            ▼
┌──────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────────┐
│ k8s MCP  │ │Prom MCP │ │ Daytona  │ │ Per-pod dive     │
│ server   │ │ server  │ │ sandbox  │ │ subagents (n)    │
└────┬─────┘ └────┬────┘ └──────────┘ └────────┬─────────┘
     │            │                            │
     ▼            ▼                            ▼
┌──────────────────────────┐         ┌──────────────────┐
│   kind cluster (local)   │         │ same k8s MCP,    │
│  ┌────────────────────┐  │         │ isolated context │
│  │ demo-app (fragile) │  │         └──────────────────┘
│  │ prometheus (lite)  │  │
│  │ metrics-server     │  │
│  └────────────────────┘  │
└──────────────────────────┘
```

**Data flow of one triage run:**

```
user report ──► saved agent session
                  │
                  ├─ kubernetes-server MCP ──► kind API ──► pods/events/deployments
                  ├─ prometheus MCP ──► metrics series (2h window)
                  ├─ spawn N subagents (one per failing pod)
                  ├─ Daytona sandbox ◄── generated analysis script
                  │        └─ reads evidence bundle, returns correlation matrix
                  ▼
             findings.json (hypotheses + evidence + proposed_fix)
                  ▼
             APPROVAL GATE ──(human approves)──► fix applied ──► recovery verified
```

### Component Inventory

| Component | Technology | Role |
|---|---|---|
| Agent harness | TrueForge (Node ≥22, SQLite, single process) | Runtime: tools, skills, sessions, approvals |
| Cluster tools | `kubernetes-server` MCP | Live pod/deployment/event/log queries |
| Metrics tools | `mcp-prometheus` MCP | Time-series around incident window |
| Code execution | Daytona sandbox | Isolated running of generated analysis code |
| Parallelism | TrueForge dynamic subagents | One investigator per failing pod |
| Target cluster | kind v0.32 on Docker Desktop (macOS ARM64) | Safe, disposable demo environment |
| Fragile app | nginx-based deployment + probes + configmaps | Realistic failure surface for scenarios |
| Failure injection | Python scripts driving `kubectl` | Reproducible incidents (chaos harness) |
| Quality gate | Qodo (PR-level, whole-repo context) | Every PR reviewed before merge |

## Why TrueForge Is Load-Bearing Here

This project would be a different (worse-shaped) thing without the harness:

| Capability | Without TrueForge | With TrueForge |
|---|---|---|
| Tool access | Hand-rolled function-calling loop, manual auth per API | Connectors: MCP servers configured once in Settings |
| Running generated code | Self-managed containers, escape risks | Sandbox-as-tool; agent requests isolation itself |
| Human control | DIY confirmation UI, easy to bypass | Approval gate is runtime-enforced |
| Parallel investigation | Custom worker pool, shared-state bugs | Dynamic subagents spawned per task |
| Incident memory | Re-implement vector store / history DB | Persistent sessions survive process restarts |
| Triage playbook | Giant system prompt, re-sent every turn | Git-backed SKILL.md loaded when needed |

Each piece exists because triage demands it — see [JOURNEY.md Entry 0.1](JOURNEY.md).

## Repository Layout

```text
k8s-sentinel/
├── README.md                 ← you are here
├── JOURNEY.md                ← problems faced, solutions, evolution (living doc)
├── infra/
│   ├── kind-config.yaml      ← control-plane-only kind cluster (8 GB Mac sized)
│   └── demo-app/
│       ├── deployment.yaml   ← deliberately fragile 3-replica app
│       └── ...
├── chaos/
│   ├── README.md             ← how to trigger each scenario
│   └── scenarios/
│       ├── crashloop.py      ← bad configmap ref → CrashLoopBackOff
│       ├── oomkill.py        ← memory limit < baseline → OOMKilled loop
│       ├── probe-fail.py     ← liveness endpoint dies → restart storm
│       └── imagepull.py      ← nonexistent tag → ImagePullBackOff
├── skills/
│   └── incident-triage/
│       └── SKILL.md          ← the triage playbook (imported into TrueForge)
├── tests/
│   ├── golden/               ← known-answer fixtures per scenario
│   ├── run_golden.sh         ← full validation suite
│   └── test_safety.sh        ← proves no mutation happens pre-approval
├── docs/
│   ├── findings-schema.md    ← output contract spec
│   ├── safety-proof.md       ← recorded approval-gate evidence
│   ├── session-persistence.md← cross-session recall demonstration
│   └── qodo-log.md           ← every Qodo finding and its resolution
└── blog/
    └── post.md               ← Field Report track submission draft
```

## Quickstart

Prereqs: Node.js ≥ 22, Docker Desktop, kind ≥ 0.30, kubectl, Python 3.9+.

### 1. Start the target cluster

```bash
kind create cluster --name sentinel-demo --config infra/kind-config.yaml
kubectl apply -f infra/demo-app/
kubectl get pods -n demo          # expect 3/3 Running
```

### 2. Start TrueForge

```bash
npx @truefoundry/trueforge
# → http://localhost:8790  (single process, SQLite-backed; keep it on localhost)
```

### 3. Configure providers (one-time, via UI)

| Where | What |
|---|---|
| Settings → Models | Add OpenRouter provider; key from env var, never committed |
| Settings → Connectors | Add `kubernetes-server` MCP; add `mcp-prometheus` |
| Settings → Skills | Import `skills/incident-triage/SKILL.md` from this repo |
| Settings → Sandbox providers | Select Daytona; add API key |

All keys via environment variables. Nothing secret lives in this repository.

### 4. Compose the agent

In TrueForge chat: select model → enable both connectors + skill + sandbox + subagents → paste the Sentinel system contract (see `docs/findings-schema.md`) → **Save Agent** as `K8s Sentinel`. It then appears in the Agents Library, reusable forever.

### 5. Break something and watch it triage

```bash
python chaos/scenarios/crashloop.py
```

Then tell the saved agent:

> Investigate: payments pods are crash-looping in namespace demo.

Watch DISCOVER → parallel subagent dives → metric correlation → sandboxed analysis → evidence-linked findings → proposed fix waiting at the approval gate.

## Chaos Scenarios

One command each. Idempotent, self-describing, safe to re-run:

| Script | Injected failure | Expected agent diagnosis class |
|---|---|---|
| `crashloop.py` | Deployment references missing configmap key | CONFIG_MISSING |
| `oomkill.py` | Memory limit set below app baseline | RESOURCE_LIMIT_MISMATCH |
| `probe-fail.py` | Liveness endpoint stops returning 200 | PROBE_ENDPOINT_FAILURE |
| `imagepull.py` | Image tag does not exist in registry | IMAGE_TAG_INVALID |

Full trigger/revert instructions: [`chaos/README.md`](chaos/README.md).
Golden expected-answer fixtures per scenario: [`tests/golden/`](tests/golden/).

## The Findings Contract

Every triage ends in this shape (full spec: [`docs/findings-schema.md`](docs/findings-schema.md)):

```json
{
  "incident_id": "inc-20260825-crashloop-demo",
  "severity": "SEV2",
  "findings": [
    {
      "hypothesis": "Deployment references configmap key DATABASE_URL that does not exist",
      "confidence": 0.94,
      "evidence": [
        {"source": "k8s_event", "ref": "demo/payments-api-7d9f-x2m4n: FailedMount ..."},
        {"source": "log", "ref": "previous-container exit 1: config load failed"},
        {"source": "metric", "ref": "kube_pod_container_status_restarts_total rising"}
      ]
    }
  ],
  "root_cause": {"summary": "missing configmap key", "confidence": 0.91},
  "proposed_fix": {
    "commands": [
      {"cmd": "kubectl -n demo set env deploy/payments-api --from=configmap/app-config", "mutating": true}
    ],
    "rollback": "revert deployment revision"
  }
}
```

Hard rules enforced by the skill:
- Every hypothesis carries ≥ 1 resolvable evidence reference.
- Confidence < 0.6 ⇒ presented as open question, never root cause.
- Every mutating command carries `"mutating": true` ⇒ blocked behind approval.

## Safety Model

Three concentric guarantees:

1. **Read-by-default.** The skill instructs: discovery/diagnosis actions are read-only against the cluster; the agent may run them freely.
2. **Runtime-enforced approval.** Mutating verbs (scale, rollout, apply, delete, set) are proposed as plan text only. TrueForge's approval flow gates execution; the agent structurally cannot skip it.
3. **Blast-radius containment.** The demo target is a disposable kind cluster. Sandbox code executes off-host at Daytona. Worst case = rebuild the cluster in 90 seconds.

Verification: `tests/test_safety.sh` triggers each scenario, asks the agent to fix, then diffs cluster state pre/post — must be byte-identical until human approval is given. Recorded results: [`docs/safety-proof.md`](docs/safety-proof.md).

## Validation Strategy

Known-answer testing against the chaos harness:

```
tests/run_golden.sh
  for scenario in crashloop oomkill probe-fail imagepull:
      1. inject failure
      2. invoke saved agent on fresh session
      3. parse findings.json
      4. assert root_cause class matches golden fixture
      5. assert every evidence.ref resolves to a real object/event/series
      6. revert scenario, record PASS/FAIL
```

Success bar for ship: 4/4 correct diagnosis classes, zero unresolvable evidence refs, zero mutations pre-approval.

## Code Quality Process (Qodo)

This repo is developed PR-first so Qodo reviews everything with whole-repo context:

- All work lands via feature branches → PR → Qodo review → fix findings → merge.
- [`docs/qodo-log.md`](docs/qodo-log.md) records each finding and its resolution — the audit trail judges can follow.
- Standards: typed Python where practical, shell scripts pass `shellcheck`, YAML validated in CI-style local checks, no secrets ever committed (enforced by `.gitignore` + grep check before push).

## Hardware & Resource Notes

Built and tested on a MacBook (Apple Silicon, 8 GB RAM):

- Docker Desktop VM allocated ~4.8 GB → kind control-plane capped accordingly in `infra/kind-config.yaml`.
- Prometheus runs scrape-lite (demo namespace only); fallback path uses metrics-server + `kubectl top` if memory pressure appears.
- TrueForge local mode: single Node process + SQLite — negligible footprint.
- Dev services stay **off** unless explicitly started; nothing auto-starts on reboot.

Full constraint log in JOURNEY.md.

## Roadmap

- [x] Problem selection & architecture (Day 0)
- [x] kind cluster + fragile demo app
- [x] MCP connectors live (kubernetes via streamable-HTTP kubernetes-mcp-server)
- [x] Chaos harness (4 scenarios) + golden fixtures — **all signatures verified live**
- [x] incident-triage skill + findings contract written
- [x] Golden-case validation suite green (`tests/run_golden.sh`: 4/4)
- [x] Safety proof, layer 1 & 2 (`tests/test_safety.sh`: 0 failures, agent approval-gate verified in `docs/safety-proof.md`)
- [x] metrics-server metrics pipeline (Prometheus deferred — RAM budget)
- [x] Model provider (OpenRouter) + sandbox keys (Daytona) configured
- [x] Saved K8s Sentinel agent composed in TrueForge
- [x] Agent-level triage run + approval-gate proof (Layer 2 verified)
- [x] Cross-session persistence demo verified (`docs/session-persistence.md`)
- [x] Qodo code quality review log published (`docs/qodo-log.md`)
- [x] Demo video produced (`demo_video/k8s_sentinel_demo.mp4`, 1080p, text overlays, AI voiceover)
- [ ] Hackathon submission form (before Aug 30)

---

*Built with TrueForge by TrueFoundry · Code quality via Qodo · Part of the WeMakeDevs Agent Harness Hackathon.*
