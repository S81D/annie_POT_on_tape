#!/usr/bin/env bash
set -euo pipefail

START_FULL="2025-10-04 17:39:53.092566"
END_FULL="2026-02-20 16:22:27.881063"

# --- next midnight after a timestamp ---
next_midnight() {
    date -d "$(date -d "$1" +%F) +1 day" +"%Y-%m-%d 00:00:00.000000"
}

CURRENT_START="$START_FULL"
FINAL_END="$END_FULL"

while true; do

    # candidate end = next midnight
    CANDIDATE_END=$(next_midnight "$CURRENT_START")

    # clamp to final end
    if [[ $(date -d "$CANDIDATE_END" +%s) -gt $(date -d "$FINAL_END" +%s) ]]; then
        CURRENT_END="$FINAL_END"
        DONE=true
    else
        CURRENT_END="$CANDIDATE_END"
        DONE=false
    fi

    echo "Running: $CURRENT_START -> $CURRENT_END"

# --- run query ---
OUTPUT=$(python3 querybnb_ind.py "$CURRENT_START" "$CURRENT_END" 2>&1)

echo "$OUTPUT"

# --- POT extraction ---
POT=$(echo "$OUTPUT" | grep -Eo '[0-9]+\.[0-9]+' | tail -1)

if [[ -z "$POT" ]]; then
    POT="NaN"
fi

if [[ "$DONE" == true ]]; then
    break
fi

CURRENT_START="$CURRENT_END"
done

echo ""
echo "done"
echo ""
