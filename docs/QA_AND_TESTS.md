# QA & ACCEPTANCE TEST PLAN — V1.2

> Trọng tâm ưu tiên: **chất lượng đề xuất nhóm nhu cầu + minh chứng taxonomy trước Semrush**. Các bước Semrush import, SERP và brief phải được kiểm thử độc lập khi đến milestone tương ứng.

## A. Form nhập dữ liệu (F0)

| ID | Scenario | Expected |
|---|---|---|
| F0-01 | Người dùng tạo project không chọn topic từ fixture | UI tạo project trống hợp lệ, không tự gán P01 |
| F0-02 | Form Topic Pillar không có `topic_type` | Báo thiếu và không chốt snapshot |
| F0-03 | Form Topic Pillar không có `pillar_axis` | Báo thiếu |
| F0-04 | Hai topic cùng code trong snapshot | Chặn trùng mã hoặc yêu cầu sửa |
| F0-05 | Hai keyword giống hệt ở hai mã nội dung | Bảo toàn cả hai nguồn; gắn cờ trùng tiềm năng |
| F0-06 | Keyword gốc là Chính đã được duyệt | Không bị AI thay ở source snapshot |
| F0-07 | Người dùng reload app | Dữ liệu nhập tay còn đủ, không cần Google account |
| F0-08 | User sửa taxonomy sau khi chạy AI | Tạo snapshot version mới, không sửa quyết định của lần cũ |

## B. Topic Intelligence / Taxonomy (E0/E1/E2)

| ID | Scenario | Expected |
|---|---|---|
| E0-01 | P01 seed “lương gross net là gì” | Gắn đúng P01.1-①, không tự đổi primary |
| E0-02 | P01 đề xuất thuế TNCN **từ lương** | Quan hệ rõ với main topic P01; research candidate, không auto approve branch |
| E0-03 | P01 nhận “thuế freelancer” | Đề xuất cross-topic P02 nếu taxonomy P02 đã có |
| E0-04 | P01 nhận “rút BHXH một lần” | Gợi ý P25 nếu taxonomy P25 đã có; không tính bài P01 |
| E0-05 | P01 nhận “bảo hiểm trừ vào lương” | REVIEW giao thoa P01/P25; phải giải thích mục đích người dùng |
| E0-06 | 20 keywords đồng nghĩa nhưng 3 nhu cầu | 3 demand groups, không 20 article opportunities |
| E0-07 | AI trích dẫn source_ref không tồn tại | HOLD/REVIEW; không tự tạo evidence giả |
| E0-08 | Chưa upload Semrush | Tất cả Volume/KD/Semrush Intent = null |
| E0-09 | P08 quỹ khẩn cấp/tiết kiệm | Phân nhóm P08, không kéo keywords P01 vào |
| E0-10 | P02 freelance | Dựa trên P02 source; không giả định mọi thu nhập đều là lương |
| E0-11 | Topic mới do user nhập mà engine chưa từng thấy | Vẫn phân tích theo taxonomy source chứ không crash/hardcode |
| E0-12 | Đổi keyword chính từ source | Tạo `CHANGE_PRIMARY_KEYWORD` proposal, approval bắt buộc |

## C. Semrush Local upload (F1/F2)

