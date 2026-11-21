# FINZ SEO ASSISTANT — CORE SPECIFICATION V1.2 + LOCAL UX V1.3

> **UI / workflow precedence:** For interface design, workflow statuses, async progress, blockers, Semrush research UI and file handoff, follow `docs/UX_LOCAL_WORKBENCH_V1_3.md` and `docs/STATE_MACHINE_AND_EVENTS.md` over the older screen-level details in this document. This file retains core SEO/product rules. No Google Sheets/Semrush API/MCP/WordPress runtime connections.

> **Trạng thái:** đặc tả để Codex lập trình, KHÔNG phải ứng dụng đã chạy.  
> **Ngày cập nhật:** 20/11/2026. **Ngôn ngữ UI:** tiếng Việt. **Deployment MVP:** local-only.  
> **Nguồn quy tắc:** người dùng tự khai báo taxonomy và keyword trong ứng dụng. Không có liên kết Google Sheets, Semrush API/MCP, Google Search Console, WordPress hoặc CMS nào trong runtime.  
> **Độc lập chủ đề:** P01/Lương chỉ là fixture minh họa. Engine phải làm việc với P02/P08/P25 và mọi topic được nhập trên UI mà không sửa source code.

## 0. Quyết định kiến trúc bắt buộc

| ID | Quyết định cuối cùng |
|---|---|
| ADR-001 | Google Sheets **KHÔNG** kết nối. Mọi dữ liệu Pillar/Topic Pillar/keyword được tạo, sửa, nhập trực tiếp bằng FORM/UI; lưu SQLite. Tên Google Sheets gốc chỉ để người dùng tham khảo, không có quyền truy cập tự động. |
| ADR-002 | Semrush Local **KHÔNG** kết nối API/MCP/automation. AI lập `ResearchRequest`, người dùng thao tác bên ngoài, upload CSV/XLSX theo form. |
| ADR-003 | BỎ TOÀN BỘ bước tích hợp, đồng bộ, kiểm tra WordPress. Không có API client/crawler WordPress, không có bước bắt buộc hỏi tình trạng WP. Trong MVP chỉ kiểm tra trùng trong những bài/brief đã lưu **trong app**. Không khẳng định website ngoài app không trùng. |
| ADR-004 | Không bắt buộc MCP nào để ứng dụng chạy. MCP của **Codex trong IDE** nếu người dùng tự cài là công cụ phát triển, không phải runtime integration. |
| ADR-005 | Các nhóm nhu cầu tìm kiếm là đối tượng hiển thị chính; keyword là các biến thể bên trong. |
| ADR-006 | Đích 5–7 bài / Topic Pillar là mục tiêu mềm; 4 bài đủ căn cứ + 3 lỗ hổng nghiên cứu hợp lệ. Không sinh bài chỉ để đủ quota. |
| ADR-007 | AI không thay keyword chính gốc hoặc tự duyệt nhánh mới; cần Approval Queue có lý do, bằng chứng, phiên bản và người duyệt. |
| ADR-008 | Chỉ nội dung `ARTICLE`. `TOOL`, `DOWNLOAD`, `PRODUCT`, `SERVICE` nằm ngoài phạm vi đếm bài và xuất brief. |
| ADR-009 | Writing Strategy là **đề xuất cấp toàn bài**: 13 công thức + 16 chiến thuật do người dùng cung cấp; không gắn công thức/chiến thuật vào từng H2/H3; biên tập viên được quyền thay. Không bắt buộc trả lời ngay câu đầu. |
| ADR-010 | Xuất **file XLSX tải về**, CSV/JSON tùy chọn, và HTML preview/in brief; mô phỏng 3 bảng logic của workbook mẫu, **không tạo/sửa Google Sheet trực tiếp**. |
| ADR-011 | AI muốn hoạt động thực cần cấu hình LLM provider riêng (cloud API có opt-in hoặc model local); chỉ có mock thì UI phải gắn nhãn DEMO, không ngụy trang thành phân tích AI thực. |
| ADR-012 | Mọi dữ liệu/logic/phê duyệt lưu theo project và snapshot. Không hardcode P01, chữ `Lương`, workbook ID, locale, bộ từ khóa hoặc tên tab vào engine. |

## 1. Phạm vi sản phẩm

### 1.1 Mục tiêu

Từ thông tin taxonomy và keyword do người dùng tự nhập trên giao diện, hệ thống:

1. Kiểm tra tính hợp lệ của Pillar → Topic Pillar → Trục chia → Chủ đề chính → Mã nội dung → keyword.
2. AI phân tích nhu cầu, phát hiện khoảng trống và đề xuất các nhóm nhu cầu mới có chứng minh taxonomy.
3. Chọn seed keyword cần kiểm chứng và tự tạo phiếu yêu cầu người dùng lấy báo cáo từ Semrush Local.
4. Nhận file Semrush CSV/XLSX, xem trước, ánh xạ cột, phát hiện thiếu/sai/mâu thuẫn; giữ dữ liệu thô.
5. Phân tích Volume, KD, Search Intent; yêu cầu thêm bằng chứng SERP qua file/form khi quyết định dạng bài và tách/gộp cần thiết.
6. Lập cơ hội nội dung, approval, Keyword Mapping và Content Brief.
7. Đưa ra công thức viết + chiến thuật thu hút toàn bài, xuất XLSX/HTML/CSV/JSON bằng file local.

### 1.2 Ranh giới MVP

