"""Manual Semrush export reader, full-file normalization and evidence gates.

No Semrush API/MCP. Not a claim about ranking probability or SEO success.
"""
from __future__ import annotations

import csv
import io
import re
from collections import Counter
from typing import Any

MAX_IMPORT_ROWS = 25_000


def read_export(payload: bytes, filename: str) -> tuple[list[str], list[dict]]:
    if filename.lower().endswith('.xlsx'):
        from openpyxl import load_workbook
        workbook = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
        try:
            sheet = workbook.active
            sheet.reset_dimensions()
            reader = sheet.iter_rows(values_only=True)
            header = next((x for x in reader if x and any(y is not None for y in x)), None)
            if header is None:
                raise ValueError('File Excel không có dòng header.')
            headers = [str(h).strip() if h is not None else '' for h in header]
            rows = []
            for raw in reader:
                if len(rows) >= MAX_IMPORT_ROWS:
                    raise ValueError(f'File vượt giới hạn {MAX_IMPORT_ROWS} dòng; hãy chia file.')
                if any(v is not None and str(v).strip() for v in raw):
                    rows.append({(h or f'Col_{i+1}'): '' if i >= len(raw) or raw[i] is None else str(raw[i])
                                 for i, h in enumerate(headers)})
            return headers, rows
        finally:
            workbook.close()
    text = None
    for encoding in ('utf-8-sig', 'utf-16', 'cp1258', 'cp1252'):
        try:
            text = payload.decode(encoding)
            break
        except UnicodeError:
            pass
    if text is None:
        raise ValueError('Không đọc được encoding CSV.')
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t|')
        rdr = csv.DictReader(io.StringIO(text), dialect=dialect)
    except csv.Error:
        rdr = csv.DictReader(io.StringIO(text))
    headers = [str(h).strip() for h in (rdr.fieldnames or [])]
    if not any(headers):
        raise ValueError('Thiếu header CSV.')
    rows = []
    for row in rdr:
        if len(rows) >= MAX_IMPORT_ROWS:
            raise ValueError(f'File vượt giới hạn {MAX_IMPORT_ROWS} dòng; hãy chia file.')
        if any(str(v or '').strip() for v in row.values()):
            rows.append({k.strip(): str(v) if v is not None else '' for k, v in row.items() if k})
    return headers, rows


def parse_metric(value: Any, locale: str, field: str) -> tuple[float | int | None, str | None]:
    raw = str(value if value is not None else '').strip().replace('\u00a0', '').replace(' ', '').replace('%', '')
    if not raw:
        return None, f'MISSING_{field.upper()}'
    if not re.fullmatch(r'[\d.,]+', raw):
        return None, f'INVALID_{field.upper()}'
    vi = locale.lower().startswith('vi')
    try:
        if field == 'volume':
            if vi:
                if ',' in raw:
                    return None, 'AMBIGUOUS_VOLUME_LOCALE'
                if '.' in raw and any(len(part) != 3 for part in raw.split('.')[1:]):
                    return None, 'AMBIGUOUS_VOLUME_LOCALE'
                num = int(raw.replace('.', ''))
            else:
                if '.' in raw:
                    return None, 'AMBIGUOUS_VOLUME_LOCALE'
                if ',' in raw and any(len(part) != 3 for part in raw.split(',')[1:]):
                    return None, 'AMBIGUOUS_VOLUME_LOCALE'
                num = int(raw.replace(',', ''))
            return num, None
        # KD is a percentage 0-100; retain decimals.
        normalized = raw.replace('.', '').replace(',', '.') if vi and ',' in raw else raw
        if raw.count('.') > 1 and not (vi and ',' in raw):
            return None, 'INVALID_KD'
        num = float(normalized)
        return (num, None) if 0 <= num <= 100 else (None, 'KD_OUT_OF_RANGE')
    except (ValueError, OverflowError):
        return None, f'INVALID_{field.upper()}'


