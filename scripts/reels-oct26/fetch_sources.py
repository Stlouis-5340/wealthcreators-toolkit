#!/usr/bin/env python3
"""Download the source windows named in cuts.json.

Vimeo sections come from the HLS playlists (see hls_section.py). The Money
Babies file is pulled from the public Dropbox folder zip. YouTube is attempted
and recorded; a bot-check or missing format does not fail the run, because
reel 3 has an explicit Vimeo fallback.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CUTS = json.loads((ROOT / "cuts.json").read_text())
WORK = ROOT / "work"


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd[:6]), "...", flush=True)
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def ytdlp_playlist(fmt: str) -> str:
    vimeo = CUTS["vimeo"]
    proc = run(
        [
            "yt-dlp",
            "--referer",
            vimeo["referer"],
            "--no-playlist",
            "-g",
            "-f",
            fmt,
            vimeo["player"],
        ]
    )
    url = proc.stdout.strip().splitlines()[0]
    if not url.startswith("http"):
        raise SystemExit(f"yt-dlp -g returned no URL for {fmt}:\n{proc.stderr[-500:]}")
    return url


def fetch_vimeo_window(reel: dict, video_url: str, audio_url: str) -> None:
    pad = float(reel.get("download_pad") or 0)
    start = max(0.0, float(reel["source_in"]) - pad)
    end = float(reel["source_out"]) + pad
    out = WORK / f"{reel['window_name']}.mp4"
    work = WORK / f"{reel['window_name']}.parts"
    cmd = [
        sys.executable,
        str(ROOT / "hls_section.py"),
        "--video-url",
        video_url,
        "--audio-url",
        audio_url,
        "--start",
        f"{start:.3f}",
        "--end",
        f"{end:.3f}",
        "--out",
        str(out),
        "--work",
        str(work),
        "--referer",
        CUTS["vimeo"]["referer"],
    ]
    print(f"slicing {reel['id']} {start:.2f}-{end:.2f}", flush=True)
    subprocess.check_call(cmd)


def fetch_dropbox() -> None:
    dest = WORK / "money_babies.mp4"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"dropbox already present: {dest}", flush=True)
        return
    url = CUTS["dropbox"]["folder_url"]
    zip_path = WORK / "dropbox_folder.zip"
    print("downloading dropbox folder zip", flush=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp, zip_path.open("wb") as out:
        shutil.copyfileobj(resp, out)
    want = CUTS["dropbox"]["filename"]
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        match = [n for n in names if Path(n).name == want]
        if not match:
            raise SystemExit(f"{want!r} not in zip. Found: {names}")
        zf.extract(match[0], WORK / "dropbox_extract")
        extracted = WORK / "dropbox_extract" / match[0]
        # zip may store a leading slash that extract strips
        if not extracted.exists():
            hits = list((WORK / "dropbox_extract").rglob(want))
            if not hits:
                raise SystemExit(f"extracted zip but {want} is missing")
            extracted = hits[0]
        shutil.copyfile(extracted, dest)
    print(f"wrote {dest} ({dest.stat().st_size} bytes)", flush=True)


def attempt_youtube() -> None:
    page = CUTS["youtube"]["page"]
    log = WORK / "youtube_attempt.txt"
    try:
        proc = subprocess.run(
            ["yt-dlp", "--skip-download", "--no-playlist", "--print", "%(title)s\t%(duration)s", page],
            text=True,
            capture_output=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        log.write_text(f"TIMEOUT\n{exc}\n")
        print("youtube attempt timed out; reel 3 will use the Vimeo fallback", flush=True)
        return
    log.write_text(f"exit={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n")
    if proc.returncode == 0:
        print(f"youtube reachable: {proc.stdout.strip()}", flush=True)
    else:
        tail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "no stderr"
        print(f"youtube unavailable ({tail}); reel 3 will use the Vimeo fallback", flush=True)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    attempt_youtube()
    fetch_dropbox()
    video_url = ytdlp_playlist(CUTS["vimeo"]["video_format"])
    audio_url = ytdlp_playlist(CUTS["vimeo"]["audio_format"])
    for reel in CUTS["reels"]:
        if reel["source"] == "vimeo":
            fetch_vimeo_window(reel, video_url, audio_url)
    print("fetch done", flush=True)


if __name__ == "__main__":
    main()
