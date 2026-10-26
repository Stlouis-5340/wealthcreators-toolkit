#!/usr/bin/env python3
"""Download a time slice of a Vimeo (or any) HLS VOD playlist.

yt-dlp's ffmpeg section downloader mis-seeks Vimeo's fMP4 HLS and emits
broken NAL units. This script slices the media playlist on segment
boundaries, downloads only those byte-range segments, and remuxes them.

Usage:
  python3 hls_section.py --playlist-url URL --start 2070 --end 2180 --out clip.mp4
  python3 hls_section.py --video-url V --audio-url A --start 2070 --end 2180 --out clip.mp4

Writes a sidecar <out>.json with the source timestamp of local t=0.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def fetch_text(url: str, referer: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": referer,
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", "replace")


def resolve(base: str, ref: str) -> str:
    return urllib.parse.urljoin(base, ref)


def parse_media_playlist(text: str, playlist_url: str):
    """Return (init_url or None, list of (start, end, url))."""
    init_url = None
    segments = []
    pending_dur = None
    t = 0.0
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXT-X-MAP:"):
            # URI="..."
            uri = line.split('URI="', 1)[1].split('"', 1)[0]
            init_url = resolve(playlist_url, uri)
        elif line.startswith("#EXTINF:"):
            pending_dur = float(line.split(":", 1)[1].split(",", 1)[0])
        elif line.startswith("#"):
            continue
        else:
            if pending_dur is None:
                raise SystemExit(f"segment without EXTINF: {line[:80]}")
            url = resolve(playlist_url, line)
            segments.append((t, t + pending_dur, url))
            t += pending_dur
            pending_dur = None
    return init_url, segments


def select(segments, start: float, end: float):
    chosen = [s for s in segments if s[1] > start and s[0] < end]
    if not chosen:
        raise SystemExit(f"no segments overlap {start}-{end}")
    return chosen


def download(url: str, dest: Path, referer: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return
    tmp = dest.with_suffix(dest.suffix + ".partial")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Referer": referer},
    )
    with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
    tmp.replace(dest)


def write_local_playlist(path: Path, init_name: str | None, seg_names: list[str], durations: list[float]) -> None:
    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:6",
        "#EXT-X-PLAYLIST-TYPE:VOD",
        "#EXT-X-TARGETDURATION:8",
        "#EXT-X-MEDIA-SEQUENCE:0",
    ]
    if init_name:
        lines.append(f'#EXT-X-MAP:URI="{init_name}"')
    for name, dur in zip(seg_names, durations):
        lines.append(f"#EXTINF:{dur:.6f},")
        lines.append(name)
    lines.append("#EXT-X-ENDLIST")
    path.write_text("\n".join(lines) + "\n")


def remux(
    video_pl: Path,
    audio_pl: Path | None,
    out: Path,
    video_src_start: float = 0.0,
    audio_src_start: float | None = None,
) -> float:
    """Mux video + audio. File t=0 is video_src_start on the source clock.

    Vimeo publishes separate fMP4 playlists whose segment boundaries do not
    line up. Concatenating each and starting both at t=0 shifts the audio.
    Delay the later stream so a source timestamp lands at the same output time.
    Returns the audio delay in seconds (positive means audio starts later).
    """
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-allowed_extensions", "ALL"]
    delay = 0.0
    if audio_pl is None or audio_src_start is None:
        cmd += ["-i", str(video_pl), "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy"]
    else:
        delay = audio_src_start - video_src_start
        if delay >= -0.001:
            # Audio playlist's first sample is later on the source clock.
            cmd += ["-i", str(video_pl)]
            if delay > 0.001:
                cmd += ["-itsoffset", f"{delay:.6f}"]
            cmd += ["-i", str(audio_pl), "-map", "0:v:0", "-map", "1:a:0", "-c", "copy"]
        else:
            # Video playlist starts later; delay video and shift the origin.
            cmd += ["-itsoffset", f"{-delay:.6f}", "-i", str(video_pl), "-i", str(audio_pl)]
            cmd += ["-map", "0:v:0", "-map", "1:a:0", "-c", "copy"]
    cmd += ["-movflags", "+faststart", str(out)]
    subprocess.check_call(cmd)
    return delay


def slice_one(playlist_url: str, start: float, end: float, work: Path, referer: str, workers: int):
    text = fetch_text(playlist_url, referer)
    init_url, segments = parse_media_playlist(text, playlist_url)
    chosen = select(segments, start, end)
    work.mkdir(parents=True, exist_ok=True)
    init_name = None
    jobs = []
    if init_url:
        init_name = "init.mp4"
        jobs.append((init_url, work / init_name))
    names = []
    durs = []
    for i, (seg_start, seg_end, url) in enumerate(chosen):
        name = f"seg_{i:04d}.mp4"
        names.append(name)
        durs.append(seg_end - seg_start)
        jobs.append((url, work / name))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(download, url, dest, referer) for url, dest in jobs]
        for fut in as_completed(futs):
            fut.result()
    pl = work / "index.m3u8"
    write_local_playlist(pl, init_name, names, durs)
    return pl, chosen[0][0], chosen[-1][1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--playlist-url", help="Single muxed media playlist")
    ap.add_argument("--video-url", help="Video-only media playlist")
    ap.add_argument("--audio-url", help="Audio-only media playlist")
    ap.add_argument("--start", type=float, required=True, help="Source start seconds (inclusive)")
    ap.add_argument("--end", type=float, required=True, help="Source end seconds (exclusive)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--work", type=Path, help="Segment directory (default: <out>.parts)")
    ap.add_argument("--referer", default="https://vimeo.com/")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if not args.playlist_url and not args.video_url:
        ap.error("provide --playlist-url or --video-url")

    work = args.work or args.out.with_suffix(".parts")
    audio_src_start = None
    audio_src_end = None
    delay = 0.0
    if args.playlist_url:
        pl, src_start, src_end = slice_one(
            args.playlist_url, args.start, args.end, work, args.referer, args.workers
        )
        remux(pl, None, args.out)
        audio_note = None
    else:
        vpl, src_start, src_end = slice_one(
            args.video_url, args.start, args.end, work / "v", args.referer, args.workers
        )
        apl = None
        if args.audio_url:
            apl, audio_src_start, audio_src_end = slice_one(
                args.audio_url, args.start, args.end, work / "a", args.referer, args.workers
            )
        delay = remux(vpl, apl, args.out, src_start, audio_src_start)
        audio_note = args.audio_url

    # File t=0 is the earlier of the two playlist clocks. With a positive
    # audio delay (the Vimeo case) that is the video playlist's first sample.
    timeline_zero = src_start if delay >= 0 else (audio_src_start if audio_src_start is not None else src_start)
    meta = {
        "out": str(args.out),
        "requested_start": args.start,
        "requested_end": args.end,
        "source_start": timeline_zero,
        "video_source_start": src_start,
        "video_source_end": src_end,
        "audio_source_start": audio_src_start,
        "audio_source_end": audio_src_end,
        "audio_delay_sec": delay,
    }
    args.out.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
