#!/usr/bin/env bash
# ==============================================================================
# K8s Sentinel — Automated MTTR (Mean Time to Resolution) Benchmark Suite
# ==============================================================================
# Evaluates autonomous SRE performance across all 4 chaos engineering scenarios.
# Measures:
#   1. MTTD (Mean Time to Detect)
#   2. Triage & Diagnostic Latency (Time to Root Cause Isolation)
#   3. Total MTTR (Time to Remediate & Verify)
#   4. Token Consumption & Operational Cost (OpenRouter Gemini/DeepSeek routing)
#   5. Safety Invariant (0 bytes pre-approval state drift)
#
# Generates SLA Scorecard and exports report to docs/benchmark-report.md
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

export REPO_ROOT
python3 "${SCRIPT_DIR}/benchmark_engine.py" "$@"
