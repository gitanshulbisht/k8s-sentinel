import subprocess
import os
import json

EDGE_TTS = "/Users/anshulbisht/Library/Python/3.14/bin/edge-tts"
VOICE = "en-US-ChristopherNeural"

NEW_SCRIPTS = {
    "scene3f_cockpit": (
        "Beyond conversational outputs, Sentinel leverages TrueForge's generative UI capabilities to produce an interactive Incident Cockpit. "
        "This standalone web artifact provides SREs with a visual mission control: live pod fleet topology, a side-by-side syntax-highlighted diff "
        "of the corrupted ConfigMap, a full event audit trail, and an interactive rollout simulator. "
        "Instead of combing through terminal output, operators get immediate visual clarity."
    ),
    "scene3g_watcher": (
        "Furthermore, K8s Sentinel is not limited to reactive chat prompts. "
        "We built a proactive event watcher daemon that streams cluster events in real time. "
        "The moment Kubelet reports a BackOff, OOM-kill, or probe failure, the watcher autonomously dispatches a triage session "
        "to the TrueForge API, launching the complete investigation before the on-call engineer even opens their laptop."
    ),
    "scene3h_autonomy_cost": (
        "Sentinel also delivers flexible policy-based autonomy. "
        "In production namespaces, Guarded Autonomy strictly enforces our zero-drift approval gate. "
        "In dev and staging clusters, Closed-Loop Auto-Heal resolves and verifies outages in under thirty seconds. "
        "And by routing through TrueForge with Gemini Flash and DeepSeek, each triage costs less than a fifth of a cent, "
        "reducing operational LLM costs by over ninety-five percent."
    )
}

durations = {}
for scene_id, text in NEW_SCRIPTS.items():
    mp3_out = f"demo_video/neural_audio/{scene_id}.mp3"
    print(f"Synthesizing {scene_id}...")
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

with open("demo_video/neural_durations.json", "r") as f:
    existing = json.load(f)

existing.update(durations)
with open("demo_video/neural_durations.json", "w") as f:
    json.dump(existing, f, indent=2)

print("Updated demo_video/neural_durations.json")
