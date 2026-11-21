#!/usr/bin/env python3
"""Local UI preview server for FinZ SEO Workbench (NOT the product backend).

Binds 127.0.0.1 and persists raw uploads/evidence in local SQLite storage.
Requires openpyxl for XLSX. Optional AI runs only with an explicitly configured provider.
"""
import csv
import hashlib
import uuid
import sqlite3
import io
import json
import os
import pathlib
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit, parse_qs
from topic_source_import import parse_topic_source
import persistent_store as store
from evidence_engine import read_export, normalize_rows, infer_research_gaps
from ai_demand_engine import provider_config, analyze_topic, assess_evidence

MAX_FILE = 5 * 1024 * 1024
MAX_ROW_SCAN = 25000
MAX_PREVIEW = 200
ROOT = pathlib.Path(__file__).resolve().parent
# Env file stays outside the HTTP static root and is gitignored.
def load_env_local():
    path = ROOT.parent / '.env.local'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line: continue
            key, value = line.split('=', 1)
            if re.fullmatch(r'[A-Z_][A-Z0-9_]*', key.strip()):
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
load_env_local()


def parse_csv(payload):
    warnings = []
    text = None
    for enc in ('utf-8-sig', 'utf-16', 'cp1258', 'cp1252'):
        try:
            text = payload.decode(enc)
            if enc != 'utf-8-sig':
                warnings.append(f'Decoded with {enc}; check Vietnamese text and header names.')
            break
        except UnicodeError:
            continue
    if text is None:
        raise ValueError('CSV encoding could not be decoded.')
    text = text.replace('\ufeff', '')
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        reader = csv.reader(io.StringIO(text), dialect)
    except csv.Error:
        reader = csv.reader(io.StringIO(text), delimiter=',')
    rows = []
    for i, row in enumerate(reader):
        if i >= MAX_ROW_SCAN:
            warnings.append(f'Only the first {MAX_ROW_SCAN} rows were scanned in the prototype.')
            break
        if row and any(str(x).strip() for x in row):
            rows.append(row)
    if not rows:
        raise ValueError('No CSV data found.')
    headers = [str(x).strip() for x in rows[0]]
    return rows_to_result(headers, rows[1:], 'CSV', warnings)


def parse_xlsx(payload):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError('Missing openpyxl. Run: python -m pip install openpyxl') from exc
    if not payload.startswith(b'PK'):
        raise ValueError('XLSX does not appear to be a valid ZIP-based workbook.')
    try:
        book = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError('Cannot read XLSX: invalid or unsupported workbook.') from exc
    sheet = book.active
    sheet.reset_dimensions()
    rows = []
    truncated = False
    for i, row in enumerate(sheet.iter_rows(values_only=True)):
        if i >= MAX_ROW_SCAN:
            truncated = True
            break
        if row and any(x is not None and str(x).strip() for x in row):
            rows.append(['' if x is None else str(x) for x in row])
    book.close()
    if not rows:
        raise ValueError('Active worksheet does not contain data.')
    warnings = ['Using the active XLSX worksheet. Production must provide a sheet picker.']
    if truncated:
        warnings.append(f'Only the first {MAX_ROW_SCAN} rows were scanned in the prototype.')
    headers = [str(x).strip() for x in rows[0]]
    return rows_to_result(headers, rows[1:], sheet.title, warnings)


def rows_to_result(headers, rows, sheet_name, warnings):
    if not headers or not any(headers):
        raise ValueError('Missing header row.')
    if len(set(headers)) != len(headers):
        warnings.append('Duplicate header names found; confirm column mapping manually.')
    objs = []
    for row in rows[:MAX_PREVIEW]:
        objs.append({headers[i] or f'Column {i+1}': str(row[i]) if i < len(row) else '' for i in range(len(headers))})
    if len(rows) > MAX_PREVIEW:
        warnings.append(f'Prototype only retains {MAX_PREVIEW} sample rows for the UI.')
    return dict(headers=headers, rows=objs, totalRows=len(rows), sheetUsed=sheet_name, warnings=warnings)


