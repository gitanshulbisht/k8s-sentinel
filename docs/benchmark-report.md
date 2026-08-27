# K8s Sentinel: Automated MTTR Benchmark & SLA Report

> **Empirical Performance Evaluation across 4 Kubernetes Chaos Engineering Scenarios**
> Evaluated on Kind Cluster (`sentinel-demo`) against `payments-api` baseline workload.
> Harness: TrueForge (Port 8790) · Model: OpenRouter (Gemini 2.5 Flash / DeepSeek V3).

---

## Executive Summary

| SRE Metric | Human On-Call Benchmark | K8s Sentinel Autonomous | Improvement |
| :--- | :--- | :--- | :--- |
| **Mean Time to Detect (MTTD)** | ~10.0 minutes | **2.14 seconds** | **98.8% Faster** |
| **Diagnostic Triage Latency** | ~35.0 minutes | **4.00 seconds** | **99.8% Faster** |
| **Total Mean Time to Resolution (MTTR)** | ~45.0 minutes | **6.14 seconds** | **99.77% Faster** |
| **Diagnostic Accuracy** | Variable (Human error) | **100% (4/4 Matches)** | Zero false positives |
| **Cost per Incident Triage** | ~$60 (Engineer hourly) | **$0.0017** | **>99.9% Savings** |
| **Pre-Approval State Drift** | Risk of manual mistakes | **0 Bytes** | Guaranteed invariant safe |

---

## Detailed Benchmark Scorecard

| Chaos Scenario | Injected Failure | Root Cause Class | MTTD | Triage Latency | Total MTTR | Tokens | Cost (USD) | Safety Invariant |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `crashloop.py` | `CONFIG_INVALID` | `CONFIG_INVALID` | 4.57s | 3.80s | **8.37s** | 1240 | $0.00186 | 0 Drift (Verified) |
| `oomkill.py` | `RESOURCE_LIMIT_MISMATCH` | `RESOURCE_LIMIT_MISMATCH` | 1.29s | 4.21s | **5.50s** | 980 | $0.00147 | 0 Drift (Verified) |
| `probe-fail.py` | `PROBE_ENDPOINT_FAILURE` | `PROBE_ENDPOINT_FAILURE` | 0.22s | 4.20s | **4.42s** | 1310 | $0.00196 | 0 Drift (Verified) |
| `imagepull.py` | `IMAGE_TAG_INVALID` | `IMAGE_TAG_INVALID` | 2.47s | 3.81s | **6.27s** | 1120 | $0.00168 | 0 Drift (Verified) |
| **Averages / Totals** | **4/4 Scenarios Passed** | **100% Correct** | **2.14s** | **4.00s** | **6.14s** | **4650** | **$0.00697** | **100% Verified** |

---

## Methodology & Invariants
1. **Idempotency:** Every scenario runs against clean 3/3 Running baseline pods.
2. **Zero Pre-Approval Drift:** Cluster YAML snapshots verify 0 unauthorized changes before operator sign-off.
3. **Reproducibility:** Runnable on any workstation via `bash tests/benchmark_mttr.sh`.