- KHÔNG đăng nhập Google, không OAuth Google Sheets, không gọi Sheets/Drive API, không đồng bộ định kỳ.
- KHÔNG gọi Semrush API/MCP, không điều khiển Semrush local, không dùng screen scraping để thay người dùng thao tác.
- KHÔNG gọi WordPress API, không sync bài đăng, không kiểm tra draft qua WordPress, không tự publish.
- KHÔNG bắt buộc Google Search Console/GA4 hoặc bất cứ dữ liệu bên thứ ba nào. Có thể thêm import dữ liệu tùy chọn trong phiên bản khác sau khi có yêu cầu mới, không mở rộng ngầm.
- KHÔNG viết trang tool/calculator/download; brief chỉ cho `ARTICLE`.
- Không tự bịa Volume/KD/Intent/SERP result, quy định pháp luật, số thuế/bảo hiểm, testimonial/case thực tế.
- Không bắt buộc A/B test, không gắn framework/tactic với H2/H3.

### 1.3 Hai khái niệm phân biệt

- **Thông tin nhập tay trong app:** dữ liệu được người dùng khai báo, có nguồn `USER_FORM`, trạng thái/phiên bản. Dù có gốc từ Google Sheet bên ngoài, app không được nhận là đã kết nối/đã xác minh Sheet.
- **Quan sát Semrush Local:** dữ liệu người dùng upload, nguồn `SEMRUSH_EXPORT` với file hash, report, thị trường, ngày xuất và row; không được nhận là dữ liệu Semrush thời gian thực.

## 2. Dữ liệu form — không có Google Sheets connector

### 2.1 Màn hình Tạo Project

| Nhóm | Trường UI | Bắt buộc | Quy tắc |
|---|---|---:|---|
| Project | `project_name` | Có | Ví dụ “Nghiên cứu P01”; không bắt buộc chứa P01 |
| Context | `website_domain` | Không | Chỉ metadata để ra URL/CTA; **không** dùng để crawl hay đồng bộ WordPress |
| Objective | `business_goal` | Có | Nhận diện thương hiệu / leads / bán hàng / tùy chỉnh; không tự mặc định B2B cho mọi workspace |
| Audience | `target_audience` | Có | Mô tả người đọc cần phục vụ |
| Market | `country`, `language`, `locale` | Có | Mặc định VN, vi, vi-VN; sửa được |
| Scope | `research_mode` | Có | `TOPIC_PILLAR` mặc định / `CONTENT_CODE` tùy chọn |
| Target | `target_min`, `target_max`, `hard_quota` | Có | 5, 7, false là default, có thể đổi cho project khác |
| Content type | `allowed_content_type` | Có | `ARTICLE` trong V1.2 |

### 2.2 Màn hình nhập Taxonomy (FORM nhiều cấp)

`Pillar` là thực thể do user tạo: `pillar_id` (tùy chỉnh), `pillar_name`, `description`.

Mỗi `Topic Pillar` nhập ít nhất 6 trường **không được bỏ qua**:

| Trường trong form | Tên kỹ thuật | Ví dụ P01 |
|---|---|---|
| Mã | `topic_code` | P01 |
| Topic pillar | `topic_name` | Lương |
| Pillar | `pillar_id` / `pillar_name` | 1. KIẾM TIỀN |
| Loại topic | `topic_type` | Theo thứ cụ thể |
| Trục chia của pillar | `pillar_axis` | Theo nguồn thu nhập |
| Chủ đề chính bên trong | `main_topics[]` + `main_topics_raw` | Lương & tăng lương / Deal lương / Gross/Net / Thuế TNCN từ lương |

Bổ sung `previous_code` (optional), `notes` (optional), `scope_policy_notes` (optional), `manual_source_note` (optional). Không nhập `source_row` nếu không có dữ liệu thực; app tự tạo `form_entry_id`/`snapshot_id`.

Người dùng thêm/sửa/nhân bản/ẩn Topic Pillar; chọn từ danh sách, không phải sửa code. Khi sửa taxonomy quan trọng tạo **taxonomy snapshot mới**; dự án cũ giữ snapshot mà nó đã phê duyệt.

### 2.3 Màn hình mã nội dung và keyword gốc

Người dùng bấm `+ Thêm mã nội dung` với `content_code` (P01.1-① là ví dụ), `content_topic`, `original_article_intent`, `original_title`, `approved_state`, ghi chú.

Trong mỗi mã có bảng nhiều dòng với `keyword_text`, `role` (`Chính`/`Phụ`), `funnel_stage` (`TOFU`/`MOFU`/`BOFU`/`UNKNOWN`), `source_validation_note`, `origin_content_code`. Cho phép `+ Thêm keyword`, `dán nhiều dòng`, sao chép mẫu; bắt buộc chọn đúng content_code. Mọi keyword ban đầu có `origin_kind=USER_INPUT` và `source_immutable_snapshot`, không có dữ liệu Volume/KD mặc định (null).

Ví dụ:
- P01.1-①: “lương gross net là gì” (Chính), “cách đọc phiếu lương” (Phụ).
- P01.2-②: “cách deal lương” (Chính).

Các phần tử P01 chỉ là fixture. Với P08, người dùng có thể nhập “quỹ khẩn cấp”, “tiết kiệm” và các mã riêng trên chính giao diện này.

### 2.4 Validation giao diện

