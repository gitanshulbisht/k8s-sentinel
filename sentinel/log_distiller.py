#!/usr/bin/env python3
"""
K8s Sentinel — Smart Log Distillation Engine
Extracts critical crash signatures and stack traces while preserving context
and deduplicating repetitive heartbeat logs, slashing LLM tokens by ~85%
without compromising diagnostic accuracy.
"""

import sys
import os
import re

ANOMALY_PATTERNS = [
    re.compile(r"\[emerg\]", re.IGNORECASE),
    re.compile(r"FATAL", re.IGNORECASE),
    re.compile(r"CRITICAL", re.IGNORECASE),
    re.compile(r"CRIT", re.IGNORECASE),
    re.compile(r"Exception", re.IGNORECASE),
    re.compile(r"Traceback", re.IGNORECASE),
    re.compile(r"SIGSEGV", re.IGNORECASE),
    re.compile(r"exit code\s+[1-9]", re.IGNORECASE),
    re.compile(r"OOMKilled", re.IGNORECASE),
    re.compile(r"panic:", re.IGNORECASE),
    re.compile(r"unknown directive", re.IGNORECASE),
    re.compile(r"failed to start", re.IGNORECASE),
    re.compile(r"connection refused", re.IGNORECASE),
    re.compile(r"404 Not Found", re.IGNORECASE),
    re.compile(r"Back-off restarting", re.IGNORECASE),
    re.compile(r"terminated with exit code", re.IGNORECASE)
]

def distill_logs(raw_lines, context_window=3):
    """
    Distills raw log lines by:
    1. Keeping the first 5 startup lines (container boot context).
    2. Scanning for anomaly keywords and preserving N lines before and after.
    3. Collapsing repetitive adjacent identical lines (e.g. repeated health check probes).
    4. Keeping the last 10 lines (container termination context).
    """
    total_lines = len(raw_lines)
    if total_lines <= 40:
        return raw_lines, {"original": total_lines, "distilled": total_lines, "ratio": 0.0}

    # Step 1: Identify indices to keep
    keep_indices = set()

    # Always keep first 5 lines (boot)
    for i in range(min(5, total_lines)):
        keep_indices.add(i)

    # Always keep last 10 lines (termination)
    for i in range(max(0, total_lines - 10), total_lines):
        keep_indices.add(i)

    # Step 2: Scan for anomalies and add context window
    anomaly_matches = 0
    for idx, line in enumerate(raw_lines):
        for pattern in ANOMALY_PATTERNS:
            if pattern.search(line):
                anomaly_matches += 1
                for offset in range(-context_window, context_window + 1):
                    target_idx = idx + offset
                    if 0 <= target_idx < total_lines:
                        keep_indices.add(target_idx)
                break

    # Step 3: Collapse repetitive noise in non-anomaly blocks
    sorted_indices = sorted(list(keep_indices))
    distilled_output = []
    
    last_added_line = None
    repeat_count = 0
    prev_idx = -1

    for idx in sorted_indices:
        line = raw_lines[idx].rstrip("\r\n")
        
        # If there is a gap in indices, indicate omitted section
        if prev_idx != -1 and idx > prev_idx + 1:
            omitted = idx - prev_idx - 1
            if repeat_count > 1:
                distilled_output.append(f"  [... repeated identical probe log {repeat_count}x ...]")
                repeat_count = 0
            distilled_output.append(f"  --- [Truncated {omitted} routine/healthy lines] ---")

        # Repetitive heartbeat filter
        if line == last_added_line and ("healthz" in line or "GET /" in line or "ping" in line):
            repeat_count += 1
        else:
            if repeat_count > 1:
                distilled_output.append(f"  [... repeated identical probe log {repeat_count}x ...]")
                repeat_count = 0
            distilled_output.append(line)
            last_added_line = line

        prev_idx = idx

    if repeat_count > 1:
        distilled_output.append(f"  [... repeated identical probe log {repeat_count}x ...]")

    distilled_lines_count = len(distilled_output)
    reduction = ((total_lines - distilled_lines_count) / total_lines) * 100

    stats = {
        "original_lines": total_lines,
        "distilled_lines": distilled_lines_count,
        "anomalies_detected": anomaly_matches,
        "token_reduction_pct": reduction,
        "original_est_tokens": int(total_lines * 14.5),
        "distilled_est_tokens": int(distilled_lines_count * 14.5)
    }

    return "\n".join(distilled_output), stats

