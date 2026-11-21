"""Read a user-exported Topic Pillar + Keywords workbook for local-only preview.

This is a source-data parser, NOT Semrush metrics importer and NOT AI.
No network calls. Never modifies uploaded bytes or existing project.
"""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from collections import Counter, OrderedDict
from typing import Any

MAX_ROWS = 5000
MAX_COLS = 50
MAX_WARNINGS = 70


def normalized(value: Any) -> str:
    s = unicodedata.normalize('NFD', str(value or '').strip().lower())
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn').replace('đ', 'd')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()


TOPIC_FIELDS = {
    'code': ('mã', 'ma', 'topic code', 'topic id', 'topic pillar code', 'pillar code'),
    'name': ('topic pillar', 'topic name', 'tên topic pillar', 'ten topic pillar', 'chủ đề', 'chu de'),
    'pillar': ('pillar', 'nhóm pillar', 'nhom pillar', 'business pillar'),
    'topicType': ('loại topic', 'loai topic', 'topic type'),
    'axis': ('trục chia của pillar', 'truc chia cua pillar', 'pillar axis', 'trục chia', 'truc chia'),
    'mainTopics': ('chủ đề chính bên trong', 'chu de chinh ben trong', 'main topics', 'topic coverage'),
    'oldCode': ('mã cũ (20 pillar)', 'ma cu 20 pillar', 'mã cũ', 'ma cu'),
    'notes': ('ghi chú', 'ghi chu', 'notes'),
}
KEYWORD_FIELDS = {
    'keyword': ('key', 'keyword', 'từ khóa', 'tu khoa'),
    'role': ('loại', 'loai', 'role', 'keyword role'),
    'funnel': ('giai đoạn', 'giai doan', 'funnel', 'content stage'),
    'verification': ('kiểm chứng', 'kiem chung', 'verification'),
    'reportedVolume': ('lượng tìm/tháng (điền từ keyword planner)', 'luong tim thang dien tu keyword planner', 'search volume', 'volume'),
    'duplicateFlag': ('trùng key?', 'trung key', 'duplicate', 'duplicate flag'),
    'contentCode': ('mã nội dung gốc', 'ma noi dung goc', 'content code', 'origin content code'),
    'contentTitle': ('chủ đề', 'chu de', 'topic'),
    'originalTitle': ('nội dung gốc', 'noi dung goc', 'original content', 'original title'),
}
TOPIC_REQUIRED = ('code', 'name', 'pillar', 'topicType', 'axis', 'mainTopics')
KW_REQUIRED = ('keyword', 'role', 'contentCode', 'contentTitle', 'originalTitle')


def column_map(header, fields):
    cells = [normalized(v) for v in header]
    aliases = {k: set(normalized(a) for a in opts) | {normalized(k)} for k, opts in fields.items()}
    found = {}
    used = set()
    for field, names in aliases.items():
        for i, cell in enumerate(cells):
            if cell and i not in used and cell in names:
                found[field] = i
                used.add(i)
                break
    return found


def find_table(rows):
    best = None
    for idx, row in enumerate(rows[:25]):
        for kind, fields, required in [('taxonomy', TOPIC_FIELDS, TOPIC_REQUIRED), ('keywords', KEYWORD_FIELDS, KW_REQUIRED)]:
            matches = column_map(row, fields)
            mandatory = sum(f in matches for f in required)
            # Ensure no false recognition from description lines.
            can_use = all(x in matches for x in (('code', 'name') if kind=='taxonomy' else ('keyword', 'contentCode')))
            if not can_use:
                continue
            score = mandatory * 100 + len(matches)
            if not best or score > best['score']:
                best = {'kind': kind, 'headerRow': idx + 1, 'mapping': matches, 'score': score}
    return best


