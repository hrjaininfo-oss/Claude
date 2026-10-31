#!/usr/bin/env bash
# Mix music + SFX, master to -16 LUFS (two-pass loudnorm), and mux with the rendered picture.
set -euo pipefail
cd "$(dirname "$0")/build"
OUT=${1:-../../claude_intro_pro.mp4}

ffmpeg -y -loglevel error -i music.wav -i sfx.wav -filter_complex \
 "[0]volume=0.5,aecho=0.8:0.45:90|180:0.16|0.08[m];[1]volume=1.0,aecho=0.8:0.5:70|150|260:0.22|0.12|0.06[s];[m][s]amix=inputs=2:normalize=0,highpass=f=28,lowpass=f=17000,acompressor=threshold=0.25:ratio=2.5:attack=8:release=120[a]" \
 -map "[a]" -ar 48000 premaster.wav

STATS=$(ffmpeg -hide_banner -i premaster.wav -af loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json -f null - 2>&1 | sed -n '/{/,/}/p')
get(){ echo "$STATS" | grep "\"$1\"" | sed -E 's/.*: "([^"]+)".*/\1/'; }
ffmpeg -y -loglevel error -i premaster.wav -af "loudnorm=I=-16:TP=-1.5:LRA=9:measured_I=$(get input_i):measured_TP=$(get input_tp):measured_LRA=$(get input_lra):measured_thresh=$(get input_thresh):offset=$(get target_offset):linear=true" -ar 48000 master.wav

ffmpeg -y -loglevel error -f concat -safe 0 -i segs.txt -c copy picture.mp4
ffmpeg -y -loglevel error -i picture.mp4 -i master.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -c:a aac -b:a 256k -t 62.5 -movflags +faststart "$OUT"
echo "Wrote $OUT"
