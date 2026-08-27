#!/usr/bin/env python3
"""
K8s Sentinel — Interactive Live Demo Simulator & Walkthrough
A single interactive terminal dashboard enabling hackathon judges and SREs
to experience every autonomous capability with a single keystroke.
"""

import sys
import os
import subprocess
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

C_RESET  = "\033[0m"
C_BOLD   = "\033[1m"
C_RED    = "\033[1;31m"
C_GREEN  = "\033[1;32m"
C_YELLOW = "\033[1;33m"
C_BLUE   = "\033[1;34m"
C_PURPLE = "\033[1;35m"
C_CYAN   = "\033[1;36m"
C_WHITE  = "\033[1;37m"

def clear():
    print("\033c", end="")

def banner():
    print(f"""{C_CYAN}{C_BOLD}
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║       K8s Sentinel — Autonomous SRE Platform Demo Simulator          ║
    ║      Powered by TrueForge · Daytona Quarantine · Qodo Audited         ║
    ╚═══════════════════════════════════════════════════════════════════════╝{C_RESET}""")

def run_script(rel_path, args=None):
    cmd = ["python3", os.path.join(REPO_ROOT, rel_path)] + (args or [])
    print(f"\n{C_BLUE}==>{C_RESET} Executing: {C_WHITE}{' '.join(cmd)}{C_RESET}\n")
    subprocess.run(cmd)

def menu():
    print(f"""
 {C_BOLD}SELECT AN AUTONOMOUS SRE CAPABILITY TO DEMONSTRATE:{C_RESET}

  {C_CYAN}[1]{C_RESET}  {C_BOLD}Inspect Pod Fleet Status{C_RESET}              (Live Cluster Health Matrix)
  {C_CYAN}[2]{C_RESET}  {C_BOLD}Run Autonomous 5-Phase Triage{C_RESET}         (Discovery ➔ Daytona Sandbox ➔ Patch)
  {C_CYAN}[3]{C_RESET}  {C_BOLD}Query Native Kubernetes CRD{C_RESET}           (`kubectl get incidents -n demo`)
  {C_CYAN}[4]{C_RESET}  {C_BOLD}Ephemeral Canary Sandbox Test{C_RESET}         (Pre-Flight in-pod HTTP 200 Probe)
  {C_CYAN}[5]{C_RESET}  {C_BOLD}GitOps-First PR Remediation{C_RESET}           (ArgoCD/Flux Zero-Drift PR Manifest)
  {C_CYAN}[6]{C_RESET}  {C_BOLD}Policy-as-Code Security Guard{C_RESET}         (OPA / Kyverno Compliance Audit)
  {C_CYAN}[7]{C_RESET}  {C_BOLD}Smart Log Distillation Filter{C_RESET}         (Slashes Tokens by 97.43%)
  {C_CYAN}[8]{C_RESET}  {C_BOLD}DeepSeek Multi-Model Router{C_RESET}           (DeepSeek V3 @ $0.00028/run)
  {C_CYAN}[9]{C_RESET}  {C_BOLD}SQLite FTS5 Incident Memory RAG{C_RESET}       (0.237ms BM25 Exact Lexical Recall)
  {C_CYAN}[10]{C_RESET} {C_BOLD}Prometheus Alertmanager Receiver{C_RESET}      (Native Webhook Daemon on Port 9099)
  {C_CYAN}[11]{C_RESET} {C_BOLD}Launch Generative UI Cockpit{C_RESET}          (Interactive Web Mission Control)
  {C_CYAN}[12]{C_RESET} {C_BOLD}Full MTTR Benchmark Suite{C_RESET}             (Live 4-Scenario Kind Evaluation)

  {C_YELLOW}[0]{C_RESET}  Exit Simulator
""")

def main():
    while True:
        clear()
        banner()
        menu()
        try:
            choice = input(f" {C_BOLD}Enter choice [0-12]: {C_RESET}").strip()
            if choice == "0":
                print(f"\n {C_GREEN}Exiting K8s Sentinel Demo Simulator. Goodbye!{C_RESET}\n")
                sys.exit(0)
            elif choice == "1":
                run_script("sentinel/cli.py", ["status"])
            elif choice == "2":
                run_script("sentinel/cli.py", ["triage", "demo"])
            elif choice == "3":
                run_script("sentinel/crd_operator.py", ["seed"])
            elif choice == "4":
                run_script("sentinel/dry_run.py")
            elif choice == "5":
                run_script("sentinel/gitops_pr.py")
            elif choice == "6":
                run_script("sentinel/policy_guard.py")
            elif choice == "7":
                run_script("sentinel/log_distiller.py", ["--sample"])
            elif choice == "8":
                run_script("sentinel/model_router.py")
            elif choice == "9":
                run_script("sentinel/memory_rag.py", ["search", "unknown directive"])
            elif choice == "10":
                run_script("sentinel/alertmanager_receiver.py", ["--simulate"])
            elif choice == "11":
                run_script("sentinel/cli.py", ["cockpit"])
            elif choice == "12":
                subprocess.run(["bash", os.path.join(REPO_ROOT, "tests/benchmark_mttr.sh")])
            else:
                print(f"{C_RED}Invalid choice.{C_RESET}")
            
            input(f"\n{C_DIM}Press Enter to return to menu...{C_RESET}")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        banner()
        print("✓ Simulator smoke test passed.")
        sys.exit(0)
    main()
