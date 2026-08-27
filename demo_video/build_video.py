import os
import subprocess
import json

scenes = [
    'scene1_intro',
    'scene2_arch',
    'scene3a_demo_discovery',
    'scene3b_demo_sandbox',
    'scene3c_demo_approval',
    'scene4_learnings'
]

print("Encoding individual scene clips...")
concat_list = []
for sid in scenes:
    img = f"demo_video/slides/{sid}.png"
    audio = f"demo_video/audio/{sid}.mp3"
    clip = f"demo_video/clips/{sid}.mp4"
    
    # Encode clip: pad audio with a tiny 0.5s pause at the end for smooth narration flow
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img,
        "-i", audio,
        "-af", "apad=pad_dur=0.5",
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
    concat_list.append(f"file '{os.path.abspath(clip)}'")
    print(f"  ✓ Encoded {clip}")

concat_file = "demo_video/concat.txt"
with open(concat_file, "w") as f:
    f.write("\n".join(concat_list) + "\n")

print("Concatenating into final demo video...")
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

# Probe final video
probe_out = subprocess.check_output([
    "ffprobe", "-v", "quiet",
    "-show_entries", "format=duration,size,bit_rate",
    "-of", "json", final_video
])
meta = json.loads(probe_out)["format"]
dur = float(meta["duration"])
size_mb = int(meta["size"]) / (1024 * 1024)

print(f"\n==================================================")
print(f"🎉 FINAL DEMO VIDEO CREATED:")
print(f"Path:     {final_video}")
print(f"Duration: {dur:.2f} seconds ({dur/60:.2f} minutes)")
print(f"Size:     {size_mb:.2f} MB")
print(f"Format:   1080p MP4 (H.264 / AAC 44.1kHz)")
print(f"==================================================")
