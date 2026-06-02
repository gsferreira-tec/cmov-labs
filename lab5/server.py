from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json, os, re, csv
from urllib.parse import urlparse
BASE = os.path.expanduser('~')
#APP_DIR = os.path.join(BASE, 'output', 'lab5_monitor')
APP_DIR = BASE


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=APP_DIR, **kwargs)

    def do_GET(self):
        p = urlparse(self.path)
        if p.path == '/api/metrics':
            data = collect_metrics()
            body = json.dumps(data).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

def parse_ping_file(path):
    values = []
    summary = {}
    if not os.path.exists(path):
        return {'samples': values, 'summary': summary}
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            m = re.search(r'time=([0-9.]+)\s*ms', line)
            if m:
                values.append(float(m.group(1)))
            s = re.search(r'rtt min/avg/max/mdev = ([0-9.]+)/([0-9.]+)/([0-9.]+)/([0-9.]+)', line)
            if s:
                summary = {'min': float(s.group(1)), 'avg': float(s.group(2)), 'max': float(s.group(3)), 'mdev': float(s.group(4))}
    return {'samples': values, 'summary': summary}

def parse_iperf_csv(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r', errors='ignore') as f:
        reader = csv.reader(f)
        for r in reader:
            if len(r) < 9:
                continue
            try:
                interval = r[6]
                bw_kbps = float(r[8])
                rows.append({'interval': interval, 'kbps': bw_kbps, 'mbps': bw_kbps/1000.0})
            except:
                continue
    return rows

def collect_metrics():
    out = {'throughput': {}, 'rtt': {}, 'present_files': []}
    for name in os.listdir(BASE):
        if re.match(r'(throughput|rtt)_.*\.(csv|txt)$', name):
            out['present_files'].append(name)
    for bw in ['20','100']:
        out['throughput'][bw] = {}
        out['rtt'][bw] = {}
        for ns in ['ue1','ue2']:
            for kind in ['udp_dl','udp_ul','tcp_dl','tcp_ul']:
                fn = os.path.join(BASE, f'throughput_{kind}_{ns}_{bw}.csv')
                out['throughput'][bw][f'{kind}_{ns}'] = parse_iperf_csv(fn)
            for kind in ['ul','dl']:
                fn = os.path.join(BASE, f'rtt_{kind}_{ns}_{bw}.txt')
                out['rtt'][bw][f'{kind}_{ns}'] = parse_ping_file(fn)
    return out

if __name__ == '__main__':
    port = 8000
    print(f'Serving on http://127.0.0.1:{port}')
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
