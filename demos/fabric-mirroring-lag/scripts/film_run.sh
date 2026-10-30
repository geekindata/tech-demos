#!/usr/bin/env bash
# Start one filmable lag run on the Fabric trial: 100 rows/s for RUN_S seconds (default 180),
# same method as the measured runs, results to OneLake Files/mirror_lag/<JOB>/ (default film_<UTC time>).
# Usage: scripts/film_run.sh [RATE] [RUN_S]   then  python3 scripts/ops.py status "$(cat /tmp/film_loc)"
set -euo pipefail
cd "$(dirname "$0")"
source ./env.sh
RATE="${1:-100}"; RUN_S="${2:-180}"; JOB="film_$(date -u +%Y%m%dT%H%M%S)"
PARAMS=$(python3 -c "import json,sys; a=sys.argv; print(json.dumps(dict(src_server=[a[1],'string'],src_db=[a[2],'string'],ep_server=[a[3],'string'],ep_db=['mirror_src_db','string'],job=[a[4],'string'],rates=[a[5],'string'],repeats=[1,'int'],run_s=[int(a[6]),'int'],gap_s=[0,'int'])))" "$SRC_SERVER" "$SRC_DB" "$EP_SERVER" "$JOB" "$RATE" "$RUN_S")
LOC=$(python3 ops.py run mirror_workload "$PARAMS" | tail -n 1)
echo "$LOC" > /tmp/film_loc
echo "job=$JOB location=$LOC"
echo "Notebook session start takes about 1 to 2 minutes before the first rows land; job status may read NotStarted meanwhile."
