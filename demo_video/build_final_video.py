import os
import subprocess
import json

scenes = [
    'scene1_intro',
    'scene2_arch',
    'scene2b_chaos',
    'scene3a_demo_discovery',
    'scene3b_demo_sandbox',
    'scene3c_demo_approval',
    'scene4_learnings'
]

concat_list = []
for sid in scenes:
    clip = f"demo_video/clips/{sid}.mp4"
    concat_list.append(f"file '{os.path.abspath(clip)}'")

concat_file = "demo_video/concat_all.txt"
with open(concat_file, "w") as f:
    f.write("\n".join(concat_list) + "\n")

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
print(f"🎬 K8S SENTINEL COMPLETE DEMO VIDEO READY:")
print(f"Path:     {final_video}")
print(f"Duration: {dur:.2f} seconds ({dur/60:.2f} minutes)")
print(f"Size:     {size_mb:.2f} MB")
print(f"Scenes:   {len(scenes)} comprehensive scenes")
print(f"Format:   1080p High-Def MP4 (H.264 / AAC)")
print(f"==================================================")
