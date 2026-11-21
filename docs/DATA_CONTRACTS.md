# DATA CONTRACTS — FINZ SEO ASSISTANT V1.2

## 1. Nguyên tắc schema

- Source nhập tay `USER_FORM`, file quan sát `SEMRUSH_EXPORT`, SERP nhập tay `SERP_MANUAL`, nhận định `MODEL_INFERENCE` là các loại bằng chứng khác nhau; không đúc thành một giá trị không nguồn.
- Người dùng tạo Pillar/Topic Pillar động; không hardcode P01, thuế, BHXH hoặc danh sách topics.
- Keyword gốc không sửa tại chỗ sau khi snapshot đã chốt. Mọi điều chỉnh tạo version mới và lưu `before`/`after`.
- Định danh `id`: UUID/ULID. `topic_code` của user không nhất thiết duy nhất giữa workspace, chỉ cần duy nhất trong snapshot/workspace theo chính sách.
- Thời gian lưu UTC, hiển thị timezone của người dùng. `null` luôn khác zero.
- `ResearchRequest` không bao giờ tự đánh dấu `UPLOADED/VALIDATED` chỉ từ AI suggestion.
- Object từ LLM chỉ là candidate; backend mã hóa bằng Pydantic và kiểm tra reference thực có trong DB.

## 2. Form submission — project & taxonomy (JSON ví dụ)

```json
{
  "project_name": "Nghiên cứu nội dung P01 (DEMO)",
  "business_goal": "Hỗ trợ hiểu biết tài chính và chuyển đổi lead khi phù hợp",
  "target_audience": "Người đi làm cần hiểu khoản thu nhập từ lương",
  "market": {"country": "VN", "language": "vi", "locale": "vi-VN"},
  "research_mode": "TOPIC_PILLAR",
  "article_target": {"min": 5, "max": 7, "hard_quota": false},
  "pillars": [{"key": "earn", "name": "1. KIẾM TIỀN"}],
  "topics": [{
    "topic_code": "P01",
    "topic_name": "Lương",
    "pillar_key": "earn",
    "topic_type": "Theo thứ cụ thể",
    "pillar_axis": "Theo nguồn thu nhập",
    "main_topics_raw": "Lương & tăng lương · Deal lương · Gross/net · Thuế TNCN từ lương",
    "main_topics": ["Lương & tăng lương", "Deal lương", "Gross/net", "Thuế TNCN từ lương"],
    "notes": null
  }],
  "content_codes": [{
    "content_code": "P01.1-①",
    "topic_code": "P01",
    "content_topic": "Phiếu lương & lương thực nhận",
    "original_title": "Lương gross và net là gì, vì sao lương thực nhận thấp hơn trên hợp đồng"
  }],
  "source_keywords": [
    {"content_code": "P01.1-①", "keyword_text": "lương gross net là gì", "role": "Chính", "funnel_stage": "TOFU"},
    {"content_code": "P01.1-①", "keyword_text": "cách đọc phiếu lương", "role": "Phụ", "funnel_stage": "MOFU"}
  ]
}
```

Ví dụ này chỉ là DEMO P01. `TopicPillar` và `main_topics` được đưa vào **input** và database, không tạo constants trong Python/TypeScript. Nếu người dùng nhập `P08` về tiết kiệm thì cùng schema và engine chạy mà không sửa code.

## 3. DemandGroup & KeywordSuggestion (LLM output)

```json
{
  "project_id": "project-uuid",
  "taxonomy_snapshot_id": "tax-snap-uuid",
  "research_state": "PRE_SEMRUSH",
  "demand_groups": [
    {
      "user_need": "Hiểu sự khác nhau giữa hai kiểu lương và khoản thực nhận",
      "suggested_name": "Hiểu Gross/Net",
      "source_ref_ids": ["evidence-backend-uuid"],
      "scope_status": "RELATED_SAME_CONTENT",
      "candidate_keywords": [{
        "text": "lương gross là gì",
        "origin_kind": "AI_PROPOSED",
        "reason_vi": "Biến thể diễn đạt một phần nhu cầu hiểu Gross",
        "source_ref_ids": ["evidence-backend-uuid"],
        "volume": null,
        "kd": null,
        "intent_semrush": null,
        "approval_state": "PENDING_REVIEW"
      }]
    }
  ]
}
```

Validator chỉ chấp nhận `source_ref_ids` xuất từ backend, cấm AI bịa row/sheet/URL. Trạng thái `PENDING_REVIEW` ở payload là đề xuất, trạng thái approval thực lấy từ DB/reviewer.

## 4. Semrush ResearchRequest

```json
{
  "request_id": "uuid-request-01",
  "project_id": "project-uuid",
  "topic_code": "P01",
  "demand_group_id": "uuid-demand-01",
  "seed_keyword": "lương gross net là gì",
  "report_category": "KEYWORD_OVERVIEW",
  "report_name_shown_in_seo_tool": "Keyword Overview",
  "market": "VN",
  "why_needed_vi": "Đo dữ liệu thực của seed gốc trước khi chọn ưu tiên",
  "required_fields": ["keyword", "volume", "kd"],
  "optional_fields": ["intent", "serp_features", "trend", "cpc"],
  "manual_steps_vi": ["Mở Semrush Local ngoài app", "Đo seed với database VN", "Xuất CSV/XLSX", "Quay lại tool để gắn file với request"],
  "status": "WAITING_FOR_UPLOAD"
}
```

`report_category` là logic của app; `report_name_shown_in_seo_tool` chỉ là nhãn UI, không được giả định 1:1 với Semrush MCP report code.

## 5. Import submission (multipart form)

Metadata request (một JSON part) + file binary (CSV/XLSX). Server tính `sha256`; không tin filename/extension một cách mù quáng.