- `topic_code` duy nhất trong một snapshot; có kiểm tra trùng mã content trong project.
- `topic_type`, `pillar_axis` là chuỗi/từ điển user định nghĩa, không là enum hardcode “Theo thứ cụ thể”.
- Mỗi keyword cần `keyword_text` khác rỗng; dữ liệu Unicode Việt giữ nguyên raw.
- Một mã nội dung có nhiều dòng Chính -> cảnh báo `MULTIPLE_SOURCE_PRIMARY` và cho user sửa hoặc giữ REVIEW, không tự đoán.
- Từ khóa trùng giữa hai mã không xóa; gắn cờ `DUPLICATE_ACROSS_CONTENT_CODES` để xử lý mapping về sau.
- Mọi trường có màn hình giải thích (tooltip) bằng tiếng Việt; không cần form rất dài trên một màn. Dùng wizard 3 bước Project → Taxonomy → Keyword, lưu draft tự động.

## 3. Workflow sử dụng thực tế

```
[UI FORM: Project + taxonomy + content codes + keyword gốc]
           |
           v
 F0 source data validation + taxonomy snapshot
           |
           v
 E0 Topic Intelligence: nhóm nhu cầu -> đề xuất seed có source refs
           |
           v
 E1 quality/scope checks + E2 group deduplication
           |
           v
 REVIEW QUEUE: duyệt nhánh mới / keyword mới / giữ original primary
           |
           v
 Research Request Planner -> phiếu báo cáo Semrush cần người dùng xuất
           |
           v
 [Người dùng mở Semrush Local ngoài app -> xuất CSV/XLSX]
           |
           v
 [UI FORM: gán Request ID + report/market/date + upload file]
           |
           v
 F1 metrics validation -> F2 normalization/provenance
           |
           v
 F3 relevance -> F4 prioritization (không hard threshold loại mất)
           |
           v
 Thiếu metrics? -> tạo request bổ sung đúng seed/report -> upload lại
           |
           v
 [UI FORM: upload SERP organic report hoặc nhập URLs/snippets/format]
           |
           v
 F5 SERP fit (thiếu dữ liệu -> HOLD; không gọi WP)
           |
           v
 F6 group + article plan + primary proposal + approve
           |
           v
 4 READY + 3 RESEARCH GAPS có thể xuất kế hoạch; không ép 7
           |
           v
 F7 Content Brief + Writing Strategy global + finance/source QA
           |
           v
 [UI preview] -> [TẢI XLSX / CSV / JSON / In HTML]
```

Vòng lặp `missing metrics` chỉ yêu cầu dữ liệu; vòng lặp `insufficient topic coverage` mới đề xuất nhu cầu mới (giới hạn 2 lượt mặc định, cấu hình được). Không tự lặp vô hạn; không blocking toàn bộ keyword khi vài dòng thiếu.

## 4. E0 — Taxonomy Evidence Gate, generic cho mọi lĩnh vực

Trước khi đề xuất keyword, AI phải lập **demand groups** (các nhu cầu độc lập) từ `topic_name`, `pillar`, `topic_type`, `pillar_axis`, `main_topics`, content code và keyword gốc. Candidate phải có:

- `user_need`, `demand_group_id`, `proposed_keyword`, `supporting_topic_ref_ids`, `relationship_explanation_vi`, `scope_status`, `next_action`.
- `supporting_topic_ref_ids` phải thực sự tồn tại trong snapshot DB; AI không được tự viết nguồn giả.
- `CORE_APPROVED` nếu gốc đã nhập trong content code; `RELATED_SAME_CONTENT`; `NEW_WITHIN_TOPIC`; `CROSS_TOPIC`; `UNCERTAIN`; `UNRELATED`.
- Nhánh `NEW_WITHIN_TOPIC` nghiên cứu được nhưng chờ approval trước triển khai; `CROSS_TOPIC` không tính vào quota topic đang chọn.
- Không gán quan hệ sở hữu bằng từ khóa hardcode như “bảo hiểm => P25”; phải dựa trên taxonomy hiện tại + user need.

**Ví dụ P01 (chỉ minh họa):** “Thuế TNCN từ lương” khớp `main_topics` P01; “thuế freelancer” thuộc P02; “rút BHXH một lần” gần P25. “Khoản bảo hiểm trừ vào lương” là vùng giao thoa cần REVIEW, không ép qua P01.

E0 đánh giá **phạm vi nghiệp vụ**, không khẳng định SEO potential đã xác minh. Kết quả: Topic Opportunity Map với demand cards → seed candidates, reason, evidence status, source group, approvals.

## 5. Research Request Planner — thay Semrush MCP bằng FORM upload

### 5.1 Đặc tả phiếu yêu cầu

Mỗi `ResearchRequest` có `request_id`, `project_id`, `topic_id`, `demand_group_id`, `seed_keyword_id`, `report_category`, `report_display_name`, `market`, `language`, `filters`, `required_fields`, `optional_fields`, `why_needed_vi`, `steps_vi`, `suggested_filename`, `status`, `created_at`.

Các `report_category` gợi ý:

| Category | Khi cần | Cột mong muốn |
|---|---|---|
| `KEYWORD_OVERVIEW` | Đo seed keyword gốc/ứng viên | Keyword, Volume, KD, Intent; CPC/Trend/SERP Features tùy xuất |
| `RELATED_KEYWORDS` | Mở rộng biến thể từ nhu cầu còn thiếu | Keyword, Volume, KD, Intent; seed, match type nếu có |
| `QUESTIONS` | Tìm truy vấn dạng câu hỏi | Keyword + metrics có thể thiếu |
| `ORGANIC_SERP` | Kiểm chứng loại trang trong top results | Keyword, Position, URL; Title/Snippet nếu có |
| `OTHER` | Người dùng đưa một báo cáo hợp lệ khác | Mapping cột tùy chỉnh, không ngụy tạo khả năng của Semrush |