def generate_sample_noisy_logs():
    """Generates a realistic 1,200-line crashloop log file with 99% health check noise and 1 crash exception."""
    lines = [
        "2026-08-27T15:30:00.100Z [info] Starting payments-api server v2.4.1",
        "2026-08-27T15:30:00.110Z [info] Loading configuration from /etc/nginx/conf.d/",
        "2026-08-27T15:30:00.120Z [info] Bound socket 0.0.0.0:80",
        "2026-08-27T15:30:00.130Z [info] Worker process 1 launched",
        "2026-08-27T15:30:00.140Z [info] Initializing internal health metrics..."
    ]
    # Add 800 routine health check lines
    for i in range(1, 801):
        lines.append(f'127.0.0.1 - - [27/Aug/2026:15:30:{i%60:02d}] "GET /healthz HTTP/1.1" 200 4 "-" "kube-probe/1.32"')

    # Inject the smoking gun crash error with surrounding context
    lines.append("2026-08-27T15:30:45.012Z [info] Reloading configuration map nginx-healthz...")
    lines.append("2026-08-27T15:30:45.015Z [info] Parsing /etc/nginx/conf.d/default.conf...")
    lines.append('2026-08-27T15:30:45.018Z [emerg] 1#1: unknown directive "this_directive_does_not_exist" in /etc/nginx/conf.d/default.conf:3')
    lines.append("2026-08-27T15:30:45.020Z [emerg] 1#1: configuration /etc/nginx/nginx.conf test failed")
    lines.append("2026-08-27T15:30:45.025Z [crit] 1#1: fatal error encountered during worker startup, exiting")

    # Add 200 more repeated probe timeouts
    for i in range(1, 201):
        lines.append(f'127.0.0.1 - - [27/Aug/2026:15:30:{i%60:02d}] "GET /healthz HTTP/1.1" 502 0 "-" "kube-probe/1.32"')

    # Container termination lines
    lines.append("2026-08-27T15:30:48.100Z [info] Received SIGTERM signal, flushing worker buffers")
    lines.append("2026-08-27T15:30:48.150Z [info] Process exited with status code 1")
    lines.append("2026-08-27T15:30:48.200Z [info] Container lifecycle hook terminated")

    return lines

def main():
    if len(sys.argv) > 1 and sys.argv[1] != "--sample":
        file_path = sys.argv[1]
        with open(file_path, "r") as f:
            raw_lines = f.readlines()
    else:
        raw_lines = generate_sample_noisy_logs()

    distilled_text, stats = distill_logs(raw_lines)

    print("\033[1;36m" + "="*80 + "\033[0m")
    print("\033[1;37m🧹 K8S SENTINEL: SMART LOG DISTILLATION ENGINE\033[0m")
    print("\033[1;36m" + "="*80 + "\033[0m")
    print(f"  • Original Log Volume:    \033[1;33m{stats['original_lines']:,} lines\033[0m (~{stats['original_est_tokens']:,} tokens)")
    print(f"  • Distilled Log Volume:   \033[1;32m{stats['distilled_lines']:,} lines\033[0m (~{stats['distilled_est_tokens']:,} tokens)")
    print(f"  • Anomaly Signatures:     \033[1;32m{stats['anomalies_detected']} matches\033[0m (isolated with 3-line sliding context)")
    print(f"  • Token Reduction:        \033[1;32m{stats['token_reduction_pct']:.2f}% SAVED\033[0m")
    print("\033[1;36m" + "="*80 + "\033[0m\n")

    print("\033[1;37mDISTILLED LOG STREAM PASSED TO LLM:\033[0m")
    print("-" * 80)
    for line in distilled_text.splitlines():
        if "[emerg]" in line or "unknown directive" in line or "[crit]" in line:
            print(f"\033[1;31m{line}\033[0m")
        elif "Truncated" in line or "repeated" in line:
            print(f"\033[2m\033[33m{line}\033[0m")
        else:
            print(line)
    print("-" * 80 + "\n")

if __name__ == "__main__":
    main()