```json
{
  "request_id": "uuid-request-01",
  "report_category": "KEYWORD_OVERVIEW",
  "source_system": "SEMRUSH_LOCAL_EXPORT",
  "seed_keyword": "lương gross net là gì",
  "geo": "VN",
  "language": "vi",
  "exported_at": "2026-11-20",
  "number_locale": "vi-VN",
  "csv_delimiter": "AUTO_DETECT",
  "encoding": "AUTO_DETECT",
  "xlsx_sheet_name": null,
  "column_mapping": {
    "keyword": "Keyword",
    "volume": "Search Volume",
    "kd": "KD %",
    "intent": "Intent",
    "serp_features": "SERP Features"
  }
}
```

Backend trả preview 20 dòng và lỗi theo `row_number`, `column`, `raw_value`, `reason_code`, `recommended_action`; chỉ tạo `MetricObservation` chính thức sau hành động `Confirm import`.

## 6. Normalized Observation

```json
{
  "keyword_id": "uuid-kw",
  "raw_keyword": "lương gross là gì",
  "normalized_keyword": "lương gross là gì",
  "volume": 9900,
  "kd": 21.0,
  "intent_raw": "Informational",
  "intent_interpreted": "Informational",
  "serp_features_raw": "AI Overview, People also ask",
  "source": {
    "kind": "SEMRUSH_EXPORT",
    "import_batch_id": "batch-uuid",
    "row_number": 2,
    "market": "VN",
    "exported_at": "2026-11-20",
    "report_category": "KEYWORD_OVERVIEW"
  }
}
```

Số liệu JSON trên chỉ để thử nghiệm parser/formatter, **không phải số liệu Semrush mới được truy vấn**. `ImportBatch` luôn kèm dấu vết file và mapping.

## 7. SERP Manual Evidence

```json
{
  "keyword_id": "uuid-kw",
  "market": "VN",
  "device": "DESKTOP",
  "observed_at": "2026-11-20",
  "source_type": "USER_UPLOADED_SERP",
  "organic_results": [
    {"position": 1, "url": "https://example.org/a", "title": "Ví dụ A", "snippet": "Ví dụ dữ liệu", "page_type": "UNKNOWN", "classification_source": "UNVERIFIED"}
  ],
  "completeness": "PARTIAL",
  "review_state": "HOLD"
}
```

Mảng chỉ một URL không được tự nhận là “SERP top 10”. Không bắt buộc user cung cấp đủ 10 URL nếu dữ liệu không sẵn có, nhưng trạng thái đủ bằng chứng phải xác định rõ dựa trên coverage, định dạng và độ chắc chắn.

## 8. ArticleOpportunity & Approval

`ArticleOpportunity` bắt buộc chứa: `project_id`, `topic_id`, `demand_group_id`, `original_content_codes`, `original_primary_refs`, `proposed_primary_id`, `secondary_ids`, `user_need`, `page_type=ARTICLE/TOOL/DOWNLOAD/...`, `serp_evidence_refs`, `priority`, `status`, `reasons`, `coverage_gaps`.

`ChangeProposal` gồm `proposal_type`, `before`, `after`, `source_ref_ids`, `reason_vi`, `impact_vi`, `reviewer`, `decision`, `decided_at`, `version`. AI không bao giờ được ghi trực tiếp `APPROVED` vào bảng approval.

Trạng thái phổ biến: `READY_FOR_RESEARCH`, `WAITING_DATA`, `WAITING_REVIEW`, `READY_FOR_BRIEF`, `DRAFT`, `APPROVED`. Mọi gate trạng thái `PASS/HOLD/REVIEW/OUT_OF_SCOPE` lưu độc lập.

## 9. ContentBrief & WritingStrategy

```json
{
  "article_id": "article-uuid",
  "content_type": "ARTICLE",
  "seo": {
    "primary_keyword_id": "kw-uuid",
    "secondary_keyword_ids": [],
    "search_intent": "Informational",
    "metric_refs": [],
    "serp_evidence_refs": [],
    "url_proposal": "/example/"
  },
  "content": {
    "target_audience": "Người đọc mô tả trong project",
    "objective": "Giải thích vấn đề",
    "title": "Tiêu đề bài viết",
    "h1": "H1 đề xuất",
    "meta_description": "Mô tả đề xuất",
    "outline": [{"h2": "Một mục nội dung", "coverage_requirements": "Những điều cần giải thích", "evidence_needed": "Nguồn cần xác minh"}]
  },
  "writing_strategy": {
    "primary_framework": "APP",
    "supporting_frameworks": ["Q&A"],
    "headline_guidance": "4U hữu ích và cụ thể, không ép giật gân",
    "global_tactics": ["T04", "T07", "T12", "T16"],
    "introduction_options": ["Gợi ý mở bài A", "Gợi ý mở bài B"],
    "editor_override_allowed": true,
    "assign_framework_to_h2": false,
    "assign_tactics_to_h2": false
  },
  "qa": {"state": "DRAFT", "missing_evidence": ["SERP_REQUIRED"]}
}
```

ContentBrief JSON hợp lệ không có nghĩa đủ điều kiện xuất brief được duyệt. Chặn bằng gate + approvals ở server.

## 10. Error object & statuses

```json
{
  "error": {
    "code": "MISSING_REQUIRED_SOURCE_FIELD",
    "message_vi": "Thiếu trường Trục chia của pillar",
    "fields": ["pillar_axis"],
    "next_action_vi": "Nhập trường này trong form Topic Pillar",
    "request_id": "trace-id"
  }
}
```

HTTP 400 bad input, 404 not found, 409 stale approval, 413 file too large, 422 schema validation. Không ghi raw file hoặc API key ra logs.
