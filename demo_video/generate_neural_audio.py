import subprocess
import os
import json

EDGE_TTS = "/Users/anshulbisht/Library/Python/3.14/bin/edge-tts"
VOICE = "en-US-ChristopherNeural"

SCRIPTS = {
    "scene1_intro": (
        "Imagine it is three a.m., pager duty goes off, and critical payments pods are crash-looping. "
        "Traditional Large Language Models are purely advisory. They tell you ten theoretical things you could check, "
        "but they cannot safely inspect your cluster. "
        "Enter K8s Sentinel, an autonomous Kubernetes incident triage agent built on TrueForge. "
        "Sentinel takes direct action. It interrogates live cluster APIs, analyzes logs in an isolated sandbox, "
        "and stops at a human approval gate before making any changes to production."
    ),
    
    "scene2_arch": (
        "Under the hood, TrueForge is load-bearing across the entire stack. "
        "The TrueForge harness manages our multi-turn orchestration, agent skill playbooks, and persistent session storage. "
        "For cluster introspection, Sentinel connects through a streamable Kubernetes Model Context Protocol server, "
        "with non-destructive flags strictly enforced. "
        "When event logs require deep correlation, TrueForge spins up an off-host Daytona sandbox over a NATS bridge. "
        "And crucially, any mutating command is halted by a runtime human approval gate, "
        "ensuring zero unauthorized drift in production."
    ),

    "scene2b_chaos": (
        "To ensure Sentinel handles diverse outage scenarios, we built a comprehensive chaos engineering harness. "
        "Our test suite covers four distinct failure modes: configuration corruption in crashloop, "
        "memory threshold exhaustion in OOM-kill, endpoint mismatch in probe-fail, "
        "and missing registry tags in image-pull. "
        "Our automated validation suite verifies all four golden signatures live in the cluster, "
        "achieving a flawless four out of four pass rate with zero safety violations."
    ),

    "scene3a_injection": (
        "Let us see the complete flow in action. We inject an outage by running our crashloop chaos script. "
        "Immediately, the payments deployment begins failing health probes, and replicas enter CrashLoopBackOff. "
        "Rather than forcing an engineer to comb through kubectl outputs manually, "
        "we report the incident to K8s Sentinel inside the TrueForge web application."
    ),

    "scene3b_trueforge_flow": (
        "Here is the real TrueForge application in action. "
        "Sentinel receives our incident prompt and autonomously executes its five-phase incident triage playbook. "
        "In the live execution timeline, you see Sentinel calling the Kubernetes MCP server to list cluster resources, "
        "fetch pod definitions, and inspect event streams. "
        "It dynamically spawns specialized sub-agents to inspect the nginx configuration map, "
        "all monitored in real-time through the TrueForge interface."
    ),

    "scene3c_sandbox_rootcause": (
        "When correlating event history, Sentinel routes execution to an isolated Daytona remote sandbox. "
        "The sandbox runs in a quarantined container with zero network access to our host cluster. "
        "Inside TrueForge, Sentinel delivers its root cause analysis: "
        "the nginx healthz ConfigMap contains an invalid syntax directive, 'this_directive_does_not_exist 42', "
        "at line three of default dot conf, causing nginx startup failure."
    ),

    "scene3d_approval_recovery": (
        "Next comes safety. Sentinel formulates the exact remediation patch, "
        "but because it mutates cluster state, TrueForge intercepts it at the human approval gate. "
        "Zero bytes of production state drift before human review. "
        "Once the operator reviews and approves the fix, the corrected ConfigMap is applied, "
        "and the deployment rolls out successfully, returning all replicas to three of three running."
    ),

    "scene3e_persistence": (
        "TrueForge also solves the context loss problem. "
        "In a follow-up turn, we ask Sentinel to recall the exact root cause in one sentence. "
        "Without making a single new diagnostic query, Sentinel instantly recalls the exact corrupted file "
        "and directive verbatim from TrueForge's persistent SQLite database."
    ),

    "scene4_learnings": (
        "Building K8s Sentinel delivered three key engineering insights. "
        "First, remote sandbox quarantine is mandatory to protect cluster control planes from untrusted code. "
        "Second, distributed Kubernetes timing races must be handled with multi-phase status matchers. "
        "And third, our codebase was guarded by Qodo pull request reviews, "
        "achieving zero bugs, zero rule violations, and strict POSIX compliance. "
        "Explore the full source code on GitHub at github dot com slash gitanshulbisht slash k8s-sentinel. Thank you!"
    )
}

os.makedirs("demo_video/neural_audio", exist_ok=True)
durations = {}

for scene_id, text in SCRIPTS.items():
    mp3_out = f"demo_video/neural_audio/{scene_id}.mp3"
    print(f"Generating neural voiceover for {scene_id}...")
    cmd = [EDGE_TTS, "--voice", VOICE, "--text", text, "--write-media", mp3_out]
    subprocess.run(cmd, check=True)
    
    probe = subprocess.check_output([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json", mp3_out
    ])
    dur = float(json.loads(probe)["format"]["duration"])
    durations[scene_id] = dur
    print(f"  ✓ {scene_id}: {dur:.2f}s")

with open("demo_video/neural_durations.json", "w") as f:
    json.dump(durations, f, indent=2)

print("\nAll neural audio generated successfully!")
print(f"Total duration: {sum(durations.values()):.2f}s ({sum(durations.values())/60:.2f} minutes)")
