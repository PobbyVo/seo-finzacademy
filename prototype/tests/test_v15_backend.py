import io
import json
import tempfile
from pathlib import Path

import ai_demand_engine as ai
import evidence_engine as ee
import persistent_store as store


def test_sqlite_persistent_projects_multiple_topics(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'DATABASE_DIR', tmp_path)
    monkeypatch.setattr(store, 'DB_FILE', tmp_path / 'test.sqlite3')
    store.init_db()
    for topic in ('P01', 'P08', 'P99'):
        st = {'project': {'id':f'id-{topic}','name':'SEO '+topic,'topicCode':topic,'primary':'giải thích về '+topic}}
        assert store.store_project(st)['revision'] == 1
    assert len(store.list_projects()) == 3
    assert store.load_project('id-P99')['project']['topicCode'] == 'P99'
    assert store.store_project({'project': {'id':'id-P08','name':'SEO P08','topicCode':'P08'}})['revision'] == 2
    assert store.load_project('id-P01')['project']['primary'] == 'giải thích về P01'


def test_semrush_export_parse_full_file_and_no_fake_metrics():
    payload = ('Keyword,Search Volume,KD,Intent\n' + ''.join(f'key {i},9.900,21,Informational\n' for i in range(400))).encode()
    headers, raw = ee.read_export(payload, 'export.csv')
    assert len(raw) == 400
    normalized, stats = ee.normalize_rows(raw, {'keyword':'Keyword','volume':'Search Volume','kd':'KD','intent':'Intent'})
    assert len(normalized) == 400
    assert stats['metric_complete_rows'] == 400
    assert normalized[-1]['data']['volume'] == 9900
    assert stats['seo_readiness'] != 'READY_FOR_BRIEF'
    assert ee.parse_metric('9,900', 'vi-VN', 'volume')[1] == 'AMBIGUOUS_VOLUME_LOCALE'
    assert ee.parse_metric('', 'vi-VN','kd')[0] is None


def test_missing_metrics_are_research_required():
    metrics={'sample_evidence':[], 'exact_seed_evidence': {'máy pha cà phê':{
        'keyword':'máy pha cà phê','volume':100,'kd':None,'intent_label':None
    }}}
    gaps=ee.infer_research_gaps(metrics,['máy pha cà phê','máy pha cà phê mini'])
    assert [x['status'] for x in gaps['seeds']] == ['RESEARCH_REQUIRED','RESEARCH_REQUIRED']
    assert gaps['ready_for_brief'] is False


def test_ai_evidence_refs_cannot_be_hallucinated():
    source={'contentCode':'P99.1','topicCode':'P99','sourceContentGroups':[]}
    out=ai.validate_analysis({'groups':[{'title':'Tìm máy','user_need':'Chọn máy','representative_seed':'máy pha cà phê',
            'scope':'WITHIN_PILLAR','source_refs':['P01.1-①'], 'taxonomy_reason':'Máy tại nhà'}]},source)
    assert out['groups'][0]['scope']=='UNCERTAIN'
    assert out['groups'][0]['source_refs']==[]
    assert out['groups'][0]['status']=='RESEARCH_CANDIDATE'
