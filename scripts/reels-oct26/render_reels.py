#!/usr/bin/env python3
"""Cut, crop, loudness-normalize, and encode the three reels in cuts.json.

Landscape webinar sources use the speaker crop in cuts.json. The Money Babies
file is already 1080x1920. Output is H.264 + AAC, 1080x1920, faststart.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUTS = json.loads((ROOT / "cuts.json").read_text())
WORK = ROOT / "work"
OUT = ROOT / "output"


def ffprobe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height,sample_rate,channels",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(proc.stdout)


def measure_loudnorm(src: Path, ss: float, to: float | None) -> dict:
    spec = CUTS["loudnorm"]
    af = f"loudnorm=I={spec['I']}:TP={spec['TP']}:LRA={spec['LRA']}:print_format=json"
    cmd = ["ffmpeg", "-hide_banner", "-ss", f"{ss:.3f}"]
    if to is not None:
        cmd += ["-t", f"{to - ss:.3f}"]
    cmd += ["-i", str(src), "-vn", "-af", af, "-f", "null", "-"]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr[-2000:])
    text = proc.stderr
    start = text.rfind("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise SystemExit(f"loudnorm json missing for {src}\n{text[-1500:]}")
    return json.loads(text[start : end + 1])


def loudnorm_filter(measured: dict) -> str:
    spec = CUTS["loudnorm"]
    return (
        f"loudnorm=I={spec['I']}:TP={spec['TP']}:LRA={spec['LRA']}"
        f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
        f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
        f":offset={measured['target_offset']}:linear=true"
    )


def video_filter(reel: dict) -> str:
    if reel["crop"] == "speaker":
        c = CUTS["speaker_crop"]
        crop = f"crop={c['w']}:{c['h']}:{c['x']}:{c['y']},"
    elif reel["crop"] == "none":
        crop = ""
    else:
        raise SystemExit(f"unknown crop {reel['crop']}")
    return crop + "scale=1080:1920:flags=lanczos,setsar=1,fps=30,format=yuv420p"


def source_for(reel: dict) -> tuple[Path, float]:
    if reel["source"] == "dropbox":
        return WORK / "money_babies.mp4", 0.0
    media = WORK / f"{reel['window_name']}.mp4"
    sidecar = media.with_suffix(".json")
    meta = json.loads(sidecar.read_text())
    return media, float(meta["source_start"])


def render_one(reel: dict) -> Path:
    src, timeline_zero = source_for(reel)
    if not src.exists():
        raise SystemExit(f"missing source {src}. Run fetch_sources.py first.")
    src_in = float(reel["source_in"])
    local_in = src_in - timeline_zero
    if local_in < -0.05:
        raise SystemExit(f"{reel['id']} in-point {src_in} is before downloaded window zero {timeline_zero}")
    local_in = max(0.0, local_in)
    local_out = None
    if reel["source_out"] is not None:
        local_out = float(reel["source_out"]) - timeline_zero
        if local_out <= local_in:
            raise SystemExit(f"{reel['id']} out-point is not after in-point")

    print(f"rendering {reel['id']} local {local_in:.3f}-{local_out}", flush=True)
    measured = measure_loudnorm(src, local_in, local_out)
    print(
        f"  input loudness I={measured['input_i']} TP={measured['input_tp']} LRA={measured['input_lra']}",
        flush=True,
    )
    out = OUT / f"{reel['id']}.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-ss",
        f"{local_in:.3f}",
    ]
    if local_out is not None:
        cmd += ["-t", f"{local_out - local_in:.3f}"]
    cmd += [
        "-vf",
        video_filter(reel),
        "-af",
        loudnorm_filter(measured),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-profile:v",
        "high",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        "-colorspace",
        "bt709",
        "-color_primaries",
        "bt709",
        "-color_trc",
        "bt709",
        str(out),
    ]
    subprocess.check_call(cmd)
    info = ffprobe(out)
    duration = float(info["format"]["duration"])
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = next(s for s in info["streams"] if s["codec_type"] == "audio")
    print(
        f"  {out.name}: {duration:.2f}s {video['width']}x{video['height']} "
        f"{video['codec_name']}/{audio['codec_name']} {info['format']['size']} bytes",
        flush=True,
    )
    if video["codec_name"] != "h264" or audio["codec_name"] != "aac":
        raise SystemExit(f"{out.name} codecs are {video['codec_name']}/{audio['codec_name']}")
    if int(video["width"]) != 1080 or int(video["height"]) != 1920:
        raise SystemExit(f"{out.name} is {video['width']}x{video['height']}")
    if not (55.0 <= duration <= 70.5):
        raise SystemExit(f"{out.name} duration {duration:.2f}s is outside 55-70s")
    return out


def copy_artifacts(paths: list[Path]) -> None:
    artifacts = Path("/opt/cursor/artifacts")
    if not artifacts.is_dir():
        print("artifacts dir missing; outputs stay in output/", flush=True)
        return
    for path in paths:
        dest = artifacts / path.name
        shutil.copy2(path, dest)
        print(f"artifact {dest}", flush=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    made = [render_one(reel) for reel in CUTS["reels"]]
    captions = ROOT / "captions.md"
    if captions.exists():
        copy_artifacts(made + [captions])
    else:
        copy_artifacts(made)
    print("render done", flush=True)


if __name__ == "__main__":
    main()