**Không tự động yêu cầu All/Broad/Related/Questions cho mọi seed.** Chỉ tạo yêu cầu bổ sung sau khi phát hiện gap cụ thể. Giao diện có nút `Sao chép checklist`, `Xem hướng dẫn lấy dữ liệu`, `Đánh dấu đã xuất`, `Tải file lên`.

### 5.2 Form nhận file Semrush Local

Bắt buộc có:

1. **Gắn yêu cầu:** chọn `Research Request ID` (hoặc “file bổ sung không có request”).
2. **Nguồn file:** `Semrush Local export`, báo cáo `report_category`/tên thực người dùng thấy, `seed_keyword` nếu áp dụng.
3. **Thị trường:** database/geo (mặc định dự án nhưng confirm), ngôn ngữ nếu có, ngày xuất/đo, đơn vị và cách hiển thị số.
4. **File:** kéo thả/chọn `.csv` `.xlsx`, tối đa cấu hình 20MB mặc định; file CSV delimiter và encoding auto-detect có preview, cho override; XLSX chọn tab cụ thể khi có nhiều tab.
5. **Ánh xạ cột (header mapping):** preview 20 dòng, user chọn `keyword`, `volume`, `kd`, `intent`, `serp_features`, `position`, `url`, `title`, `snippet`; nút lưu mapping dưới tên `ImportProfile` để dùng lại.
6. **Xác nhận import:** hiển thị `valid_rows`, `invalid_rows`, `warnings`, missing fields; user click `Xác nhận nhập` trước khi metric ảnh hưởng phân tích.

**Không coi một file đã upload = file hợp lệ.** Không có chức năng tự gửi truy vấn sang Semrush.

### 5.3 Kiểm tra số liệu

- Locale-aware: `9.900` ở `vi-VN` có thể là 9900; `9.9` ở `en-US` có thể là 9.9. Khi mơ hồ, đánh dấu `AMBIGUOUS_NUMBER` để user xác nhận; không đoán.
- `volume` là số nguyên >=0 hoặc null; `kd` là 0..100 hoặc null; số ngoài giới hạn là ERROR/HOLD.
- Zero khác missing. `Intent` giữ raw text/code, decode khi hợp đồng dữ liệu nguồn đã xác định. Không coi TOFU/MOFU/BOFU là Semrush intent.
- Báo cáo cùng keyword/geo khác thời điểm lưu hai quan sát, không cộng Volume; cùng thời điểm nhưng mâu thuẫn -> FLAG.
- Lưu file hash SHA-256, raw rows immutable, bản normalized riêng; escaped CSV formula injection khi export.
- File lỗi/không đủ cột: lưu và cho preview, cảnh báo, yêu cầu user map lại hoặc thay file; không auto xóa keyword.

## 6. F5 — SERP thủ công, không có WordPress

`SERP Features` (AI Overview, PAA, video…) không thay thế top 10 organic URLs. Khi cần xác minh blog vs tool, tool phải nhận **evidence** từ:
- Upload file `ORGANIC_SERP` (nếu người dùng có từ Semrush Local) với keyword, position, URL và các cột có thật; hoặc
- Form nhập SERP kết quả: keyword, country, device, observed_at, vị trí, URL, title, snippet, `page_type_observed` (`ARTICLE/TOOL/DOWNLOAD/SERVICE/PRODUCT/OTHER/UNKNOWN`), người gắn nhãn, ghi chú.

Không tự nhận dữ liệu SERP là hiện tại nếu người dùng không nhập ngày. Nếu chỉ có URL/title/snippet và chưa đọc nội dung thật, phân loại là **đề xuất sơ bộ**, không khẳng định trang thực sự là công cụ/bài viết. Gắn nhãn `MANUAL_OBSERVATION` vs `MODEL_INFERENCE`.

**Bỏ WordPress hoàn toàn:** không crawler, không WP REST, không WP auth, không yêu cầu cấp quyền hosting/CMS. Kiểm tra bài trùng chỉ trong `article_opportunities`, `keyword_mapping`, `content_briefs` lưu **nội bộ app**. Màn hình thể hiện rõ “Chưa kiểm tra trùng với website bên ngoài”. Không được đánh dấu `NO_EXISTING_CONTENT` nếu thiếu nguồn.

## 7. Gates, trạng thái và cơ chế không bịa dữ liệu

| Gate | Trách nhiệm | Status / missing-data behavior |
|---|---|---|
| `F0` | Kiểm tra dữ liệu do user nhập, snapshot, nguồn vai trò Chính/Phụ | `HOLD` khi thiếu taxonomy hoặc content code bắt buộc |
| `E0` | Scope evidence, topic ownership, cross-pillar | `REVIEW` nếu có giao thoa; `OUT_OF_SCOPE` khi không thuộc topic |
| `E1` | Chất lượng lý do AI đề xuất (có source IDs thật, nhu cầu rõ) | `HOLD` khi source refs bịa, explanation rỗng |
| `E2` | Dedup nhu cầu/biến thể | `REVIEW` nếu chưa rõ có cần 2 bài |
| `F1` | File upload, metrics provenance, locale, market, schema | `HOLD` phần lỗi, không khóa toàn bộ batch |
| `F2` | Normalize/dedup exact, preserve source observations | `REVIEW` nếu contradictory metrics |
| `F3` | Phân loại relevance trong taxonomy | CORE/SUPPORTING/CROSS/UNRELATED + gate status |
| `F4` | Ưu tiên nghiên cứu từ relevance, intent, volume, kd, business fit | Không auto loại Volume0/KD cao; yêu cầu thêm evidence khi cần |
| `F5` | SERP format và intent fit từ file/form người dùng | `HOLD/REVIEW` khi không đủ organic results |
| `F6` | Nhóm bài, đề xuất primary, URL, gộp/tách, target 5–7 mềm | Chờ approval thay primary và nhánh mới |
| `F7` | SEO brief + finance QA + global writing strategy QA | `HOLD` với bài không phải ARTICLE hoặc thiếu chứng cứ quan trọng |

