from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json, os, re, csv, time
from urllib.parse import urlparse

BASE = os.path.expanduser('~')
# index.html is served from here. Keep equal to BASE so the dashboard sits
# in the same folder where running_steps.sh drops the throughput/rtt files.
APP_DIR = BASE

STREAM_INTERVAL = 1.0   # seconds between pushes on /api/stream
ACTIVE_WINDOW   = 3.0   # a file modified within this many seconds is "live"

INTERVAL_RE = re.compile(r'^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$')
TIME_RE     = re.compile(r'time[=<]\s*([0-9.]+)\s*ms', re.IGNORECASE)
SUMMARY_RE  = re.compile(r'min/avg/max/mdev\s*=\s*([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+)')

# Metrics the xApp (xapp_kpm_rc.c) can emit. Kept here so the API only ever
# reports known KPM names; everything else from the CSV is grouped as "other".
KPM_KNOWN = {
    'DRB.UEThpDl', 'DRB.UEThpUl',
    'RRU.PrbTotDl', 'RRU.PrbTotUl',
    'DRB.PdcpSduVolumeDL', 'DRB.PdcpSduVolumeUL',
    'DRB.RlcSduDelayDl',
}


KPM_CSV="/home/mobile/flexric/build/examples/xApp/x/kpm_rc/"

def kpm_csv_path():
    """
    The xApp opens a *relative* "kpm_results.csv" in its working directory,
    which is usually the FlexRIC build dir, not ~. Resolve it like this:
      1. $KPM_CSV if set (recommended),
      2. ~/kpm_results.csv,
      3. ./kpm_results.csv (cwd of this server).
    """

    env = os.environ.get('KPM_CSV')
    if env:
        return os.path.expanduser(env)
    candidates = [os.path.join(BASE, 'kpm_results.csv'),
                  os.path.join(os.getcwd(), 'kpm_results.csv')]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/metrics':
            self._send_json(collect_metrics())
            return
        if path == '/api/stream':
            self._stream()
            return
        return super().do_GET()

    def _send_json(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _stream(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'keep-alive')
        self.end_headers()
        try:
            self.wfile.write(b'retry: 2000\n\n')
            self.wfile.flush()
            while True:
                payload = json.dumps(collect_metrics())
                self.wfile.write(f'data: {payload}\n\n'.encode())
                self.wfile.flush()
                time.sleep(STREAM_INTERVAL)
        except (BrokenPipeError, ConnectionResetError):
            return


# ---------------------------------------------------------------- iperf / rtt
def parse_ping_file(path):
    samples, summary = [], {}
    if not os.path.exists(path):
        return {'samples': samples, 'summary': summary}
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            m = TIME_RE.search(line)
            if m:
                samples.append(float(m.group(1)))
            s = SUMMARY_RE.search(line)
            if s:
                summary = {'min': float(s.group(1)), 'avg': float(s.group(2)),
                           'max': float(s.group(3)), 'mdev': float(s.group(4))}
    if not summary and samples:
        summary = {'min': min(samples), 'avg': sum(samples) / len(samples),
                   'max': max(samples), 'mdev': 0.0, 'live': True}
    return {'samples': samples, 'summary': summary}


def parse_iperf_csv(path):
    """Column 8 is bandwidth in BITS/sec -> Mbps = value / 1e6."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r', errors='ignore') as f:
        for r in csv.reader(f):
            if len(r) < 9:
                continue
            m = INTERVAL_RE.match(r[6].strip())
            if not m:
                continue
            try:
                start = float(m.group(1)); end = float(m.group(2)); bps = float(r[8])
            except ValueError:
                continue
            rows.append({'interval': r[6].strip(), 't_start': start, 't_end': end,
                         'kbps': bps / 1e3, 'mbps': bps / 1e6,
                         'summary': (end - start) > 1.5})
    return rows


# ----------------------------------------------------------------- xApp KPM
def parse_kpm_csv(path):
    """
    Parse kpm_results.csv written by xapp_kpm_rc.c.
    Format: ts_now_us, collect_start_us, latency_us, metric, value
    Returns time series per metric, with x = seconds since the first sample.
    """
    metrics = {}
    other = {}
    first_ts = None
    last_latency = None
    if not os.path.exists(path):
        return {'present': False, 'metrics': metrics, 'other_metrics': other, 'path': path}

    with open(path, 'r', errors='ignore') as f:
        for line in f:
            parts = line.rstrip('\n').split(',')
            if len(parts) < 5:
                continue
            try:
                ts = float(parts[0])
                val = float(parts[4])
            except ValueError:
                continue  # header row or junk
            metric = parts[3].strip()
            if first_ts is None:
                first_ts = ts
            try:
                last_latency = float(parts[2])
            except ValueError:
                pass
            point = {'t': (ts - first_ts) / 1e6, 'y': val}
            bucket = metrics if metric in KPM_KNOWN else other
            bucket.setdefault(metric, []).append(point)

    return {'present': bool(metrics or other),
            'metrics': metrics,
            'other_metrics': other,
            'first_ts_us': first_ts,
            'last_latency_us': last_latency,
            'path': path}


# ----------------------------------------------------------------- aggregate
def collect_metrics():
    now = time.time()
    out = {'throughput': {}, 'rtt': {}, 'present_files': [],
           'active_files': [], 'server_time': now}

    for name in sorted(os.listdir(BASE)):
        if re.match(r'(throughput|rtt)_.*\.(csv|txt)$', name):
            out['present_files'].append(name)
            try:
                if now - os.path.getmtime(os.path.join(BASE, name)) <= ACTIVE_WINDOW:
                    out['active_files'].append(name)
            except OSError:
                pass

    for bw in ['20', '100']:
        out['throughput'][bw] = {}
        out['rtt'][bw] = {}
        for ns in ['ue1', 'ue2']:
            for kind in ['udp_dl', 'udp_ul', 'tcp_dl', 'tcp_ul']:
                fn = os.path.join(BASE, f'throughput_{kind}_{ns}_{bw}.csv')
                out['throughput'][bw][f'{kind}_{ns}'] = parse_iperf_csv(fn)
            for kind in ['ul', 'dl']:
                fn = os.path.join(BASE, f'rtt_{kind}_{ns}_{bw}.txt')
                out['rtt'][bw][f'{kind}_{ns}'] = parse_ping_file(fn)

    # xApp KPM stream
    kpm_path = kpm_csv_path()
    kpm = parse_kpm_csv(kpm_path)
    try:
        kpm['active'] = os.path.exists(kpm_path) and (now - os.path.getmtime(kpm_path)) <= ACTIVE_WINDOW
    except OSError:
        kpm['active'] = False
    out['kpm'] = kpm
    return out


if __name__ == '__main__':
    port = 8000
    print(f'Serving on http://127.0.0.1:{port}  (live stream at /api/stream)')
    print(f'Reading KPM from: {kpm_csv_path()}   (override with KPM_CSV=/path/to/kpm_results.csv)')
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
