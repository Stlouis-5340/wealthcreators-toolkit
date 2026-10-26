#!/usr/bin/env bash
# Build the three October 26 reels from the public Vimeo webinar and the
# Dropbox "Money Babies" file. Does not post anywhere.
#
# Needs: ffmpeg, ffprobe, yt-dlp, python3, unzip (via Python's zipfile).
# Usage: ./run.sh
set -euo pipefail
cd "$(dirname "$0")"
export PATH="${HOME}/.local/bin:${PATH}"

command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
command -v yt-dlp >/dev/null
command -v python3 >/dev/null

python3 fetch_sources.py
python3 render_reels.py
echo "Reels are in output/ and, when present, /opt/cursor/artifacts/"
