# Findings Contract — K8s Sentinel Output Specification

Every completed triage MUST end with a single JSON document in this exact
shape. It is simultaneously:
- the human-readable incident report,
- the machine-checkable target for `tests/run_golden.sh`,
- and the input format for the approval gate.

## Schema

```jsonc
{
  "incident_id": "string, inc-YYYYMMDD-<slug>",
  "generated_at": "ISO-8601 timestamp",
  "namespace": "string",
  "severity": "SEV1 | SEV2 | SEV3",
  // SEV1: workload fully unavailable · SEV2: degraded/partially failing
  // SEV3: risk detected, service currently healthy

  "findings": [
    {
      "hypothesis": "one-sentence causal claim",
      "confidence": 0.0,            // 0.0–1.0
      "evidence": [                 // >= 1 REQUIRED per finding
        {
          "source": "k8s_event | log | metric | spec",   // 'spec' = live object YAML/JSON
          "ref": "verbatim quote or resolvable reference",
          // k8s_event: "<type> <reason>: <message>" as returned by the API
          // log:      "pod/<name>: <exact line>"
          // metric:   "<series query> @<window>: <observed shape>"
          // spec:     "<resource>/<name>.<jsonpath>: <value>"
          "collected_by": "orchestrator | subagent:<id> | sandbox"
        }
      ]
    }
  ],

  "root_cause": {
    "summary": "short class label + one-line explanation",
    "class": "IMAGE_TAG_INVALID | RESOURCE_LIMIT_MISMATCH |
              PROBE_ENDPOINT_FAILURE | CONFIG_INVALID | OTHER",
    "confidence": 0.0                  // must be >= 0.6 or root_cause is null
  },
  "open_questions": [                  // hypotheses below 0.6 confidence land here
    { "question": "...", "check_that_would_resolve_it": "..." }
  ],

  "proposed_fix": {
    "commands": [
      {
        "cmd": "kubectl ...",
        "mutating": true,              // true => REQUIRES human approval gate
        "why": "links this command to a finding index"
      }
    ],
    "verification_steps": ["how we confirm recovery after applying"],
    "rollback": "exact revert procedure"
  }
}
```

## Invariants (enforced in golden tests)

1. **Evidence resolvability** — every `evidence[].ref` must match something real:
   an event line present in `kubectl get events`, a pod that exists, a metric
   series that returns data, or a field value equal to the live spec.
2. **Confidence floor** — `root_cause.confidence >= 0.6` is REQUIRED for a
   non-null root cause; weaker beliefs go to `open_questions`.
3. **Mutation flagging** — any command whose verb ∈ {apply, patch, scale, set,
   rollout, delete, edit, replace} MUST carry `"mutating": true`.
4. **K8s validation invariants** — proposed patches must satisfy API-side
   validation (requests ≤ limits; probe paths returning 2xx on the declared
   port; images existing in registry). A fix the API server would reject is a bug.
5. **Rollback presence** — non-empty `rollback` whenever any mutating command exists.

## Golden classes → expected root_cause.class

| Chaos scenario | Expected class | Primary evidence source |
|---|---|---|
| `imagepull.py` | IMAGE_TAG_INVALID | k8s_event (`Failed to pull image`) |
| `oomkill.py` | RESOURCE_LIMIT_MISMATCH | spec (`lastState.terminated.reason=OOMKilled`) + events |
| `probe-fail.py` | PROBE_ENDPOINT_FAILURE | spec (livenessProbe path) + restart metrics |
| `crashloop.py` | CONFIG_INVALID | log (previous-container `[emerg]` line) |

## System-contract snippet (paste into saved agent instructions)

```
You are K8s Sentinel. Follow skills/incident-triage phases in order, skipping
sandbox analysis when the cause is already unambiguous. Terminate every triage
with ONE findings JSON document conforming to docs/findings-schema.md. Never
execute a mutating command; propose it with mutating=true and stop at approval.
If confidence < 0.6, report open_questions instead of a root cause.
```