def error_feedback(route, exc):
    code = ('DB_SAVE_FAILED' if route == '/api/projects/save' or isinstance(exc, sqlite3.Error)
            else 'COLUMN_MAPPING_INVALID' if route == '/api/import-confirm'
            else 'AI_NOT_CONFIGURED' if route.startswith('/api/ai/') and not provider_config()['ready']
            else 'LLM_REQUEST_FAILED' if route.startswith('/api/ai/') else 'UNSUPPORTED_FILE')
    return {'code': code, 'severity': 'ERROR', 'title': 'Thao tác chưa hoàn tất',
            'reason': str(exc) if isinstance(exc, ValueError) else 'Server chưa xác nhận kết quả.',
            'impact': 'Không thể chuyển bước hoặc xác nhận chất lượng từ thao tác này.',
            'solution': 'Kiểm tra trường dữ liệu và thử lại tác vụ.',
            'next_action': {'label': 'Thử lại', 'target': 'setup' if code == 'DB_SAVE_FAILED' else 'upload'},
            'blocking': True, 'source_ref': None}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print('[local] ' + fmt % args)

    def respond(self, status, data):
        blob = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(blob)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(blob)

    def json_body(self, limit=3_000_000):
        length = int(self.headers.get('Content-Length', '0'))
        if not (0 < length <= limit):
            raise ValueError('JSON request vượt giới hạn cho phép.')
        val = json.loads(self.rfile.read(length))
        if not isinstance(val, dict):
            raise ValueError('Body phải là một JSON object.')
        return val

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/health':
            c = provider_config()
            return self.respond(200, {'ok': True, 'mode': 'LOCAL_WORKBENCH_V1_5', 'database': 'sqlite',
                                      'semrush_api': False, 'mcp': False,
                                      'ai_provider': c['provider'], 'ai_ready': c['ready']})
        if path == '/api/projects/list':
            return self.respond(200, {'projects': store.list_projects()})
        if path.startswith('/api/projects/'): 
            project_id = unquote(path.split('/api/projects/', 1)[1])
            state = store.load_project(project_id)
            return self.respond(200, {'state': state}) if state else self.respond(404, {'error':'Không thấy dự án trong DB.'})
        if path == '/api/ai/status':
            cfg = provider_config()
            return self.respond(200, {'configured': cfg['ready'], 'provider':cfg['provider'], 'model':cfg['model']})
        if path == '/api/research/evidence':
            q = parse_qs(urlsplit(self.path).query)
            project_id=(q.get('projectId') or [''])[0]
            if not project_id: return self.respond(400, {'error':'Thiếu projectId'})
            return self.respond(200, store.load_evidence(project_id))
        return super().do_GET()

    def do_POST(self):
        route = urlsplit(self.path).path
        try:
            if route in ('/api/import-preview', '/api/topic-source-preview'):
                length = int(self.headers.get('Content-Length', '0'))
                if length < 1 or length > MAX_FILE:
                    return self.respond(413, {'error': 'File phải từ 1 byte đến 5 MB.', 'feedback': error_feedback(route, ValueError('Chọn file từ 1 byte đến 5 MB.'))})
                fname = os.path.basename(unquote(self.headers.get('X-File-Name', 'unknown')))
                ext = pathlib.Path(fname).suffix.lower()
                if ext not in ('.csv', '.xlsx'):
                    return self.respond(415, {'error': 'Chỉ hỗ trợ CSV hoặc XLSX.', 'feedback': error_feedback(route, ValueError('Chọn file CSV/XLSX.'))})
                payload = self.rfile.read(length)
                result = (parse_topic_source(payload, fname) if route == '/api/topic-source-preview'
                          else (parse_csv(payload) if ext == '.csv' else parse_xlsx(payload)))
                if route == '/api/import-preview':
                    store.DATABASE_DIR.mkdir(parents=True, exist_ok=True)
                    uploads = store.DATABASE_DIR / 'uploads'
                    uploads.mkdir(exist_ok=True)
                    filepath = uploads / (uuid.uuid4().hex + ext)
                    filepath.write_bytes(payload)
                    result['uploadId'] = store.record_upload(fname, filepath, hashlib.sha256(payload).hexdigest(), len(payload))
                    result['backendFullImportAvailable'] = True
                return self.respond(200, result)
            if route == '/api/projects/save':
                inp = self.json_body()
                return self.respond(200, store.store_project(inp.get('state') or {}))
            if route == '/api/import-confirm':
                inp = self.json_body()
                uploaded = store.get_upload(str(inp.get('uploadId') or ''))
                if not uploaded: raise ValueError('Không tìm thấy file preview. Upload lại.')
                data = pathlib.Path(uploaded['path']).read_bytes()
                headers, rows = read_export(data, uploaded['filename'])
                mapping = inp.get('mapping') or {}
                if any(c and c not in headers for c in mapping.values()):
                    raise ValueError('Cột ghép không tồn tại trong file gốc.')
                locale = str(inp.get('locale') or 'vi-VN')
                rep = str(inp.get('reportType') or 'KEYWORD_OVERVIEW')
                if rep not in ('KEYWORD_OVERVIEW','RELATED','QUESTIONS','ORGANIC_RESULTS'):
                    raise ValueError('Loại báo cáo không được hỗ trợ.')
                normalized, stats = normalize_rows(rows, mapping, locale, rep)
                batch_id = store.store_batch(str(inp.get('projectId') or ''), str(inp.get('requestId') or ''), uploaded['id'],
                                              rep, locale, mapping, stats, normalized)
                return self.respond(200, {'batchId':batch_id,'stats':stats,'fullRowCount':len(rows),
                                          'completion': {'type':'PROCESS_COMPLETED','storage':'sqlite'},
                                          'note':'Dữ liệu raw đã lưu SQLite; status không đồng nghĩa SEO-ready.'})
            if route in ('/api/ai/topic', '/api/ai/critic', '/api/research/gaps'):
                inp = self.json_body()
                project_id = str(inp.get('projectId') or '')
                state = store.load_project(project_id)
                if not state: raise ValueError('Hãy lưu dự án SQLite trước khi dùng AI.')
                if route == '/api/ai/topic':
                    out = analyze_topic(state)
                    out['run_id'] = store.store_ai_run(project_id, 'TOPIC_INTELLIGENCE', provider_config()['provider'], 'COMPLETED', out)
                    return self.respond(200, out)
                ev = store.load_evidence(project_id)
                project = state.get('project') or {}
                seeds = [project.get('primary',''), *(project.get('secondaries','') or '').splitlines()]
                ev['exact_seed_evidence'] = store.exact_seed_evidence(project_id, seeds)
                gaps = infer_research_gaps(ev, seeds)
                if route == '/api/research/gaps':
                    return self.respond(200, {'gaps':gaps,'evidence':{'batch_count':len(ev['batches'])}})
                out = assess_evidence(state, ev, gaps)
                out['deterministic_gaps']=gaps
                out['run_id']=store.store_ai_run(project_id,'CRITIC_AFTER_SEMRUSH',provider_config()['provider'],'COMPLETED',out)
                return self.respond(200,out)
            return self.respond(404, {'error':'Route không tồn tại.'})
        except (ValueError, json.JSONDecodeError) as exc:
            return self.respond(422, {'error': str(exc), 'feedback': error_feedback(route, exc)})
        except Exception as exc:
            self.log_message('Request error: %s', str(exc))
            return self.respond(500, {'error':'Lỗi server local. Kiểm tra server và thử lại; chưa xác nhận hoàn thành.', 'feedback':error_feedback(route, exc)})


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5173
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    print(f'Local SEO Workbench prototype: http://127.0.0.1:{port} (Ctrl+C to stop)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down.')
    finally:
        server.server_close()