| ID | Scenario | Expected |
|---|---|---|
| IMP-01 | CSV/XLSX có đủ cột, đúng report/geo | Preview/map/confirm thành công |
| IMP-02 | Headers `Keyword`, `Search Volume`, `KD %` | Map theo profile/alias, user có thể sửa |
| IMP-03 | Header lạ hoặc đổi thứ tự | UI yêu cầu mapping; không bỏ dữ liệu |
| IMP-04 | XLSX có nhiều tabs | User phải chọn tab phù hợp |
| IMP-05 | Dấu ngăn nghìn kiểu `9.900` locale vi-VN | Parsed 9900 trong ngữ cảnh hợp lệ, không thành 9.9 hoặc 9 |
| IMP-06 | `9,900` locale en-US | Parsed 9900 khi rõ ngữ cảnh |
| IMP-07 | `9.900` nhưng không rõ locale | REVIEW `AMBIGUOUS_NUMBER` |
| IMP-08 | Volume trống | NULL, không thành 0 |
| IMP-09 | Volume = 0 | Giữ zero là dữ liệu hợp lệ có nguồn |
| IMP-10 | KD=107 hoặc Volume=-1 | HOLD row invalid |
| IMP-11 | Keyword xuất 2 báo cáo | Không cộng Volume; lưu hai observations |
| IMP-12 | Báo cáo sai database | Không dùng làm metrics cho project mà không được duyệt |
| IMP-13 | File vượt size hoặc không hợp MIME | 413/422, không ghi file có hại |
| IMP-14 | CSV có `=HYPERLINK(...)` trong cột text | Export an toàn để không tạo formula injection |
| IMP-15 | Upload file hợp lệ nhưng chưa bấm Confirm | Không tác động quyết định hiện tại |

## D. SERP, Mapping, Approval (F3–F6)

| ID | Scenario | Expected |
|---|---|---|
| SERP-01 | Chỉ có `SERP Features` | Không nhận là có organic top 10 |
| SERP-02 | SERP nhập 3 URL | Có thể tham khảo nhưng confidence thấp, không nói “đã xem top 10” |
| SERP-03 | Kết quả SERP chủ yếu là công cụ hoặc file | Không tính keyword làm blog ready khi intent không phù hợp |
| SERP-04 | Có 4 ARTICLE ready, 3 gaps | Xuất kế hoạch 4+3, không sinh ba bài giả |
| SERP-05 | Primary proposed có Volume cao hơn | Cần approval, giữ original primary |
| SERP-06 | Không có WordPress connector | App không gọi WP, không khẳng định không trùng trên website bên ngoài |
| SERP-07 | Người dùng Reject proposal | Lưu lý do và không tự lặp lại cùng proposal không có bằng chứng mới |
| SERP-08 | Edit proposal với `expected_version` cũ | Trả 409 conflict |

## E. Brief & Writing Strategy (F7)

| ID | Scenario | Expected |
|---|---|---|
| BR-01 | Brief tool/Excel/download | Không xuất như ARTICLE brief chính thức |
| BR-02 | Chưa duyệt primary change | HOLD brief official; có draft cảnh báo nếu cần |
| BR-03 | Overview `P1` nhưng detail `P0` | Phát hiện mâu thuẫn trước export |
| BR-04 | Writing Strategy có công thức H2-specific | Test fail, loại bỏ mapping này |
| BR-05 | WritingStrategy có chính 1, phụ tối đa 2, tactics 3–6 | PASS cấu trúc |
| BR-06 | Mở bài không trả lời ngay câu đầu | Không tự fail; chỉ xem có đáp ứng intent không |
| BR-07 | Thông tin thuế hoặc BHXH không nguồn/ngày áp dụng | HOLD nguồn, không bịa |
| BR-08 | URL internal link mới chưa được xác minh | Ghi PLANNED/UNVERIFIED, không coi đã live |
| BR-09 | Export XLSX 3 logical tables | File tải được, header/giao diện đúng, overview/detail đồng bộ |
| BR-10 | Không có tài khoản Google | Vẫn export local thành công |

## F. Hardcode / adapter bans

- Quét mã nguồn nghiệp vụ, grep các chuỗi `P01`, `lương`, `gross`, `Google Sheets`, `gid=`, các spreadsheet IDs. Những chuỗi này chỉ được xuất hiện trong docs/test/fixture; không có branch logic theo topic.
- Không import Google SDK, Semrush SDK, WordPress SDK trong runtime dependencies. Không yêu cầu MCP installed.
- V0.1 DEMO/MOCK phải chạy 100% offline; ở chế độ provider cloud không gọi API trước khi user cho phép.
- Thử tạo topic mới `P99` bất kỳ từ UI và chạy planner mà không sửa code.