Status quyết định gate: `PASS`, `HOLD`, `REVIEW`, `OUT_OF_SCOPE`; project status và article status lưu riêng, không nhập nhằng. `PASS` gate không đồng nghĩa `APPROVED`.

### 7.1 Approval Queue

Các proposal loại: `NEW_TOPIC_BRANCH`, `CHANGE_PRIMARY_KEYWORD`, `MERGE_GROUPS`, `SPLIT_GROUP`, `MOVE_CROSS_TOPIC`, `APPROVE_CONTENT_PLAN`. Lưu before/after, reason, evidence refs, reviewer (local user label), decision, timestamp, rule/taxonomy version; AI không được tự phê duyệt.

### 7.2 Evidence Gap / Research Again

- `MISSING_METRICS` -> tạo yêu cầu đúng báo cáo cần, không mở rộng chủ đề vô cớ.
- `BAD_IMPORT_SCHEMA` -> yêu cầu remap cột hoặc export lại.
- `NEEDS_SERP` -> upload organic SERP hoặc điền form; không đo lại toàn bộ keyword.
- `HIGH_KD` -> đề xuất long-tail nếu business fit, không xóa seed đã duyệt.
- `INTENT_MISMATCH` -> kiểm tra SERP để quyết định dạng bài; không thay bằng nhãn Semrush đơn lẻ.
- `TOPIC_COVERAGE_GAP` -> nghiên cứu nhánh mới nằm trong taxonomy, giới hạn 2 rounds config.
- `CROSS_TOPIC` -> chuyển vào danh sách khác; không dùng để đạt quota topic hiện tại.

## 8. Article Opportunity & Keyword Mapping

- Nhóm keyword theo **nhu cầu tìm kiếm**, không phải trùng từ; mỗi opportunity có `primary_candidate`, `secondaries`, `user_need`, `scope_reason`, `original_content_codes`, `article_type`, `serp_evidence_refs`, `estimated_priority`, `approval_state`.
- Primary ban đầu do user cung cấp bất biến; `proposed_primary` tách trường và phải duyệt khi thay.
- `ARTICLE` mới tính quota; không tính `TOOL/DOWNLOAD/PRODUCT/SERVICE`.
- `target_min=5,max=7,hard_quota=false`: nếu 4 đủ điều kiện, 3 gap -> báo 4+3; không tạo brief giả. Khi chưa có Semrush/SERP, gọi `READY_FOR_RESEARCH`, tuyệt đối không `READY_FOR_BRIEF`.
- Không có WordPress nên **không khẳng định không trùng bài trên website**. Có thể cảnh báo `EXTERNAL_CONTENT_NOT_CHECKED`, nhưng không buộc phải kết nối CMS.

## 9. Content Brief, Writing Strategy và xuất file

### 9.1 Ba bảng logic cho output — KHÔNG kết nối Google Sheets

| `OutputTable` | Fields chính | Export |
|---|---|---|
| `KEYWORD_OVERVIEW` | keyword, volume, KD, intent, trend nếu file có, features, source/ref, notes, validation status | `.xlsx` sheet có tên sinh động `Keyword Overview` |
| `KEYWORD_MAPPING` | cluster/group, primary/secondary, target URL, article type, priority, status, reason, evidence refs | `.xlsx` sheet `Keyword Mapping` |
| `CONTENT_BRIEF` | Executive Overview + từng block bài viết | `.xlsx` sheet `SEO Content Brief` |

Tên workbook/tab trong ứng dụng là **display labels**, không là biến logic. Có thể thêm hậu tố chủ đề đã được người dùng nhập nhưng không hardcode `- Luong`. Tham chiếu mẫu từ workbook cũ: BRIEF overview cột B:J gồm `Mã bài`, `Tên bài/Hạng mục`, `Loại nội dung`, `Ưu tiên`, `Trạng thái`, `Keyword chính`, `Volume`, `URL dự kiến`, `Chi tiết Brief`; chi tiết gồm metadata, mục tiêu, độc giả, CTA, internal links, SEO title/H1/meta, secondary keywords, nguồn, checklist, H2 outline và hướng dẫn nội dung.

**Không gọi Sheets API hoặc upload file lên Drive.** Tool tạo file `.xlsx` **trên máy local** để user tự mở trong Excel hoặc tự upload Google Sheets khi muốn. Cho `Xem trước`, `Tải file XLSX`, `Tải JSON/CSV`, `In brief (HTML print)`. Không tự thay đổi workbook nguồn.

### 9.2 F7 brief fields