def rows_from_csv(data):
    decoded = None
    for enc in ('utf-8-sig', 'utf-16', 'cp1258', 'cp1252'):
        try:
            decoded = data.decode(enc)
            break
        except UnicodeError:
            pass
    if decoded is None:
        raise ValueError('Không đọc được mã hóa CSV. Hãy xuất CSV UTF-8.')
    sample = decoded[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
        reader = csv.reader(io.StringIO(decoded), dialect)
    except csv.Error:
        reader = csv.reader(io.StringIO(decoded), delimiter=',')
    rows = []
    for index, line in enumerate(reader):
        if index >= MAX_ROWS:
            raise ValueError('CSV vượt giới hạn 5.000 dòng của bản prototype.')
        rows.append([str(x or '').strip()[:5000] for x in line[:MAX_COLS]])
    return [{'name': 'CSV', 'rows': rows}]


def rows_from_xlsx(data):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError('Cần cài openpyxl để đọc XLSX.') from exc
    if not data.startswith(b'PK'):
        raise ValueError('Đây không phải file XLSX hợp lệ.')
    try:
        book = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:
        raise ValueError('Không thể đọc XLSX. Hãy xuất lại dưới định dạng .xlsx.') from exc
    tables = []
    try:
        for sheet in book.worksheets[:35]:
            sheet.reset_dimensions()
            rows = []
            for idx, row in enumerate(sheet.iter_rows(values_only=True)):
                if idx >= MAX_ROWS:
                    raise ValueError(f'Tab {sheet.title} vượt giới hạn 5.000 dòng.')
                rows.append(['' if x is None else str(x).strip()[:5000] for x in row[:MAX_COLS]])
            tables.append({'name': sheet.title, 'rows': rows})
    finally:
        book.close()
    return tables


def extract_records(table, info):
    mapping = info['mapping']
    results = []
    start = info['headerRow']
    for i, row in enumerate(table['rows'][start:], start=start+1):
        if not any(str(x).strip() for x in row):
            continue
        mapped = {key: (row[pos].strip() if pos < len(row) else '') for key, pos in mapping.items()}
        if info['kind'] == 'taxonomy':
            if not mapped.get('code') and not mapped.get('name'):
                continue
        else:
            if not mapped.get('keyword') and not mapped.get('contentCode'):
                continue
        mapped['sourceRow'] = i
        mapped['sourceTab'] = table['name']
        results.append(mapped)
    return results


def choose_best(tables, kind):
    found=[]
    for table in tables:
        info=find_table(table['rows'])
        if info and info['kind']==kind:
            name_bonus = 60 if (kind=='taxonomy' and normalized(table['name']) in ('topic pillar','taxonomy','topic pillars')) or (kind=='keywords' and normalized(table['name']) in ('keywords','keyword')) else 0
            found.append((info['score']+name_bonus, table, info))
    return max(found, key=lambda x:x[0])[1:] if found else (None,None)


def derive_topic_code(content_code, known_codes):
    value = str(content_code or '').strip()
    if not value:
        return ''
    # Match known taxonomy IDs by delimiter boundary; never infer from topic words.
    for code in sorted(known_codes, key=len, reverse=True):
        if value.casefold() == code.casefold() or value.casefold().startswith((code+'.').casefold()) or value.casefold().startswith((code+'-').casefold()):
            return code
    return re.split(r'[.\-]', value, maxsplit=1)[0].strip()


def interpret_source(tables, filename):
    tax_table, tax_info = choose_best(tables, 'taxonomy')
    kw_table, kw_info = choose_best(tables, 'keywords')
    if tax_table is None and kw_table is None:
        raise ValueError('Không nhận diện được bảng Topic Pillar hoặc Keywords. Kiểm tra tên cột trong file.')
    topics = extract_records(tax_table,tax_info) if tax_table else []
    keyword_records = extract_records(kw_table,kw_info) if kw_table else []
    warnings=[]
    def warn(code, message, sheet=None, row=None):
        if len(warnings)<MAX_WARNINGS:
            warnings.append({'code':code,'message':message,'sheet':sheet,'row':row})
    if tax_table is None: warn('NO_TAXONOMY','Chưa có bảng Topic Pillar. Hãy nạp file Topic Pillar để hoàn thiện dữ liệu.')
    if kw_table is None: warn('NO_KEYWORDS','Chưa có bảng Keywords. Hãy nạp file Keywords để điền mã nội dung và seed.')
    valid_topics=[]
    incomplete=[]
    seen=set()
    for row in topics:
        missing=[field for field in TOPIC_REQUIRED if not str(row.get(field,'')).strip()]
        code=row.get('code','').strip()
        if code and code.casefold() in seen:
            warn('DUPLICATE_TOPIC',f'Mã Topic Pillar {code} xuất hiện nhiều lần; cần rà soát.',row['sourceTab'],row['sourceRow'])
            missing.append('Mã bị trùng')
        if code: seen.add(code.casefold())
        row['isValid']=not missing
        row['missingFields']=missing
        if missing:
            incomplete.append(row)
            warn('INCOMPLETE_TOPIC',f'Topic {code or "(không mã)"} thiếu: {", ".join(missing)}.',row['sourceTab'],row['sourceRow'])
        else:
            valid_topics.append(row)
    code_map={row['code']:row for row in valid_topics}
    groups=OrderedDict()
    orphan=[]
    duplicate_keyword_counter=Counter()
    for r in keyword_records:
        code=r.get('contentCode','')
        topic_code=derive_topic_code(code, code_map)
        r['topicCode']=topic_code
        r['roleRaw']=r.get('role','')
        role=normalized(r.get('role',''))
        r['roleType']='PRIMARY' if role in ('chinh','primary','main') else ('SECONDARY' if role in ('phu','secondary','supporting') else 'UNCLASSIFIED')
        r['funnelSource']=r.get('funnel','')
        r['metricStatus']='UNVERIFIED_SOURCE' if r.get('reportedVolume') else 'NOT_MEASURED'
        if not r.get('keyword') or not code:
            warn('INCOMPLETE_KEYWORD','Thiếu Keyword hoặc Mã nội dung gốc.',r['sourceTab'],r['sourceRow'])
            orphan.append(r)
            continue
        if not topic_code or (topics and topic_code not in code_map):
            warn('UNMATCHED_KEYWORD',f'Keyword "{r["keyword"]}" không ghép được với một Topic Pillar hợp lệ: {topic_code or "(trống)"}.',r['sourceTab'],r['sourceRow'])
            orphan.append(r)
            continue
        if code not in groups:
            groups[code]={'code':code,'topicCode':topic_code,'contentTitle':r.get('contentTitle',''), 'originalTitle':r.get('originalTitle',''), 'keywords':[], 'firstRow':r['sourceRow']}
        groups[code]['keywords'].append(r)
        key=(topic_code,normalized(r['keyword']))
        duplicate_keyword_counter[key]+=1
    for (topiccode,keyword),v in duplicate_keyword_counter.items():
        if v>1: warn('DUPLICATE_KEYWORD',f'Keyword "{keyword}" bị lặp {v} lần trong {topiccode}.')
    content_groups=list(groups.values())
    for group in content_groups:
        primary=[r for r in group['keywords'] if r['roleType']=='PRIMARY']
        group['primaryCount']=len(primary)
        group['primary']=primary[0]['keyword'] if primary else ''
        group['secondaries']=[r['keyword'] for r in group['keywords'] if r['roleType']=='SECONDARY']
        if len(primary)!=1: warn('PRIMARY_COUNT',f'Mã {group["code"]}: tìm thấy {len(primary)} keyword chính; cần chọn thủ công.',kw_table['name'] if kw_table else '',group['firstRow'])
    complete = bool(valid_topics) and bool(keyword_records)
    return {'formatVersion':1,'filename':filename,'detected':{'taxonomyTab':tax_table['name'] if tax_table else None,'taxonomyHeaderRow':tax_info['headerRow'] if tax_info else None,'keywordTab':kw_table['name'] if kw_table else None,'keywordHeaderRow':kw_info['headerRow'] if kw_info else None},
        'topics':valid_topics,'incompleteTopics':incomplete,'contentGroups':content_groups,'orphanKeywords':orphan,
        'stats':{'validTopics':len(valid_topics),'incompleteTopics':len(incomplete),'keywordRows':len(keyword_records),'contentCodes':len(content_groups),'orphanKeywords':len(orphan),'complete':complete},'warnings':warnings}


def parse_topic_source(payload:bytes, filename:str):
    if filename.lower().endswith('.xlsx'):
        tabs=rows_from_xlsx(payload)
    elif filename.lower().endswith('.csv'):
        tabs=rows_from_csv(payload)
    else:
        raise ValueError('Chỉ hỗ trợ file .xlsx hoặc .csv.')
    return interpret_source(tabs,filename)
