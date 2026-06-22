#!/usr/bin/env python3
"""
Local proxy + static server for chatbox.html and the Chrome extension.
  GET  /              → serves chatbox.html
  GET  /config        → returns Bifrost URL + key as JSON
  GET  /search?q=...  → proxies SearXNG search (CORS bypass for the extension)
  POST /proxy/v1/*    → proxies to Bifrost upstream
  POST /codesec       → runs lacework SCA+SAST on submitted code snippet
  POST /sbom          → runs lacework SCA and returns CycloneDX SBOM JSON

Usage: python3 serve.py
       open http://localhost:8765

SEARXNG_URL in .env overrides the default (http://localhost:8080).
The extension tries Docker SearXNG first; falls back here if Docker is not running.
"""
import http.server, json, os, shutil, socketserver, subprocess, tempfile, urllib.parse, urllib.request, urllib.error

PORT      = 8765
DIR       = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(DIR, 'chatbox.html')

def load_env():
    path = os.path.join(DIR, '.env')
    env = {}
    if not os.path.exists(path):
        return env
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                env[k.strip()] = v.strip()
    return env

env         = load_env()
VIRTUAL_KEY = env.get('BIFROST_VIRTUAL_KEY', '')
SEARXNG_URL = env.get('SEARXNG_URL', 'http://localhost:8080')
UPSTREAM    = env.get('ANTHROPIC_BASE_URL', 'https://your-bifrost-endpoint/anthropic')

CORS = {
    'Access-Control-Allow-Origin':  '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, x-api-key, anthropic-version',
}