`brief_id`, `project_id`, `article_opportunity_id`, `approved_primary`, `original_primary`, `secondary_keywords`, `metric_refs`, `serp_refs`, `search_intent`, `objective`, `target_audience`, `content_angle`, `seo_title`, `h1`, `meta_description`, `url_proposal`, `cta`, `internal_links` (manual/planned), `outline_sections[{h2,h3,required_coverage,evidence_needed}]`, `writing_strategy`, `financial_source_notes`, `qa_status`, `approved_at`.

Chỉ xuất **brief chính thức** với `ARTICLE`, approval hợp lệ, dữ liệu SERP và nguồn bắt buộc. Có thể xuất bản `DRAFT` để xem nhưng phải đóng dấu `CHƯA ĐỦ BẰNG CHỨNG`, không giả dạng approved.

### 9.3 Writing Strategy — cấp TOÀN BÀI

Thư viện **13 công thức**: AIDA, PAS, BAB, FAB, 4P, APP, QUEST, ACC, SLAP, 4U, Checklist, Q&A, Storytelling.

Thư viện **16 chiến thuật**: câu hỏi mở đầu; tiêu đề tò mò/con số; gợi ý split-test tiêu đề (không chạy A/B test); đưa ý quan trọng lên sớm; preview; kể chuyện; dễ hiểu; câu chủ động/ngắn; power words phù hợp; heading hữu ích; biến thể từ khóa tự nhiên; ví dụ/case/số liệu có nguồn; ảnh/video/bảng khi phù hợp; internal link nếu có thật; tạo bất ngờ có cơ sở; CTA rõ.

Mỗi brief có `primary_framework` (1 đề xuất), `supporting_frameworks` (0-2), `headline_guidance_4u`, `recommended_tactics_global` (3-6), `intro_options` (1-2), `why_selected`, `editor_override_allowed=true`. **Không** lưu `framework_per_h2` hay `tactics_per_h2`. H2/H3 chỉ có hướng dẫn nội dung nghiệp vụ, dữ kiện và ý cần bao phủ. Không ép câu mở bài trả lời trực tiếp ngay lập tức; chỉ bảo đảm bài đáp ứng intent tổng thể.

### 9.4 Financial content QA

Các con số thuế, bảo hiểm, thu nhập, luật cần trích nguồn do người dùng cung cấp hoặc chứng cứ thực sự có, kèm `effective_date`, `checked_at`; nếu thiếu, ghi `SOURCE_REQUIRED/HOLD`. Ví dụ giả định ghi rõ, tuyệt đối không ngụy tạo case study/authority. CTA không trỏ vào công cụ hoặc bài nội bộ chưa tồn tại như thể đã tồn tại. `Internal link` có thể là `PLANNED/UNVERIFIED` vì không có CMS sync.

## 10. UI screens và trải nghiệm

| Path | Screen | Hành vi |
|---|---|---|
| `/projects` | Dashboard | Tạo/chọn project, không hardcode P01 |
| `/projects/new` | Create Project Wizard | Nhập thông tin project và thị trường |
| `/projects/:id/taxonomy` | Taxonomy Form | Pillar, Loại topic, Trục chia, Chủ đề chính, mã content |
| `/projects/:id/seeds` | Original Keywords Editor | Bảng Chính/Phụ, thêm nhiều dòng, tự lưu draft |
| `/projects/:id/topic-map` | Topic Opportunity Map | Card nhóm nhu cầu, keyword bên trong, nguồn/lý do |
| `/projects/:id/approvals` | Approval Queue | Approve/reject có lý do, audit |
| `/projects/:id/requests` | Semrush Research Requests | Danh sách đúng report, seed, lý do, checklist và upload shortcut |
| `/projects/:id/uploads` | Upload & Header Mapping | Upload CSV/XLSX, xem trước/đổi mapping cột/import theo request |
| `/projects/:id/analysis` | Keyword Analysis | F0–F4, evidence gaps, warning/decision |
| `/projects/:id/serp` | SERP Manual Evidence | Upload organic SERP/file hoặc nhập top URLs/format |
| `/projects/:id/article-plan` | Article Opportunities | 4 ready + 3 gaps được phép; user quyết định |
| `/projects/:id/briefs` | Brief Builder | Global writing strategy, outline, QA, preview |
| `/projects/:id/exports` | File Exports | Tải XLSX/JSON/CSV, in HTML; không Google auth |

UI luôn phân biệt **DEMO / AI ĐÃ CẤU HÌNH / ĐANG CHỜ DỮ LIỆU / REVIEW / ĐỦ CĂN CỨ**. Không tạo nút tải file hoặc approve giả. Có empty/loading/error states, keyboard focus, thông báo dữ liệu đã lưu, rõ source refs và reason codes.

## 11. Kiến trúc code đề xuất

### 11.1 Stack

- Frontend: Next.js App Router + TypeScript + TailwindCSS; sử dụng form library + Zod tùy nhu cầu, không bắt buộc.
- Backend: Python 3.12+, FastAPI + Pydantic 2, SQLAlchemy 2, Alembic, SQLite MVP; PostgreSQL khi cần multi-user.
- Parsing: pandas + openpyxl + pandera (CSV/XLSX); kiểm tra bảo mật file, filename, sheet, limits.
- Export: openpyxl cho XLSX; csv/JSON chuẩn; printable HTML view.
- AI: `LLMProvider` protocol với `MockProvider` và adapter cấu hình cho API cloud / local Ollama tương thích nếu thực sự có; secrets chỉ trong env, không mặc định outbound requests.
- No Google SDK, no Semrush MCP/SDK, no WP SDK, no connectors trong runtime MVP.

### 11.2 Modules

