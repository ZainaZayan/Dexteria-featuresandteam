#!/bin/zsh
# Render the v5.1 film and turn it into website frames (public/dexteria/v51), unattended.
# Passes: every 4th frame, every 2nd, then the rest. Existing frames are skipped.
cd "$(dirname "$0")/.."
B=/Applications/Blender.app/Contents/MacOS/Blender
PY=../v3/.venv/bin/python
echo "$(date +%H:%M:%S) START v5.1" >> logs/final51.log
for spec in "1-266:4" "1-266:2" "1-266"; do
  $B -b film51.blend --python ../v4/scripts/render4.py -- raw51 1920 1080 48 "$spec" skip >> logs/render51.log 2>&1
  $PY scripts/post5.py raw51 anchors51.json v51 >> logs/post51.log 2>&1
  echo "$(date +%H:%M:%S) DONE pass $spec ($(ls raw51 | wc -l | tr -d ' ') frames)" >> logs/final51.log
done
echo "$(date +%H:%M:%S) ALL DONE" >> logs/final51.log
