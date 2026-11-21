# UI / UX DESIGN — MANUAL WORKFLOW V1.2 (REFERENCE)

> **SUPERSEDED FOR UI by V1.3:** `docs/UX_LOCAL_WORKBENCH_V1_3.md` and `docs/STATE_MACHINE_AND_EVENTS.md` are authoritative for workflow status, blockers, Semrush Request Center and local UI. Keep this V1.2 document as background only.

## Guiding principles

Người dùng có thể không giỏi SEO. Mọi bước cần giải thích **Tại sao cần dữ liệu? Cần thao tác gì? File nào cần upload? Kết quả có đủ tin cậy chưa?**

Không dùng một form khổng lồ trong onboarding. Wizard lưu draft và hiển thị trạng thái đã hoàn tất.

## 1. Sơ đồ điều hướng

```text
Dashboard
  └── Project
      ├── (1) Setup & Taxonomy [FORM]
      ├── (2) Original Keywords [FORM]
      ├── (3) Topic Opportunity Map [AI / MOCK]
      ├── (4) Approval Queue
      ├── (5) Semrush Research Requests
      ├── (6) Semrush File Upload [FORM + FILE]
      ├── (7) Keyword Analysis / Issues
      ├── (8) SERP Evidence Upload [FORM + FILE]
      ├── (9) Article Plan & Mapping
      ├── (10) SEO Content Brief
      └── (11) Export / Print
```

## 2. Project Setup Wizard

### Step A: Project

- `Project name*`, `Business goal*`, `Target audience*`, `Market (Country/Language/Locale)*`, `Research mode*`, `Target article count min/max`, `Domain (optional metadata)`.
- Show inline “Mục tiêu 5–7 bài là mục tiêu mềm”.
- CTA `Lưu dự án và tiếp tục`.

### Step B: Taxonomy

- Thẻ Pillar: `Pillar name*`, `Pillar code (optional)`, `Description (optional)`.
- Thẻ Topic Pillar: `Mã*`, `Topic pillar*`, `Pillar*` (select Pillar đã nhập), `Loại topic*`, `Trục chia của pillar*`, `Chủ đề chính bên trong*` (chips/tokens + textarea), `Ghi chú`.
- Sidebar hiển thị taxonomy tree, có nút `Thêm Topic Pillar`, `Nhân bản`, `Chọn topic nghiên cứu`.
- Không có “Connect Google” hoặc “Đồng bộ Sheet” ở bất kỳ màn nào.

### Step C: Content & Seeds

- Block `Mã nội dung*`, `Tên chủ đề nội dung*`, `Ý định nội dung gốc*`, `Bài gốc/tiêu đề dự kiến`.
- Table keyword với `Key*`, `Loại Chính/Phụ*`, `Giai đoạn`, `Ghi chú`, `Mã nội dung`. Có `+ Thêm dòng`, paste newline-to-rows, `Lưu bản nháp`.
- Banner: “Đây là dữ liệu do bạn nhập; các số liệu SEO chưa được kiểm chứng”.

## 3. Topic Opportunity Map

- Top summary: `N nhóm nhu cầu`, `M seed gốc`, `K seed được AI đề xuất`, `L cần duyệt`, `0 đã đo`.
- Body là **cards demand groups** có `user_need`, `source_topic`, `why_relevant`, `original seeds`, `proposed seeds`, `potential overlap`, `scope status`, `evidence links`.
- Filters: CORE / SAME_TOPIC / NEW_WITHIN_TOPIC / CROSS_TOPIC / UNCERTAIN.
- Action `Chấp nhận để nghiên cứu`, `Đưa vào xem xét`, `Không nghiên cứu`, lý do optional; không auto sửa keyword gốc.
- Chế độ AI `MOCK` có banner rõ, chỉ dùng fixture cho demo.

## 4. Semrush Research Requests

- Danh sách mỗi request có `request ID`, seed, mục tiêu, report cần mở, market, required columns, trạng thái.
- CTA `Sao chép hướng dẫn`, `Gắn file đã xuất`, `Tạm bỏ qua`, `Đã xử lý` (có validation).
- Không giả vờ truy vấn Semrush hay có nút “Run Semrush”.
- Có progress theo `WAITING_FOR_UPLOAD`, `FILE_SELECTED`, `MAPPING_REQUIRED`, `READY_TO_CONFIRM`, `IMPORTED`, `ERROR`.

## 5. Upload file — màn hình quan trọng nhất của V0.2

Khu vực ba cột hoặc stepper:

1. **Báo cáo**: chọn request; report kind; keyword seed; geo VN/khác; thời điểm; CSV separator/encoding hoặc XLSX tab.
2. **Upload**: kéo thả file .csv/.xlsx, size limit; hiển thị name/size/hash, sample 20 rows, cảnh báo dữ liệu không đáng tin.
3. **Mapping & Confirm**: tự gợi ý mapping cột, user sửa; hiển thị ví dụ số parsed theo locale; warn missing; bấm `Xác nhận import`.

Bảng lỗi cụ thể: `Row`, `Column`, `Raw value`, `Issue`, `Next action`; cho tải danh sách lỗi CSV. Không âm thầm bỏ dòng.

## 6. Keyword Analysis, SERP, Article Plan

- Keyword Analysis: tách evidence original vs observations vs AI inference; hiển thị trạng thái PASS/REVIEW/HOLD/OUT_OF_SCOPE và next action.
- SERP form: chọn keyword, geo/date/device, cho thêm result rows position/url/title/snippet/page type; hoặc upload CSV/XLSX organic results; hiển thị coverage. Không có WordPress step.
- Article Plan: bảng `N Ready`, `M Review`, `K Hold`, `G gaps`; nhu cầu/chùm từ khóa, primary proposal, secondary, proposed URL, intent, evidence, approval. Warning: “Không kiểm tra trùng trên website bên ngoài”.

## 7. Brief Builder & Export

- Overview table với `Mã bài`, `Tên bài`, `Loại`, `Ưu tiên`, `Trạng thái`, `Keyword chính`, `Volume`, `URL`, `Mở brief`.
- Detailed Brief: SEO fields + audience/goal + SEO title/H1/meta + keywords + H2/H3 and content requirements + `Writing Strategy` cấp toàn bài.
- Card `Writing Strategy`: primary framework + why, up to 2 supporting frameworks, 4U title guidance, 3–6 tactics global, 1–2 intro options; chip “Content được quyền điều chỉnh”. Tuyệt đối không gắn tactics vào H2.
- Action `Xem trước`, `Tải XLSX`, `Tải JSON`, `Tải CSV`, `In/PDF qua trình duyệt`. Không Google Sheets connect/export.
- Nếu thiếu evidence: `Xem bản nháp` có watermark DRAFT; `Xuất brief chính thức` disabled và có reason code/next action.

## 8. UX quality

- Giao diện tiếng Việt, giải thích thuật ngữ SEO trong tooltip (Volume, KD, Intent, SERP, Pillar).
- Tất cả action có phản hồi thật; không thiết kế button chỉ để minh họa trong production.
- Progress state hiển thị rõ cho việc upload, phân tích AI, approval và file export.
- Không dùng mẫu P01 khi tạo dự án mới trừ khi user chọn `Nạp dữ liệu demo`.
- Desktop-first nhưng responsive; contrast/keyboard/labels rõ.