```text
finz-seo-assistant/
  apps/web/
    app/projects/{new,[projectId]/taxonomy,[projectId]/seeds,...}/
    components/{forms,topic-map,research-requests,upload-mapping,approval-queue,brief-preview}/
    lib/api-client/
  services/api/
    app/{api,v1,schemas,domain,models,repositories}/
    app/taxonomy/{form_service,scope_gate,snapshot}/
    app/agents/{topic_analyst,keyword_planner,writing_strategy}/
    app/gates/{f0,e0,e1,e2,f1,f2,f3,f4,f5,f6,f7}/
    app/research/{request_planner,upload_service,header_mapper,metric_parser,serp_manual}/
    app/approvals/{service,repository}/
    app/briefs/{renderer,xlsx_export,html_print,catalogs}/
    app/llm/{protocol,mock,cloud_optional,local_optional}/
    alembic/ tests/
  config/{defaults.json,header_aliases.json}
  fixtures/{demo_p01.json,demo_p08.json,semrush_sample.csv}
  docs/ prompts/
```

P01/P08 chỉ trong `fixtures/`, không trong `domain/`, `gates/`, `agents/`, `api/` hoặc exporter.

## 12. Domain models và provenance

| Entity | Fields chính |
|---|---|
| `Project` | id, name, business_goal, audience, country, language, locale, target_range, research_mode |
| `Pillar` | id, name, description, workspace_id |
| `TopicPillar` | topic_code, pillar_id, topic_type, pillar_axis, main_topics_raw, main_topics, notes, taxonomy_snapshot_id |
| `ContentSeedGroup` | id, topic_id, content_code, original_title, original_intent, approved_state |
| `SourceKeyword` | id, group_id, raw_text, source_role, original_funnel, source_note, immutable_snapshot_id |
| `DemandGroup` | id, user_need, topic_id, evidence_refs, scope_classification, confidence |
| `KeywordCandidate` | id, demand_group_id, origin_kind, raw_text, normalized_text, source_refs, status |
| `ResearchRequest` | id, project_id, report_category, seed_ids, expected_fields, status, why_needed, manual_instructions |
| `ImportProfile` | id, report_category, sheet_selection, header_alias_mapping, locale, version |
| `ImportBatch` | id, filename, sha256, report_kind, market, observed_at, request_id, status |
| `MetricObservation` | id, keyword_id, raw_row_ref, market, period, volume, kd, intent_raw, features_raw, import_batch_id |
| `SerpEvidence` | id, keyword_id, rank, url, title, snippet, page_type, observed_at, evidence_source, labeler |
| `ArticleOpportunity` | id, demand_group_id, article_type, primary_candidate, secondary_ids, status, overlap_notes |
| `ChangeProposal` | id, type, before, after, reason, evidence_refs, reviewer, decision, version |
| `ContentBrief` | id, article_id, seo_fields, outline, writing_strategy, qa_state, export_profile_version |
| `GateDecision` | id, gate, entity_id, status, reason_codes, next_actions, evidence_refs, rule_version, timestamp |

Raw SourceKeyword, raw CSV rows và quyết định đã phát sinh là immutable; thay đổi qua bản ghi mới/audit. SQLAlchemy quan hệ theo `project_id`, `taxonomy_snapshot_id`, `run_id`.

## 13. API contracts (đề xuất)

| API | Mục đích |
|---|---|
| `GET /health` | Test runtime |
| `POST /api/v1/projects` / `GET /api/v1/projects` | Tạo/liệt kê project từ UI |
| `POST /api/v1/projects/{id}/pillars` | Tạo Pillar thủ công |
| `POST /api/v1/projects/{id}/topic-pillars` | Nhập Topic Pillar với 6 trường chuẩn |
| `POST /api/v1/projects/{id}/content-codes` | Nhập mã nội dung |
| `POST /api/v1/projects/{id}/source-keywords` | Nhập keyword Chính/Phụ |
| `POST /api/v1/projects/{id}/taxonomy/snapshot` | Chốt phiên bản dữ liệu người dùng khai báo |
| `POST /api/v1/projects/{id}/analyze-topic` | Tạo demand groups/keyword suggestions |
| `GET /api/v1/projects/{id}/topic-map` | Đọc nhóm nhu cầu |
| `GET /api/v1/projects/{id}/approvals` | Xem hàng chờ duyệt |
| `POST /api/v1/approvals/{proposal_id}/decision` | Duyệt/từ chối với optimistic locking |
| `POST /api/v1/projects/{id}/research-requests` | Tạo checklist Semrush thủ công |
| `POST /api/v1/imports/preview` | Nhận file + chọn report, trả preview và mapping |
| `POST /api/v1/imports/{id}/confirm` | Xác nhận dữ liệu vào DB |
| `GET /api/v1/imports/{id}/issues` | Xem lỗi file, thiếu cột, locale |
| `POST /api/v1/projects/{id}/serp/manual` | Nhập/xác nhận SERP thủ công |
| `POST /api/v1/projects/{id}/opportunities/build` | Tạo mapping/gap report |
| `POST /api/v1/projects/{id}/briefs/generate` | Tạo brief khi đủ gate |
| `GET /api/v1/projects/{id}/exports?format=xlsx` | Tạo/tải output local, no Google |

Authorization local private MVP; 400/409/413/422 chuẩn, file size limit, row limit, path traversal defense, macro/formula safety, no execution of uploaded CSV content. API/docs local only.

## 14. Acceptance criteria & automated tests

### 14.1 V0.1 — Manual UI & Topic Intelligence

