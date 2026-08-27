import os
import subprocess
import json

new_scenes = ["scene3f_cockpit", "scene3g_watcher", "scene3h_autonomy_cost"]

print("Encoding new video clips...")
for sid in new_scenes:
    img = f"demo_video/slides_v2/{sid}.png"
    audio = f"demo_video/neural_audio/{sid}.mp3"
    clip = f"demo_video/clips_v2/{sid}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img,
        "-i", audio,
        "-af", "apad=pad_dur=0.6",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-shortest",
        clip
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    print(f"  ✓ Encoded {clip}")

full_sequence = [
    "scene1_intro",
    "scene2_arch",
    "scene2b_chaos",
    "scene3a_injection",
    "scene3b_trueforge_flow",
    "scene3c_sandbox_rootcause",
    "scene3d_approval_recovery",
    "scene3e_persistence",
    "scene3f_cockpit",
    "scene3g_watcher",
    "scene3h_autonomy_cost",
    "scene4_learnings"
]

concat_list = []
for sid in full_sequence:
    clip = f"demo_video/clips_v2/{sid}.mp4"
    concat_list.append(f"file '{os.path.abspath(clip)}'")

concat_file = "demo_video/concat_master.txt"
with open(concat_file, "w") as f:
    f.write("\n".join(concat_list) + "\n")

print("\nConcatenating master 12-scene demo video...")
final_video = "demo_video/k8s_sentinel_demo.mp4"
concat_cmd = [
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", concat_file,
    "-c", "copy",
    final_video
]
subprocess.run(concat_cmd, check=True, stderr=subprocess.DEVNULL)

probe_out = subprocess.check_output([
    "ffprobe", "-v", "quiet",
    "-show_entries", "format=duration,size,bit_rate",
    "-of", "json", final_video
])
meta = json.loads(probe_out)["format"]
dur = float(meta["duration"])
size_mb = int(meta["size"]) / (1024 * 1024)

print(f"\n==================================================")
print(f"🎬 K8S SENTINEL MASTER DEMO VIDEO COMPLETE:")
print(f"Path:     {final_video}")
print(f"Duration: {dur:.2f} seconds ({dur/60:.2f} minutes)")
print(f"Size:     {size_mb:.2f} MB")
print(f"Scenes:   {len(full_sequence)} complete scenes")
print(f"Features: Real TrueForge UI, Generative UI Cockpit,")
print(f"          Proactive Watcher Daemon, Autonomy Spectrum,")
print(f"          Neural Audio Narration")
print(f"==================================================")

# Copy to artifacts directory
art_path = "/Users/anshulbisht/.gemini/antigravity-cli/brain/c8d7e606-7c07-4f74-9490-4b7a3ee11a85/k8s_sentinel_demo.mp4"
subprocess.run(["cp", final_video, art_path], check=True)
print(f"✓ Copied master video to {art_path}")