def normalize_rows(rows: list[dict], mapping: dict, locale: str = 'vi-VN', report_type: str = 'KEYWORD_OVERVIEW') -> tuple[list[dict], dict]:
    if report_type != 'ORGANIC_RESULTS' and not mapping.get('keyword'):
        raise ValueError('Bắt buộc chọn cột Keyword.')
    output = []
    stat = Counter()
    seen = set()
    for r in rows:
        keyword = str(r.get(mapping.get('keyword', ''), '')).strip()
        if not keyword and report_type != 'ORGANIC_RESULTS':
            stat['missing_keyword'] += 1
            continue
        errors = []
        volume, vol_err = parse_metric(r.get(mapping.get('volume', ''), ''), locale, 'volume') if mapping.get('volume') else (None, 'MISSING_VOLUME_COLUMN')
        kd, kd_err = parse_metric(r.get(mapping.get('kd', ''), ''), locale, 'kd') if mapping.get('kd') else (None, 'MISSING_KD_COLUMN')
        intent = str(r.get(mapping.get('intent', ''), '')).strip() if mapping.get('intent') else ''
        if vol_err: errors.append(vol_err)
        if kd_err: errors.append(kd_err)
        if not intent: errors.append('MISSING_INTENT')
        key = keyword.casefold()
        if key in seen: errors.append('DUPLICATE_KEYWORD_IN_FILE')
        if key: seen.add(key)
        for err in errors: stat[err] += 1
        stat['processed'] += 1
        output.append({'raw':r,'data':{'keyword':keyword,'keyword_key':key,'volume':volume,'kd':kd,'intent_label':intent or None,
                                               'report_type':report_type,'source':'USER_SEMRUSH_EXPORT'},'warnings':errors})
    stat['input_rows'] = len(rows)
    stat['usable_keywords'] = sum(1 for x in output if x['data']['keyword'])
    stat['metric_complete_rows'] = sum(1 for x in output if x['data']['volume'] is not None and x['data']['kd'] is not None and x['data']['intent_label'])
    stat['data_quality'] = 'COMPLETE_METRICS' if stat['metric_complete_rows'] == stat['usable_keywords'] and stat['usable_keywords'] else 'PARTIAL_METRICS'
    stat['seo_readiness'] = 'SERP_AND_HUMAN_APPROVAL_REQUIRED' if stat['usable_keywords'] else 'HOLD'
    stat['note'] = 'Metrics đầy đủ không chứng minh đã đủ điều kiện SEO; cần kiểm tra SERP, cạnh tranh, scope, giá trị kinh doanh và duyệt.'
    return output, dict(stat)


def infer_research_gaps(evidence: dict, topic_seeds: list[str]) -> dict:
    """Deterministic research queue; does not invent keywords, intent or metrics."""
    found = dict(evidence.get('exact_seed_evidence') or {})
    summaries = []
    for item in evidence.get('sample_evidence', []):
        row = item.get('data') or {}
        name = (row.get('keyword') or '').casefold()
        if not name:
            continue
        found[name] = row
    for keyword in dict.fromkeys(s.strip() for s in topic_seeds if s and s.strip()):
        row = found.get(keyword.casefold())
        if not row:
            summaries.append({'keyword':keyword,'status':'RESEARCH_REQUIRED','reason':'Chưa có dữ liệu Semrush khớp keyword này',
                              'reports':['KEYWORD_OVERVIEW']})
        elif row.get('volume') is None or row.get('kd') is None or not row.get('intent_label'):
            summaries.append({'keyword':keyword,'status':'RESEARCH_REQUIRED','reason':'Thiếu hoặc mơ hồ Volume/KD/Intent',
                              'reports':['KEYWORD_OVERVIEW']})
        else:
            summaries.append({'keyword':keyword,'status':'SERP_REQUIRED','reason':'Đã có metrics nhưng chưa xác minh dạng trang và khả năng tách/gộp qua SERP',
                              'reports':['ORGANIC_RESULTS']})
    return {'seeds':summaries, 'ready_for_brief':False,
            'explanation':'Không thể chứng minh đủ điều kiện SEO bằng metrics alone; bắt buộc bước SERP, scope và human approval.'}
