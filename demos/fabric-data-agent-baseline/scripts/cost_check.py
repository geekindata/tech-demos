"""Azure cost guard. Prints MTD actual and month-end forecast (NOK). Exit 2 if actual > 120 or forecast > 150.
Usage: cost_check.py [--extra NOK]  (extra = planned spend to add to the forecast, e.g. the run estimate)."""
import json, subprocess, sys, datetime as dt, calendar, time
AZ = '/home/box/tools/azcli/bin/az'
STOP_ACTUAL, STOP_FORECAST = 120.0, 150.0
def az(*a): return subprocess.run([AZ, *a], capture_output=True, text=True, check=True).stdout
def rest(url, body):
    for i in range(4):
        p = subprocess.run([AZ, 'rest', '--method', 'post', '--url', url, '--body', json.dumps(body)], capture_output=True, text=True)
        if p.returncode == 0: return json.loads(p.stdout)
        if '429' in p.stderr or 'Too many' in p.stderr: time.sleep(20 * (i + 1)); continue
        sys.exit('cost query failed: ' + p.stderr.strip()[:300])
    sys.exit('cost query throttled')
sub = az('account', 'show', '--query', 'id', '-o', 'tsv').strip()
base = f'https://management.azure.com/subscriptions/{sub}/providers/Microsoft.CostManagement'
today = dt.date.today(); first = today.replace(day=1); last = today.replace(day=calendar.monthrange(today.year, today.month)[1])
agg = {'totalCost': {'name': 'Cost', 'function': 'Sum'}}
q = rest(f'{base}/query?api-version=2023-11-01', {'type': 'ActualCost', 'timeframe': 'MonthToDate',
         'dataset': {'granularity': 'None', 'aggregation': agg, 'grouping': [{'type': 'Dimension', 'name': 'ServiceName'}]}})
cols = [c['name'] for c in q['properties']['columns']]; rows = q['properties']['rows']
ci, si, cur = cols.index('Cost'), cols.index('ServiceName'), (rows[0][cols.index('Currency')] if rows else 'NOK')
actual = sum(r[ci] for r in rows)
fc_rest = 0.0
if today < last:
    f = rest(f'{base}/forecast?api-version=2023-11-01', {'type': 'ActualCost', 'timeframe': 'Custom',
             'timePeriod': {'from': (today + dt.timedelta(days=1)).isoformat() + 'T00:00:00Z', 'to': last.isoformat() + 'T23:59:59Z'},
             'includeActualCost': False, 'includeFreshPartialCost': False,
             'dataset': {'granularity': 'Daily', 'aggregation': agg}})
    fc_rest = sum(r[0] for r in f['properties']['rows'])
extra = float(sys.argv[sys.argv.index('--extra') + 1]) if '--extra' in sys.argv else 0.0
forecast = actual + fc_rest + extra
for r in sorted(rows, key=lambda r: -r[ci]):
    if r[ci] >= 0.01: print(f'  {r[si]}: {r[ci]:.2f}')
print(f'utc={dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} mtd_actual={actual:.2f} {cur} forecast_rest={fc_rest:.2f} extra={extra:.2f} forecast_month={forecast:.2f}')
if actual > STOP_ACTUAL or forecast > STOP_FORECAST:
    print(f'ABORT: actual > {STOP_ACTUAL} or forecast > {STOP_FORECAST}'); sys.exit(2)
print('OK under guard'); print(f'headroom_to_{STOP_ACTUAL:.0f}={STOP_ACTUAL - actual:.2f}')
