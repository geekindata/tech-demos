#!/usr/bin/env bash
# F2 window controls for the data agent baseline. Approved: ONE window, moved by Sai to Fri 2026-10-30 evening (t139u), max 2 h, then pause.
# Usage: f2.sh state | resume | to_f2 | back | hardstop_arm | hardstop_status | minutes
# resume refuses unless DATE is 2026-10-30 (Oslo) and F2_WINDOW_OK=2026-10-30 is exported.
set -uo pipefail
A=/home/box/tools/azcli/bin/az
D=$(cd "$(dirname "$0")/.." && pwd)
S=$D/scripts
F2_ARM=${F2_ARM:?set F2_ARM to the F2 capacity ARM resource path}
WS=${AGENT_WS_ID:-$(cat $D/scripts/agent_ws_id)}
LOG=$D/results/f2_window_log.csv
HARD_MIN=${HARD_MIN:-115}   # hard stop fires 115 min after resume, so Paused well before 120
now(){ date -u +%Y-%m-%dT%H:%M:%SZ; }
log(){ [ -f $LOG ] || echo "utc,event,detail" > $LOG; echo "$(now),$1,$2" >> $LOG; echo "$(now) $1 $2"; }
cap_id(){ python3 -c "import sys;sys.path.insert(0,'$S');import fab;print([c['id'] for c in fab.call('GET','/capacities')[1]['value'] if c['displayName']==sys.argv[1] or c['sku']==sys.argv[1]][0])" "$1"; }
state(){ $A rest --method get --url "https://management.azure.com${F2_ARM}?api-version=2023-11-01" --query properties.state -o tsv; }
ws_cap(){ python3 -c "import sys;sys.path.insert(0,'$S');import fab;print(fab.call('GET','/workspaces/'+sys.argv[1])[1].get('capacityId'))" "$WS"; }
assign(){ python3 -c "import sys;sys.path.insert(0,'$S');import fab;s,j,_=fab.call('POST','/workspaces/'+sys.argv[1]+'/assignToCapacity',{'capacityId':sys.argv[2]});print(s, '' if s<300 else j)" "$WS" "$1"; }
suspend(){ for i in 1 2 3; do
    $A rest --method post --url "https://management.azure.com${F2_ARM}/suspend?api-version=2023-11-01" >/dev/null 2>&1
    for j in $(seq 1 12); do s=$(state); [ "$s" = "Paused" ] && { log suspended "state=Paused"; return 0; }; sleep 10; done
  done; log suspend_FAILED "state=$(state)"; return 1; }
case "${1:-state}" in
  state) echo "F2=$(state) agent_ws_capacity=$(ws_cap)";;
  resume)
    [ "$(TZ=Europe/Oslo date +%F)" = "2026-10-30" ] && [ "${F2_WINDOW_OK:-}" = "2026-10-30" ] || { echo "REFUSED: resume only on 2026-10-30 with F2_WINDOW_OK=2026-10-30"; exit 3; }
    [ -f $D/results/.resumed_once ] && { echo "REFUSED: window already used ($(cat $D/results/.resumed_once))"; exit 3; }
    $A rest --method post --url "https://management.azure.com${F2_ARM}/resume?api-version=2023-11-01" >/dev/null || { log resume_FAILED ""; exit 1; }
    now > $D/results/.resumed_once
    for j in $(seq 1 18); do s=$(state); [ "$s" = "Active" ] && break; sleep 10; done
    log resumed "state=$s"; "$0" hardstop_arm;;
  hardstop_arm)
    nohup bash -c "sleep $((HARD_MIN*60)); '$0' back hardstop" > $D/results/hardstop.out 2>&1 &
    echo $! > $D/results/hardstop.pid; log hardstop_armed "pid=$! fires_in_min=$HARD_MIN";;
  hardstop_status) p=$(cat $D/results/hardstop.pid 2>/dev/null); ps -p "$p" >/dev/null 2>&1 && echo "armed pid=$p" || echo "not running";;
  to_f2) F2=$(cap_id "${F2_NAME:?set F2_NAME to the F2 capacity name}"); log assign_f2 "$(assign $F2)"; echo "ws capacity now $(ws_cap)";;
  back)
    TR=$(cap_id FTL64); log assign_trial "$(assign $TR) via=${2:-manual}"
    suspend; s=$(state); echo "F2=$s agent_ws_capacity=$(ws_cap)"
    [ "${2:-}" != hardstop ] && { p=$(cat $D/results/hardstop.pid 2>/dev/null); [ -n "$p" ] && kill "$p" 2>/dev/null && log hardstop_disarmed "pid=$p"; }
    "$0" minutes;;
  minutes) python3 - "$LOG" <<'PY'
import csv, sys, datetime as dt
r = list(csv.DictReader(open(sys.argv[1]))); p = lambda s: dt.datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
a = [p(x['utc']) for x in r if x['event'] == 'resumed']; b = [p(x['utc']) for x in r if x['event'] == 'suspended']
if a and b and b[-1] > a[0]: m = (b[-1] - a[0]).total_seconds() / 60; print(f'F2 minutes: {m:.1f} (uptime cost ~kr{m/60*3.618:.2f})')
else: print('F2 minutes: window not closed yet')
PY
  ;;
  *) echo "usage: $0 state|resume|to_f2|back|hardstop_arm|hardstop_status|minutes"; exit 1;;
esac