class Handler(http.server.BaseHTTPRequestHandler):

    # ── helpers ───────────────────────────────────────────────────────────

    def send_pdf(self, body: bytes, filename: str):
        self.send_response(200)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.send_header('Content-Type', 'application/pdf')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, body: bytes):
        self.send_response(status)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ── routing ───────────────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        if self.path in ('/', '/chatbox.html'):
            self.serve_html()
        elif self.path == '/config':
            self.serve_config()
        elif self.path.startswith('/search'):
            self.serve_search()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/codesec':
            self.serve_codesec()
        elif self.path == '/sbom':
            self.serve_sbom()
        elif self.path == '/compliance':
            self.serve_compliance()
        elif self.path.startswith('/proxy/'):
            self.proxy_upstream()
        else:
            self.send_error(404)

    # ── handlers ──────────────────────────────────────────────────────────

    def serve_html(self):
        with open(HTML_FILE, 'rb') as f:
            html = f.read().decode()
        if VIRTUAL_KEY:
            html = html.replace(
                'placeholder="Virtual key (x-bf-vk)…" autocomplete="off"',
                f'placeholder="Virtual key…" autocomplete="off" value="{VIRTUAL_KEY}"',
            )
        body = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_config(self):
        body = json.dumps({
            'bifrost_url': env.get('ANTHROPIC_BASE_URL', ''),
            'api_key':     VIRTUAL_KEY,
        }).encode()
        self.send_json(200, body)

    def serve_search(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        query  = params.get('q', [''])[0]
        if not query:
            self.send_error(400, 'Missing q parameter')
            return
        url = f"{SEARXNG_URL}/search?q={urllib.parse.quote(query)}&format=json&language=en"
        try:
            req  = urllib.request.Request(url, headers={'User-Agent': 'BifrostChat/1.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            self.send_json(200, resp.read())
        except urllib.error.HTTPError as e:
            self.send_error(e.code, str(e))

    def proxy_upstream(self):
        url    = UPSTREAM + self.path[len('/proxy'):]
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length)
        req    = urllib.request.Request(url, data=body, method='POST', headers={
            'content-type':      self.headers.get('content-type', 'application/json'),
            'anthropic-version': self.headers.get('anthropic-version', '2023-06-01'),
            'x-api-key':         VIRTUAL_KEY,
        })
        try:
            resp = urllib.request.urlopen(req, timeout=120)
            self.send_response(resp.status)
            for k, v in CORS.items():
                self.send_header(k, v)
            for h in ('content-type', 'x-request-id'):
                if val := resp.headers.get(h):
                    self.send_header(h, val)
            self.end_headers()
            while chunk := resp.read(4096):
                self.wfile.write(chunk)
                self.wfile.flush()
        except urllib.error.HTTPError as e:
            self.send_json(e.code, e.read())

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(length)

    def _write_files(self, tmpdir, payload):
        """Write files array [{filename, code}] or legacy {filename, code} to tmpdir."""
        files = payload.get('files')
        if files:
            for entry in files:
                name = os.path.basename(entry.get('filename', 'snippet.txt'))
                path = os.path.join(tmpdir, name)
                with open(path, 'w') as f:
                    f.write(entry.get('code', ''))
        else:
            name = os.path.basename(payload.get('filename', 'snippet.txt'))
            with open(os.path.join(tmpdir, name), 'w') as f:
                f.write(payload.get('code', ''))

    def serve_codesec(self):
        """Accept JSON {files:[{filename,code}]}, run lacework SCA+SAST, return findings."""
        if not shutil.which('lacework'):
            self.send_json(503, json.dumps({'error': 'lacework CLI not found'}).encode())
            return
        try:
            payload = json.loads(self._read_body())
        except json.JSONDecodeError:
            self.send_error(400, 'Expected JSON {files:[{filename,code}]}')
            return

        tmpdir = tempfile.mkdtemp(prefix='bifrost-codesec-')
        try:
            self._write_files(tmpdir, payload)
            filename = 'scan'  # used only for error display

            out_json = os.path.join(tmpdir, 'sca.json')
            result   = subprocess.run(
                ['lacework', 'sca', 'scan', tmpdir,
                 '--deployment=offprem', '--noninteractive',
                 '--save-results=false', '-f', 'lw-json', '-o', out_json],
                capture_output=True, text=True, timeout=120,
            )

            findings, weaknesses, secrets = [], [], []
            if os.path.exists(out_json):
                with open(out_json) as f:
                    data = json.load(f)

                # Build artifact id → name map
                art_map = {a['Id']: a.get('Name', a.get('Path', ''))
                           for a in data.get('Artifacts', [])}

                # SCA vulnerabilities — top-level Vulnerabilities[]
                for vuln in data.get('Vulnerabilities', []):
                    info = vuln.get('Info', {})
                    aid  = (vuln.get('AffectedArtifactIds') or [''])[0]
                    fv = info.get('FixVersion') or {}
                    findings.append({
                        'type':        'vuln',
                        'id':          info.get('ExternalId', ''),
                        'severity':    info.get('Severity', ''),
                        'package':     art_map.get(aid, aid),
                        'fixVersion':  fv.get('Version', '') if isinstance(fv, dict) else str(fv),
                        'description': info.get('Description', ''),
                    })

                # SAST / secrets — top-level Weaknesses[]
                for w in data.get('Weaknesses', []):
                    for inst in w.get('Instances', []):
                        loc = (inst.get('LocationDetails') or [{}])[0]
                        ll  = loc.get('LineLocation', {})
                        cat = w.get('Info', {}).get('Category', '')
                        entry = {
                            'type':        'secret' if cat == 'Secret' else 'sast',
                            'id':          w.get('Info', {}).get('ExternalId', ''),
                            'severity':    inst.get('Severity', ''),
                            'title':       w.get('Info', {}).get('Name', ''),
                            'description': w.get('Info', {}).get('ShortDescription', ''),
                            'file':        ll.get('RelativePath', ''),
                            'line':        ll.get('Start', 0),
                            'fix':         w.get('Info', {}).get('RemediationRecommendation', ''),
                        }
                        if cat == 'Secret':
                            secrets.append(entry)
                        else:
                            weaknesses.append(entry)

            body = json.dumps({
                'filename':   filename,
                'vulns':      findings,
                'weaknesses': weaknesses,
                'secrets':    secrets,
                'stderr':     result.stderr[-2000:] if result.returncode not in (0, 1) else '',
            }).encode()
            self.send_json(200, body)
        except subprocess.TimeoutExpired:
            self.send_json(504, json.dumps({'error': 'scan timed out'}).encode())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def serve_sbom(self):
        """Accept JSON {files:[{filename,code}]}, return CycloneDX SBOM from lacework SCA."""
        if not shutil.which('lacework'):
            self.send_json(503, json.dumps({'error': 'lacework CLI not found'}).encode())
            return
        try:
            payload = json.loads(self._read_body())
        except json.JSONDecodeError:
            self.send_error(400, 'Expected JSON {files:[{filename,code}]}')
            return

        tmpdir = tempfile.mkdtemp(prefix='bifrost-sbom-')
        try:
            self._write_files(tmpdir, payload)

            out_json = os.path.join(tmpdir, 'sbom.json')
            result   = subprocess.run(
                ['lacework', 'sca', 'scan', tmpdir,
                 '--deployment=offprem', '--noninteractive',
                 '--save-results=false', '-f', 'cyclonedx-json', '-o', out_json],
                capture_output=True, text=True, timeout=120,
            )

            if os.path.exists(out_json):
                with open(out_json) as f:
                    sbom = json.load(f)
                self.send_json(200, json.dumps(sbom).encode())
            else:
                self.send_json(200, json.dumps({
                    'error':  'no SBOM generated — no packages detected in snippet',
                    'stderr': result.stderr[-2000:],
                }).encode())
        except subprocess.TimeoutExpired:
            self.send_json(504, json.dumps({'error': 'scan timed out'}).encode())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    # Maps framework short IDs → exact --report_name strings the lacework CLI accepts
    COMPLIANCE_REPORT_NAMES = {
        # AWS
        'AWS_CIS_14':       'CIS Amazon Web Services Foundations Benchmark v1.4.0',
        'AWS_CIS_12':       'CIS Amazon Web Services Foundations Benchmark v1.2.0',
        'AWS_NIST_CSF':     'AWS NIST CSF',
        'AWS_NIST_80053':   'AWS NIST 800-53 rev5',
        'AWS_NIST_800171':  'AWS NIST 800-171 rev2',
        'AWS_PCI_321':      'AWS PCI DSS 3.2.1',
        'AWS_PCI_40':       'AWS PCI DSS 4.0.0',
        'AWS_SOC2':         'AWS SOC 2 Report Rev2',
        'AWS_HIPAA':        'AWS HIPAA Report',
        'AWS_ISO27001':     'AWS ISO 27001:2013 Report',
        # Azure
        'AZURE_CIS_131':    'Azure CIS 1.3.1 Report',
        'AZURE_CIS_15':     'CIS Microsoft Azure',
        'AZURE_NIST_CSF':   'Azure NIST CSF Report',
        'AZURE_NIST_80053': 'Azure NIST 800-53 Rev5 Report',
        'AZURE_NIST_800171':'Azure NIST 800-171 Rev2 Report',
        'AZURE_PCI_321':    'Azure PCI DSS 3.2.1 CIS 1.5',
        'AZURE_PCI_40':     'Azure PCI DSS 4.0.0 CIS 1.5',
        'AZURE_SOC2':       'Azure SOC 2 Report Rev2',
        'AZURE_HIPAA':      'Azure HIPAA Report',
        'AZURE_ISO27001':   'Azure ISO 27001 Report',
        # GCP
        'GCP_CIS_13':       'GCP CIS Benchmark 1.3',
        'GCP_CIS_12':       'GCP CIS Benchmark 1.2',
        'GCP_NIST_CSF':     'GCP NIST CSF Report',
        'GCP_NIST_80053':   'GCP NIST 800-53 rev5',
        'GCP_NIST_800171':  'GCP NIST 800 171 REV2 Report',
        'GCP_PCI_321':      'GCP PCI DSS 3.2.1',
        'GCP_PCI_40':       'GCP PCI DSS 4.0.0',
        'GCP_SOC2':         'GCP SOC 2 Report Rev2',
        'GCP_HIPAA':        'GCP HIPAA Report Rev2',
        'GCP_ISO27001':     'GCP ISO 27001 Report',
    }

    def serve_compliance(self):
        """Accept JSON {cloud, framework, accountId}, run lacework compliance get-report --pdf."""
        if not shutil.which('lacework'):
            self.send_json(503, json.dumps({'error': 'lacework CLI not found'}).encode())
            return
        try:
            payload = json.loads(self._read_body())
        except json.JSONDecodeError:
            self.send_error(400, 'Expected JSON {cloud, framework, accountId}')
            return

        cloud      = payload.get('cloud', '').lower()
        framework  = payload.get('framework', '').strip()
        account_id = payload.get('accountId', '').strip()

        cloud_cmd_map = {'aws': 'aws', 'azure': 'azure', 'gcp': 'google'}
        if cloud not in cloud_cmd_map:
            self.send_json(400, json.dumps({'error': f'Unknown cloud: {cloud}'}).encode())
            return

        report_name = self.COMPLIANCE_REPORT_NAMES.get(framework)
        if not report_name:
            self.send_json(400, json.dumps({'error': f'Unknown framework: {framework}'}).encode())
            return

        tmpdir = tempfile.mkdtemp(prefix='bifrost-compliance-')
        try:
            # lacework writes the PDF to cwd with an auto-generated filename
            cmd = ['lacework', 'compliance', cloud_cmd_map[cloud], 'get-report']
            if account_id:
                cmd.append(account_id)
            cmd += ['--pdf', f'--report_name={report_name}', '--noninteractive']

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=tmpdir)

            # Find the generated PDF in tmpdir
            import glob as _glob
            pdfs = _glob.glob(os.path.join(tmpdir, '*.pdf'))
            if pdfs:
                with open(pdfs[0], 'rb') as f:
                    pdf_bytes = f.read()
                safe_fw = framework.replace('/', '-')
                self.send_pdf(pdf_bytes, f'compliance-{cloud}-{safe_fw}.pdf')
            else:
                stderr = (result.stdout + result.stderr)[-2000:]
                self.send_json(500, json.dumps({
                    'error': 'No PDF generated — check lacework credentials or account ID',
                    'stderr': stderr,
                }).encode())
        except subprocess.TimeoutExpired:
            self.send_json(504, json.dumps({'error': 'compliance report timed out'}).encode())
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def log_message(self, fmt, *args):
        print(f'  {self.address_string()} {fmt % args}')


LW_AVAILABLE = shutil.which('lacework') is not None

print(f'Bifrost chatbox  →  http://localhost:{PORT}')
print(f'Virtual key      →  {"loaded (" + VIRTUAL_KEY[:12] + "…)" if VIRTUAL_KEY else "MISSING — edit .env"}')
print(f'Proxy route      →  /proxy/v1/* → {UPSTREAM.rstrip("/")}/v1/*')
print(f'Search proxy     →  /search?q=... → {SEARXNG_URL}')
print(f'CodeSec scan     →  POST /codesec     {"(lacework CLI ready)" if LW_AVAILABLE else "(WARNING: lacework CLI not found)"}')
print(f'SBOM export      →  POST /sbom        {"(lacework CLI ready)" if LW_AVAILABLE else "(WARNING: lacework CLI not found)"}')
print(f'Compliance PDF   →  POST /compliance  {"(lacework CLI ready)" if LW_AVAILABLE else "(WARNING: lacework CLI not found)"}')

with socketserver.TCPServer(('', PORT), Handler) as httpd:
    httpd.serve_forever()
