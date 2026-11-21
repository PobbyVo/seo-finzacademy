"""SQLite persistence for a local-only SEO workbench.

DB is outside the public prototype/ web root. All write paths use parameterized SQL.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sqlite3
import threading
import uuid
from typing import Any

DATABASE_DIR = pathlib.Path(os.environ.get('FINZ_PROTOTYPE_DATA_DIR') or pathlib.Path(__file__).resolve().parent.parent / '.finz_local_data')
DB_FILE = DATABASE_DIR / 'seo_workbench.sqlite3'
LOCK = threading.RLock()


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def conn() -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_FILE, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=15000')
    db.execute('PRAGMA journal_mode=WAL')
    return db


def init_db() -> None:
    with LOCK, conn() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS projects(
                id TEXT PRIMARY KEY, name TEXT NOT NULL, topic_code TEXT NOT NULL,
                data_json TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS project_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL,
                action TEXT NOT NULL, details_json TEXT NOT NULL, at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS file_uploads(
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, path TEXT NOT NULL,
                sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS research_batches(
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, request_id TEXT NOT NULL,
                upload_id TEXT NOT NULL, report_type TEXT NOT NULL, locale TEXT NOT NULL,
                mapping_json TEXT NOT NULL, stats_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id));
            CREATE TABLE IF NOT EXISTS evidence_rows(
                batch_id TEXT NOT NULL, row_num INTEGER NOT NULL,
                raw_json TEXT NOT NULL, normalized_json TEXT NOT NULL,
                warnings_json TEXT NOT NULL, PRIMARY KEY(batch_id,row_num),
                FOREIGN KEY(batch_id) REFERENCES research_batches(id));
            CREATE INDEX IF NOT EXISTS idx_batches_project ON research_batches(project_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_batch ON evidence_rows(batch_id);
            CREATE TABLE IF NOT EXISTS ai_runs(
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL, phase TEXT NOT NULL,
                provider TEXT NOT NULL, status TEXT NOT NULL,
                output_json TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')


def store_project(state: dict[str, Any]) -> dict:
    with LOCK:
        return _store_project(state)


def _store_project(state: dict[str, Any]) -> dict:
    project = state.get('project')
    if not isinstance(project, dict):
        raise ValueError('Chưa có project để lưu SQLite.')
    project_id = str(project.get('id') or '').strip()
    if not project_id or len(project_id) > 128:
        raise ValueError('project.id không hợp lệ.')
    name = str(project.get('name') or '').strip()
    code = str(project.get('topicCode') or '').strip()
    if not name or not code:
        raise ValueError('Thiếu tên dự án hoặc Topic Pillar.')
    # Legacy SERP records remain historical even when the new UI omits that screen.
    previous = load_project(project_id)
    if previous and previous.get('serp'):
        state = dict(state)
        historical = list(previous['serp'])
        for item in state.get('serp') or []:
            if item not in historical:
                historical.append(item)
        state['serp'] = historical
    payload = json.dumps(state, ensure_ascii=False, separators=(',', ':'))
    if len(payload.encode('utf-8')) > 3_000_000:
        raise ValueError('Dữ liệu trạng thái quá lớn. Upload số liệu bằng form Semrush.')
    now = iso_now()
    with LOCK, conn() as db:
        old = db.execute('SELECT revision FROM projects WHERE id=?', (project_id,)).fetchone()
        revision = int(old['revision']) + 1 if old else 1
        if old:
            db.execute('UPDATE projects SET name=?,topic_code=?,data_json=?,updated_at=?,revision=? WHERE id=?',
                       (name, code, payload, now, revision, project_id))
        else:
            db.execute('INSERT INTO projects VALUES (?,?,?,?,?,?,?)',
                       (project_id, name, code, payload, now, now, revision))
        db.execute('INSERT INTO project_events(project_id,action,details_json,at) VALUES (?,?,?,?)',
                   (project_id, 'STATE_SAVED', json.dumps({'revision': revision}), now))
    return {'id': project_id, 'revision': revision, 'saved_at': now, 'storage': 'sqlite', 'completion': {'type': 'PROCESS_COMPLETED', 'storage': 'sqlite'}}


def list_projects() -> list[dict]:
    with conn() as db:
        rows = db.execute('SELECT id,name,topic_code,updated_at,revision FROM projects ORDER BY updated_at DESC').fetchall()
    return [dict(r) for r in rows]


def load_project(project_id: str) -> dict | None:
    with conn() as db:
        row = db.execute('SELECT data_json FROM projects WHERE id=?', (project_id,)).fetchone()
    return json.loads(row['data_json']) if row else None


def record_upload(filename: str, path: pathlib.Path, sha256: str, size: int) -> str:
    upload_id = uuid.uuid4().hex
    with LOCK, conn() as db:
        db.execute('INSERT INTO file_uploads VALUES(?,?,?,?,?,?)',
                   (upload_id, filename, str(path), sha256, size, iso_now()))
    return upload_id


def get_upload(upload_id: str) -> dict | None:
    with conn() as db:
        row = db.execute('SELECT * FROM file_uploads WHERE id=?', (upload_id,)).fetchone()
    return dict(row) if row else None


def store_batch(project_id: str, request_id: str, upload_id: str, report_type: str,
                locale: str, mapping: dict, stats: dict, rows: list[dict]) -> str:
    if not load_project(project_id):
        raise ValueError('Project chưa được lưu trong SQLite.')
    batch_id = uuid.uuid4().hex
    with LOCK, conn() as db:
        db.execute('INSERT INTO research_batches VALUES (?,?,?,?,?,?,?,?,?)',
                   (batch_id, project_id, request_id, upload_id, report_type, locale,
                    json.dumps(mapping, ensure_ascii=False), json.dumps(stats, ensure_ascii=False), iso_now()))
        db.executemany('INSERT INTO evidence_rows VALUES (?,?,?,?,?)', (
            (batch_id, i + 1, json.dumps(r['raw'], ensure_ascii=False),
             json.dumps(r['data'], ensure_ascii=False),
             json.dumps(r['warnings'], ensure_ascii=False)) for i, r in enumerate(rows)
        ))
    return batch_id


def load_evidence(project_id: str, max_rows: int = 300) -> dict:
    with conn() as db:
        batches = [dict(r) for r in db.execute(
            'SELECT id,request_id,report_type,locale,stats_json,created_at FROM research_batches WHERE project_id=? ORDER BY created_at', (project_id,))]
        items = []
        for b in batches:
            rr = db.execute('SELECT normalized_json,warnings_json FROM evidence_rows WHERE batch_id=? LIMIT ?',
                            (b['id'], max_rows)).fetchall()
            items.extend({'batch_id': b['id'], 'report_type': b['report_type'],
                          'data': json.loads(r['normalized_json']), 'warnings': json.loads(r['warnings_json'])} for r in rr)
            b['stats'] = json.loads(b.pop('stats_json'))
    return {'batches': batches, 'sample_evidence': items[:max_rows],
            'warning': 'AI chỉ nhận mẫu tối đa 300 dòng; thống kê đầy đủ được tính khi import, không suy ra tình trạng toàn file từ mẫu.'}


def store_ai_run(project_id: str, phase: str, provider: str, status: str, output: dict) -> str:
    run_id = uuid.uuid4().hex
    with LOCK, conn() as db:
        db.execute('INSERT INTO ai_runs VALUES (?,?,?,?,?,?,?)',
                   (run_id, project_id, phase, provider, status,
                    json.dumps(output, ensure_ascii=False), iso_now()))
    return run_id


init_db()


def exact_seed_evidence(project_id: str, seeds: list[str]) -> dict[str, dict]:
    """Search ALL saved observations for exact seed matches (not the 300-row LLM sample)."""
    target = {str(s).strip().casefold() for s in seeds if str(s).strip()}
    matches: dict[str, dict] = {}
    with conn() as db:
        for row in db.execute('''SELECT r.normalized_json FROM evidence_rows r
                JOIN research_batches b ON b.id=r.batch_id WHERE b.project_id=?''', (project_id,)):
            item = json.loads(row['normalized_json'])
            key = str(item.get('keyword_key') or '').strip().casefold()
            if key in target:
                current = matches.get(key)
                # Prefer a fully measured observation, without averaging or adding volumes.
                complete = item.get('volume') is not None and item.get('kd') is not None and item.get('intent_label')
                old_complete = current and current.get('volume') is not None and current.get('kd') is not None and current.get('intent_label')
                if not current or (complete and not old_complete):
                    matches[key] = item
    return matches
