#!/usr/bin/env bash
#
# sweep_taps.sh -- walks bpm.py through a BPM range, waiting briefly
# between each step before sending the next tempo.
#
# Usage:
#   ./sweep_taps.sh                       # 40 to 250 BPM, step 4 (default)
#   ./sweep_taps.sh 40 250 4              # same, explicit
#   ./sweep_taps.sh 60 180 2 --taps 6     # custom range + step, 6 taps/step
#
# Any extra args after the first three are passed straight through to
# bpm.py (e.g. --taps, --gpio-tap, --pulse-ms).

set -euo pipefail

START="${1:-40}"
STOP="${2:-250}"
STEP="${3:-4}"
shift $(( $# >= 3 ? 3 : $# )) || true
EXTRA_ARGS=("$@")

DELAY="${SWEEP_DELAY:-1}"   # seconds to wait between steps; override with SWEEP_DELAY=2 ./sweep_taps.sh ...

TOTAL=$(( (STOP - START) / STEP + 1 ))
LAST=$(( START + (TOTAL - 1) * STEP ))

echo "Sweeping ${START} to ${STOP} BPM in steps of ${STEP} (${TOTAL} steps, ${DELAY}s apart)."
if [ "$LAST" -ne "$STOP" ]; then
    echo "Note: step size doesn't divide evenly -- last step will be ${LAST} BPM, not ${STOP}."
fi
echo "Ctrl+C to bail out."
echo

STEP_NUM=0
for (( bpm=START; bpm<=STOP; bpm+=STEP )); do
    STEP_NUM=$(( STEP_NUM + 1 ))
    echo "[${STEP_NUM}/${TOTAL}] ${bpm} BPM"
    python3 bpm.py "$bpm" "${EXTRA_ARGS[@]}"
    sleep "$DELAY"
done

echo "Sweep complete: ${TOTAL} tempos sent."
