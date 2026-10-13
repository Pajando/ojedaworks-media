#!/bin/bash
# Text BEHIND the person (house style). Layers: video -> behind.png -> person cutout -> front.png (optional)
# usage: depth_text.sh in.mp4 behind.png out.mp4 [front.png]
# PNGs: 1080x1920 transparent (render HTML with headless Chrome, --default-background-color=00000000)
set -e
export PATH=/opt/homebrew/bin:$PATH
IN="$1"; BEH="$2"; OUT="$3"; FRONT="$4"
SEG="$HOME/Library/Application Support/ojedaworks/motion/behind/seg"
W=$(mktemp -d); mkdir "$W/f" "$W/m"
ffmpeg -v error -i "$IN" -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30" "$W/f/%05d.png"
"$SEG" "$W/f" "$W/m" >/dev/null
FC="[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=rgba[v];[2:v]format=gray,scale=1080:1920[mk];[v]split[v1][v2];[v2][mk]alphamerge[p];[v1][1:v]overlay=0:0[b];[b][p]overlay=0:0"
if [ -n "$FRONT" ]; then
  ffmpeg -v error -y -i "$IN" -loop 1 -i "$BEH" -framerate 30 -i "$W/m/%05d.png" -loop 1 -i "$FRONT" -filter_complex "$FC[c];[c][3:v]overlay=0:0,format=yuv420p[o]" -map "[o]" -map 0:a? -shortest -c:v libx264 -crf 18 -c:a aac "$OUT"
else
  ffmpeg -v error -y -i "$IN" -loop 1 -i "$BEH" -framerate 30 -i "$W/m/%05d.png" -filter_complex "$FC,format=yuv420p[o]" -map "[o]" -map 0:a? -shortest -c:v libx264 -crf 18 -c:a aac "$OUT"
fi
rm -rf "$W"; echo "done $OUT"