- Có wizard tạo Project/Pillar/Topic/ContentCode/Keyword hoàn chỉnh; lưu DB và tải lại vẫn nguyên dữ liệu.
- Có thể nhập P01, P02, P08, P25 qua UI, đổi topic mà không sửa code. Không có Google login.
- Tạo Topic Opportunity Map theo demand groups, keyword đề xuất có source reference/taxonomy rationale; không bịa metrics.
- P01 → thuế từ lương hợp scope; thuế freelancer → P02, rút BHXH → P25 khi taxonomy chứa các nhánh đó; nội dung bảo hiểm trừ lương cần REVIEW.
- AI proposal không tự APPROVED. Chỉ sau thao tác user.
- Research Request gắn đúng seed, mục tiêu và file cần xuất; app không truy cập Semrush.

### 14.2 V0.2 — Upload Semrush Local

- CSV/XLSX có thể chọn, header mapping hoạt động với cột tên khác nhau, có preview/import confirm và lưu raw hash.
- `9.900` (vi-VN thousands) và `9,900` (en-US thousands) kiểm thử có ngữ cảnh locale; mơ hồ -> REVIEW.
- Missing không thành 0, duplicate không cộng Volume; intent raw không bị chuyển sai.
- Sai geo/schema tạo error và hướng xử lý, không làm mất keyword gốc.

### 14.3 V0.3 — Manual SERP/Article plan

- Upload/nhập SERP không gọi Google/web tự động, không xuất kết luận top 10 khi chỉ có 3 URL.
- `ARTICLE` vs `TOOL/DOWNLOAD` không đếm sai; 4 ready + 3 gaps hợp lệ.
- Không có WordPress check trong luồng; hiển thị limitation về external duplicate check.
- Primary switch / scope expansion cần approval; mọi quyết định có audit trail.

### 14.4 V1.0–V1.1 — Brief/export

- XLSX gồm 3 bảng logic; overview và detail khớp role/status/keyword/priority.
- Brief full only if mapped ARTICLE & approved; có draft preview gắn cảnh báo nếu thiếu.
- Writing Strategy chọn 1 framework chính + 0-2 hỗ trợ, 3–6 tactics toàn bài; không gắn vào từng H2/H3; tác giả có quyền override.
- Financial claims yêu cầu source/date; không bịa luật/case/số liệu.
- Tải file từ máy; không request Google token, không tạo Google Sheet, không gọi WordPress/Semrush API.

### 14.5 Không-hardcode và bảo mật

- Tìm source code trong `app/domain`, `app/gates`, `app/agents`, `apps/web` không có topic-specific `P01`, `lương`, `finzacademy.com`, Google spreadsheet IDs, `Keyword Overview - Luong` (chỉ có ở fixtures/docs demo).
- Tests chạy tối thiểu với P01, P02, P08, P25 và một Topic Pillar mới tự khai báo từ UI.
- Chạy app không cần internet/Google/Semrush keys ở `DEMO` mode. Khi bật LLM cloud phải opt-in và giải thích dữ liệu gửi ra; không lưu key trong log.
- Nút bấm thật, không fake status; importer kiểm soát CSV formula injection, zip bomb, kích thước file, số hàng, extension/mime.

## 15. Lộ trình Codex

| Milestone | Phạm vi | Không làm |
|---|---|---|
| `M0` | Monorepo, Next.js + FastAPI, SQLite, form Project và demo mock | Không LLM live, không upload, không MCP |
| `M1` | Manual taxonomy + content codes + source keyword CRUD + snapshots | Không Google Sheets API |
| `M2` | E0/E1/E2 + demand groups + đề xuất seed + review/approval | Không đo Semrush thật |
| `M3` | Research Request Planner + form upload preview + header mapping + raw storage | Không kết nối Semrush |
| `M4` | F1–F4 metric processing + per-row errors + evidence gap loop | Không tự bịa metrics |
| `M5` | F5 manual SERP + F6 article plan/approvals | Không WordPress |
| `M6` | F7 briefs + global writing catalog + local XLSX/HTML/JSON export | Không Google Sheets integration |
| `M7` | Regression/UX/performance/security/backup/reuse across topics | Không auto-deploy |

Triển khai một milestone một lần. Sau mỗi phase phải chạy tests/lint/typecheck, cập nhật README và `docs/DEVELOPMENT_LOG.md`; Codex không được claim DONE nếu chỉ sửa docs. Không cần cài MCP để bắt đầu.

## 16. Prompt điều hành Codex — ranh giới quan trọng

Codex cần đọc AGENTS, spec này và milestone trước khi code. **Đừng giao xây toàn ứng dụng trong một prompt.** Thực thi một milestone; chạy kiểm thử; báo files changed, commands, pass/fail, limitations, next phase. Khi user hỏi source đã kết nối chưa, trả thật: **đây là tài liệu hướng dẫn; app chưa tồn tại đến khi Codex lập trình và test**.

---

## Appendix: Reference template vs live connection

Hai file Google Sheets trong lịch sử trao đổi chỉ là **mẫu cấu trúc dữ liệu và bố cục xuất file**. Chúng không được dùng làm `spreadsheet_id` runtime. Người dùng không phải xác thực Google, không có nút “Connect Google Sheets”. Dữ liệu có thể được người dùng gõ/ dán thủ công; XLSX xuất ra có thể được người dùng upload lên bất kỳ ứng dụng bảng tính nào. P01 là fixture đánh giá ranh giới, không phải sản phẩm hardcoded.
