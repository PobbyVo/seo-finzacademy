import persistent_store as store
from evidence_engine import normalize_rows
from server import error_feedback


def test_history_survives_new_ui_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DATABASE_DIR', tmp_path)
    monkeypatch.setattr(store, 'DB_FILE', tmp_path / 'history.sqlite3')
    store.init_db()
    project = {'id': 'history', 'name': 'Topic mới', 'topicCode': 'Z42'}
    old = [{'url': 'https://example.org/a', 'position': 1}]
    store.store_project({'project': project, 'serp': old, 'approvals': [{'status': 'PENDING'}]})
    result = store.store_project({'project': project, 'serp': []})
    assert result['completion']['type'] == 'PROCESS_COMPLETED'
    assert store.load_project('history')['serp'] == old
    with store.conn() as db:
        assert db.execute('select count(*) from project_events').fetchone()[0] == 2


def test_low_volume_and_duplicate_rows_preserved():
    rows, stats = normalize_rows([{'Keyword':'máy', 'Volume':'0'}, {'Keyword':'máy', 'Volume':'1'}],
                                 {'keyword':'Keyword', 'volume':'Volume'})
    assert len(rows) == 2
    assert rows[0]['data']['volume'] == 0
    assert rows[0]['data']['kd'] is None
    assert stats['MISSING_KD_COLUMN'] == 2
    assert stats['DUPLICATE_KEYWORD_IN_FILE'] == 1
    assert stats['seo_readiness'] != 'READY_FOR_BRIEF'


def test_feedback_has_actionable_contract():
    f = error_feedback('/api/projects/save', ValueError('Thiếu Topic Pillar'))
    assert f['code'] == 'DB_SAVE_FAILED'
    assert all(k in f for k in ('reason', 'impact', 'solution', 'next_action', 'blocking', 'source_ref'))
