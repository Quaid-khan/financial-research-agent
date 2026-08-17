"""WSGI Application Adapter for PythonAnywhere & Production Deployments."""
import sys
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ['SEC_EDGAR_USER_AGENT'] = os.environ.get('SEC_EDGAR_USER_AGENT', 'QKResearcher quaidkhan@gmail.com')

STATIC_DIR = PROJECT_ROOT / "web" / "static"

def application(environ, start_response):
    path_info = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    if method == 'GET':
        if path_info in ['/', '/index.html']:
            filepath = STATIC_DIR / 'index.html'
            content_type = 'text/html; charset=utf-8'
        elif path_info == '/styles.css':
            filepath = STATIC_DIR / 'styles.css'
            content_type = 'text/css; charset=utf-8'
        elif path_info == '/app.js':
            filepath = STATIC_DIR / 'app.js'
            content_type = 'application/javascript; charset=utf-8'
        elif path_info in ['/favicon.svg', '/favicon.ico']:
            filepath = STATIC_DIR / 'favicon.svg'
            content_type = 'image/svg+xml'
        elif path_info == '/api/market-ticker':
            try:
                from agent.tools.market_ticker import fetch_market_ticker_data
                data = fetch_market_ticker_data()
            except Exception:
                data = []
            body = json.dumps({"status": "success", "tickers": data}).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(body)))])
            return [body]
        elif path_info == '/api/traces':
            traces = [
                {
                    "trace_id": "trace-1-jpm-primary-10k",
                    "title": "Strict Primary Form 10-K Binding & Lineage (JPMorgan Chase)",
                    "query": "JPM 3-year revenue, net income, assets, liabilities, and CET1 ratio analysis",
                    "highlights": "Validated FY2024 (0000019617-25-000270), FY2023 (0000019617-24-000225), and FY2022 (0000019617-23-000231) statutory filing binding.",
                    "confidence_score": 0.94
                }
            ]
            body = json.dumps({"status": "success", "traces": traces}).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(body)))])
            return [body]
        else:
            filepath = STATIC_DIR / 'index.html'
            content_type = 'text/html; charset=utf-8'

        if filepath.exists():
            body = filepath.read_bytes()
            start_response('200 OK', [('Content-Type', content_type), ('Content-Length', str(len(body)))])
            return [body]

    if method == 'POST' and path_info == '/api/research':
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_body = environ['wsgi.input'].read(content_length).decode('utf-8')
            payload = json.loads(post_body) if post_body else {}
        except Exception:
            payload = {}

        ticker = payload.get('ticker', 'JPM')
        task = payload.get('task', 'Analyze revenue, net income, total assets for last 3 fiscal years.')

        try:
            from web.app import execute_research_pipeline
            report_data, scorecard_data, state_data = execute_research_pipeline(ticker, task)
            res_payload = {
                "status": "success",
                "report": report_data,
                "scorecard": scorecard_data,
                "state": state_data
            }
            body = json.dumps(res_payload).encode('utf-8')
            start_response('200 OK', [('Content-Type', 'application/json'), ('Content-Length', str(len(body)))])
            return [body]
        except Exception as err:
            body = json.dumps({"status": "error", "message": str(err)}).encode('utf-8')
            start_response('500 Internal Server Error', [('Content-Type', 'application/json'), ('Content-Length', str(len(body)))])
            return [body]

    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    return [b'Not Found']