## G. Data provenance QA

- 100% user seed row được đối chiếu với snapshot, không mất hàng.
- Mọi quyết định có `reason_codes`, `evidence_refs`, `rule_version`.
- Mọi file import có SHA-256 và uploader metadata; raw rows immutable.
- Không có số liệu thực bị tạo từ model; missing != 0.
- Kết quả AI không trở thành APPROVED mà không có click user lưu audit.

## H. Reporting

Sau mỗi milestone: Codex ghi số tests passed/failed, commands đã chạy, lỗi chưa xử lý, trạng thái phần đang MOCK; không giả vờ kết nối Google/Semrush/WordPress.


## I. V1.3 Local Workbench GUI & Event Assertions

| ID | Scenario | Expected |
|---|---|---|
| UX-01 | Không có dự án | Empty state, CTA tạo dự án/nạp demo, 7 bước sau blocked |
| UX-02 | User nạp demo P01 có chủ đích | Badge DEMO, các bước phản ánh dữ liệu mock, không giả Semrush metrics |
| UX-03 | Tạo Topic mới không phải P01 | Không chứa nhóm Gross/Net mặc định; mọi request mới lấy seed nhập tay |
| UX-04 | ResearchRequest chờ file | `WAITING_USER`, không có `RUNNING`; nút Sao chép hướng dẫn/Gửi file |
| UX-05 | Upload file nhưng chưa confirm | `MAPPING_REQUIRED`; metrics chưa được tính vào observations |
| UX-06 | Confirm import đúng request | Request chuyển IMPORTED; dashboard số file tăng; journal ghi event |
| UX-07 | File CSV sai header | Cho mapping thủ công; không auto đi tiếp |
| UX-08 | XLSX có nhiều sheet | Bản thật chọn sheet; prototype cảnh báo active-sheet-only |
| UX-09 | Thiếu Volume/KD | Warning + next action; null giữ nguyên, không coi thành 0 |
| UX-10 | Có 3 SERP URLs | Status REQUIRES_REVIEW, không nhận top10 |
| UX-11 | Approval chưa duyệt | Không phát hành official brief; Reject giữ keyword nguồn |
| UX-12 | Người dùng refresh | Bản thật resume từ DB, demo resume metadata qua localStorage |
| UX-13 | Tác vụ không có progress quantifiable | Chỉ spinner + operation, không % giả |
| UX-14 | Import lỗi | ERROR, mã lỗi, retry; giữ raw file cũ trong bản thật |
| UX-15 | Phiếu thứ ba bên ngoài có tên menu khác | Hướng dẫn mang tính tương đương, không giả UI điều khiển được Semrush |
| UX-16 | Xuất báo cáo trạng thái | Download JSON từ thao tác thật |

**Smoke test UI prototype:** `python prototype/tests/test_ui_smoke.py` trong môi trường có Playwright + Chromium. Đây là test **giao diện demo**, không thay thế end-to-end tests của ứng dụng Next.js/FastAPI.


## V1.4 Input File / Bản đồ nhu cầu QA
- Upload original FinZ XLSX (taxonomy header row4, Keywords row1) → 25 valid topics, 1 incomplete P26, 299 keywords, 63 codes.
- Upload normalized `fixtures/FINZ_TOPIC_IMPORT_READY.xlsx` → 25 valid topics, 299 keywords, 63 codes, no incomplete taxonomy in active table.
- Choose P01/P01.1 → primary original unchanged, 5 secondary; P01.2 likewise.
- Save P01 → 2 provisional SOURCE_GROUP; no automatic claim that there are 2 Search Intents / 2 ready articles.
- Switch P01 → P08 without code change, clear audience/business goal while updating taxonomy & seed.
- Generic Z42 fixture with header row4 passes without a P01-specific rule.
- Missing topicType / mainTopics → HOLD/REVIEW, do not invent.
- Test separate Topic Pillar CSV and Keywords CSV; note upload is only local.
- No Google, Semrush or WordPress API calls.
