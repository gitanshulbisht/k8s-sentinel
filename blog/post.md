# K8s Sentinel: Building an Autonomous Kubernetes Incident Triage Agent on TrueForge

> *An agent that investigates your cluster instead of telling you what to investigate.*
>
> Built for the **Agent Harness Hackathon** (WeMakeDevs × TrueFoundry) on **TrueForge**, with **Qodo** guarding code quality.

---

## The 3 AM Reality Check: Advice vs. Action

If you have ever been on-call for a Kubernetes production outage at 3 AM, you know the dread of the terminal:

```text
kubectl get pods -A                    → 47 pods, 6 not Ready
kubectl describe pod api-7d9f-x2m4n    → wall of 200 events
kubectl logs --previous ...            → 3,000 lines of noisy application output
metrics-server / top                   → which container is leaking memory?
ChatGPT / Claude prompt                → "Here are 10 things you could check..."
```

That last line represents the current limitation of AI in DevOps. Raw LLMs are excellent at offering advice, but they do not *do the work*. They don't hold credentials, they don't query live cluster APIs, they can't execute correlation scripts in an isolated sandbox, and they don't know where to stop so that a human can verify a destructive change before it brings down production.

For the **Agent Harness Hackathon**, we built **K8s Sentinel**: an autonomous SRE incident triage agent built on **TrueForge** (TrueFoundry's open-source agent harness), backed by **Daytona** sandboxing and verified through **Qodo**.

---

## Why TrueForge Is Load-Bearing

The hackathon explicitly challenged participants to move beyond "another chat interface around an LLM." We designed K8s Sentinel so that every core feature of TrueForge was essential to the agent's operation:

| Capability | What Happens Without TrueForge | How TrueForge Powers K8s Sentinel |
|---|---|---|
| **MCP Connectors** | Hand-rolled curl scripts and bespoke token auth | Standardized `kubernetes-mcp-server` exposed directly into the agent context |
| **Sandbox Isolation** | Agent runs unsafe code on the host machine | Daytona remote sandbox tool; Python analysis scripts run in quarantine |
| **Human Approvals** | DIY confirmation logic, easily bypassed by LLM hallucination | Runtime-enforced approval gate on mutating verbs (`patch`, `apply`, `scale`) |
| **Incident Memory** | Context lost on page reload or process restart | SQLite-backed persistent sessions allow cross-day incident recall |
| **Dynamic Skills** | Massive, brittle system prompts copied every message | Git-backed `SKILL.md` loaded dynamically when incident triage begins |

---

## System Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        TRUEFORGE HARNESS (local)                     │
│                      npx @truefoundry/trueforge                      │
│                                                                      │
│  ┌──────────────┐   ┌──────────────────────────────────────────┐    │
│  │ Saved Agent: │   │            SKILL: incident-triage        │    │
│  │ K8s Sentinel ├──►│  DISCOVER → PARALLEL-DIVE → CORRELATE →  │    │
│  │              │   │  SANDBOX-ANALYSIS → SYNTHESIZE → PROPOSE │    │
│  └──────┬───────┘   └──────────────────────────────────────────┘    │
│         │                                                            │
│  ┌──────┴───────────────────────────────────────────────────────┐   │
│  │        RUNTIME: dynamic subagents · approval gates · SQLite  │   │
│  └──────┬───────────────────────┬───────────────────────────────┘   │
└─────────┼───────────────────────┼───────────────────────────────────┘
          │MCP Tools              │Sandbox API
          ▼                       ▼
    ┌───────────┐           ┌───────────┐
    │  k8s MCP  │           │  Daytona  │
    │  server   │           │  sandbox  │
    └─────┬─────┘           └───────────┘
          │
          ▼
   ┌──────────────┐
   │ kind cluster │
   │ (local demo) │
   └──────────────┘
```

### The Triage Lifecycle
1. **DISCOVER**: Queries cluster health, listings, and event logs via the Kubernetes MCP connector.
2. **DIVE**: Isolates failing pods, inspecting `lastState.terminated` and previous-container logs.
3. **CORRELATE**: Samples metrics (CPU, memory, restart rate slope) to detect pressure.
4. **SANDBOX**: For non-obvious issues, generates Python analysis code and runs it inside Daytona.
5. **SYNTHESIZE & GATE**: Produces a standardized JSON Findings document and proposes exact remediation commands with `mutating: true` — pausing at the approval gate.

---

## Building the Chaos Harness & Golden Cases

To ensure K8s Sentinel was battle-tested, we built a 4-scenario chaos engineering harness with known-answer golden fixtures:

1. **`crashloop.py` (CONFIG_INVALID):** Injects an invalid directive (`this_directive_does_not_exist 42;`) into an nginx ConfigMap. Container fails on boot with previous-container log smoking guns.
2. **`oomkill.py` (RESOURCE_LIMIT_MISMATCH):** Forces `requests.memory = limits.memory = 4Mi` on an app needing 12Mi baseline. Triggers exit 137 and OOMKilled events.
3. **`probe-fail.py` (PROBE_ENDPOINT_FAILURE):** Repoints liveness probes to a 404 endpoint (`/healthz-deprecated`). Container logs stay clean while restart counts climb — forcing the agent to inspect the probe spec rather than blindly reading logs.
4. **`imagepull.py` (IMAGE_TAG_INVALID):** Swaps image tag to `nginx:this-tag-does-not-exist-xyz`. Pods flip into `ImagePullBackOff`.

Our automated validation suite (`tests/run_golden.sh`) validates all 4 signatures in live cluster state:
```text
RESULTS: 4 passed, 0 failed — ALL GOLDEN SIGNATURES VERIFIED
```

---

## What Broke Along the Way (and How We Fixed It)

We maintained a living log in [JOURNEY.md](https://github.com/gitanshulbisht/k8s-sentinel/blob/main/JOURNEY.md). Here are three real engineering hurdles we hit:

### 1. The `set -u` Bash Ordering Trap
In `tests/run_golden.sh`, we wrote:
```bash
local name="$1" fixture=".../${name}_expected.json"
```
Under `set -u`, bash expands `$name` while processing the declaration list before the prior variable assignment took effect, crashing the script instantly with `name: unbound variable`. Separating into discrete `local` statements resolved it.

### 2. The Kubelet Event Timing Race
In testing `imagepull.py`, the validation passed once and failed on the next run. Why?
1. Pods flip from `ErrImagePull` to `ImagePullBackOff` within seconds. Grepping for only one phase lost the race ~50% of the time.
2. Kubelet emits Warning events asynchronously *after* pod status changes.
We resolved this by matching both status phases and implementing a bounded retry loop (7 × 5s) that explicitly waits for event availability.

### 3. Safety Immutability: Metadata vs. Functional Drift
Our safety test (`tests/test_safety.sh`) initially diffed full cluster YAML before and after chaos injection. It failed because Kubernetes updates bookkeeping metadata (`observedGeneration`, condition timestamps, terminating replica counters). We rewrote our state snapshotting logic to extract only functional properties (container specs, volumes, ConfigMap data), achieving a clean zero-drift pass.

---

## Guarding Quality with Qodo

Throughout the hackathon, **Qodo** acted as our automated architectural guardian. By analyzing pull requests with full repository context, Qodo caught:
- Destructive API exposure risks.
- Shell script portability flaws.
- Missing rollback commands in proposed remediation plans.

Every finding and its exact resolution is documented in [docs/qodo-log.md](https://github.com/gitanshulbisht/k8s-sentinel/blob/main/docs/qodo-log.md).

---

## Live Agent Demonstration: CrashLoop Triage & Recall

In our live evaluation, we triggered `crashloop.py` and instructed K8s Sentinel:
> *"Investigate: payments pods are crash-looping in namespace demo."*

### The Agent in Action
1. **Tool Invocation:** The agent called `resources_list` and `resources_get` via the Kubernetes MCP server.
2. **Sandbox Execution:** TrueForge initialized a Daytona container via NATS to analyze event logs.
3. **Exact Root Cause:** The agent found the exact smoking gun in `/etc/nginx/conf.d/default.conf:3`:
   ```nginx
   this_directive_does_not_exist 42;
   ```
4. **Approval Gate:** The agent provided the corrected ConfigMap and restart commands, explicitly stopping before execution for human review.
5. **Cross-Session Recall:** In a follow-up turn in the same session, we asked:
   *"In one sentence, what was the exact root cause of the incident we just investigated?"*
   The agent reconstructed context directly from TrueForge's SQLite database, responding immediately with the exact file, directive, and error reason without re-running queries.

---

## Conclusion

K8s Sentinel proves that with the right harness, AI agents can graduate from advisory chatbots into trusted, autonomous SRE investigators. TrueForge provided the mission-critical scaffolding — MCP tool routing, Daytona sandboxing, approval gates, and persistent sessions — while Qodo ensured the codebase remained production-grade.

The complete code, test suites, and documentation are open source:
👉 **GitHub:** [gitanshulbisht/k8s-sentinel](https://github.com/gitanshulbisht/k8s-sentinel)
