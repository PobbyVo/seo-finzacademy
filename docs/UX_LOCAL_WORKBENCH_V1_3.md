# SEO WORKBENCH V1.3 — UI/UX SPEC (LOCAL, HUMAN-IN-THE-LOOP)

**Trạng thái:** đặc tả thiết kế để Codex triển khai. Thư mục `prototype/` là bản giao diện tương tác DEMO, không phải SEO engine hoàn chỉnh.

**Quyết định nền tảng:** người dùng có quyền sử dụng Semrush qua giao diện của bên thứ ba; không có Semrush API/MCP hoặc quyền truy cập tự động. Ứng dụng CHỈ cung cấp phiếu hướng dẫn thao tác bên ngoài, nhận tệp được xuất thủ công và phân tích dữ liệu có nguồn. Google Sheets và WordPress cũng không nằm trong luồng.

## 1. Công việc chính mà giao diện phải giải quyết

Người dùng phải trả lời được năm câu hỏi tại mọi thời điểm:

1. **Tool đang ở bước nào?** Stepper ghi số thứ tự, tên, trạng thái và thời điểm cập nhật.
2. **Nó đang làm gì?** Tác vụ nền (nếu có) hiển thị thao tác hiện tại, số dòng đã xử lý nếu đo được, nhật ký sự kiện; không dùng phần trăm giả.
3. **Vì sao bị dừng?** Blocker nêu nguyên nhân, dữ liệu thiếu, mức ảnh hưởng và trường hợp có thể xử lý.
4. **Tôi cần làm gì?** Một primary next action đặt cạnh blocker, ví dụ `Mở phiếu Semrush`, `Chọn file`, `Ánh xạ cột`, `Duyệt keyword chính`.
5. **Bấm tiếp có làm mất dữ liệu không?** Lưu snapshot, có phiên bản, cảnh báo khi đổi Topic Pillar/seed hoặc import trùng.

Mọi trạng thái phải được tính từ dữ liệu & event thực, **không** được tự hiện DONE khi UI mới render xong. Không tự chuyển task `WAITING_USER` sang `RUNNING` khi người dùng đang thao tác Semrush bên ngoài.

## 2. Information architecture

```
Workbench (Dashboard / tổng quan)
  01. Thiết lập dự án và taxonomy
  02. Nhóm nhu cầu & đề xuất keyword (Topic Opportunity Map)
  03. Phiếu yêu cầu Semrush — thao tác bên ngoài
  04. Nhận file — upload → preview → map → confirm
  05. Kiểm tra dữ liệu — F1–F4 & khoảng trống
  06. SERP Evidence — nhập URL hoặc import organic results
  07. Kế hoạch bài viết — demand clusters → article opportunities
  08. Content Brief — Writing Strategy & xuất local
  Hàng chờ duyệt — cross-cutting
  Nhật ký & lịch sử — cross-cutting
```

Điều hướng hiện ở sidebar. Bấm vào bước chưa mở khóa chỉ cho phép xem **lý do bị chặn** và nút quay lại dữ liệu cần nhập, không tạo dữ liệu giả.

## 3. Layout desktop & responsive

### Desktop 1440px

- Sidebar tối 254px (dự án, menu theo quy trình, trạng thái nhỏ, nút reset demo).
- Topbar 67px (breadcrumb, nhãn LOCAL, nhãn MOCK/LIVE, thời điểm lưu, Hướng dẫn).
- Main max-width 1530px; dashboard có grid hai cột: workflow ở trái, blockers/activity bên phải ~300px.
- Hàng KPI: `Completed steps`, `Waiting on me`, `Review required`, `Imported reports`.
- Hero next-action: **một việc quan trọng nhất**, CTA dẫn đúng nơi người dùng có thể hoàn thành.
- Stepper 8 bước luôn cho biết `DONE/WAITING/REVIEW/BLOCKED`, có click để inspect.

### Tablet/moblie

- Sidebar thu gọn icon; trên mobile ẩn nhãn để còn không gian thao tác.
- Dashboard, upload form, source mapping xếp một cột.
- Table dữ liệu scroll ngang; không tự ẩn cột nguồn gốc và trạng thái.
- File input hoạt động với keyboard, click và drag/drop.
- Kích thước click tối thiểu ~38px, contrast đủ rõ, có label/aria-live cho loading/toast.

## 4. BẢNG TRẠNG THÁI CHUẨN

| Trạng thái | Ai kích hoạt? | Khi nào dùng? | CTA phù hợp | Có đi tiếp tự động không? |
|---|---|---|---|---|
| `NOT_STARTED` | System | Chưa nhập | Bắt đầu | Không |
| `READY` | System | Đã đủ điều kiện để chạy | Chạy phân tích | Chỉ khi user bật auto cho bước an toàn |
| `RUNNING` | Worker | Đang phân tích/upload/validate | Xem chi tiết hoặc Hủy nếu an toàn | Khi job kết thúc |
| `WAITING_USER` | System | Người dùng cần thao tác Semrush/UI | Sao chép checklist, upload | Không |
| `FILE_RECEIVED` | Upload | Đã nhận file, chưa confirm | Xem trước | Không |
| `MAPPING_REQUIRED` | Validator | Header thiếu/lệch tên | Ghép cột | Không |
| `VALIDATING` | Worker | Kiểm tra file & metrics | Xem tiến trình | Khi job kết thúc |
| `REVIEW_REQUIRED` | Rule/AI | Quyết định thay primary/nhánh mới | Duyệt / Bác bỏ | Không |
| `HOLD` | Gate | Thiếu evidence/quy tắc quan trọng | Xem dữ liệu cần bổ sung | Không |
| `DONE` | Backend | Job/gate hoàn thành | Xem kết quả | Có thể mở step kế |
| `ERROR` | Backend | File/worker/network lỗi | Xem chi tiết / Thử lại | Không |
| `SKIPPED` | User có quyền | Bước tùy chọn được bỏ qua có lý do | Xem lý do | Chỉ nếu policy cho phép |

**Lưu ý:** `DONE` cho bước nhập file không đồng nghĩa `PASS` của SEO gate. Trạng thái workflow, trạng thái import và trạng thái SEO gate phải lưu tách biệt (xem `STATE_MACHINE_AND_EVENTS.md`).

## 5. Màn hình A — Workbench Overview (home)

Hiển thị ngay khi chọn một Project:

1. Hero `Việc cần làm tiếp theo`. Nếu chưa có dữ liệu Semrush: `Bạn cần xuất Keyword Overview cho <seed>`; CTA `Xem phiếu yêu cầu`.
2. Stepper 8 mục có trạng thái và lời giải thích một câu.
3. Cột phải `Điểm nghẽn hiện tại`: ví dụ `2 phiếu chưa upload`, `chưa có SERP URL`, `1 đề xuất keyword chính chờ duyệt`.
4. Timeline 5 event mới nhất: `Người dùng đã tạo yêu cầu`, `Đã chọn report`, `Đã xác nhận import`, `F1 HOLD`, `Người dùng approve`.
5. Nhãn môi trường `LOCAL`, trạng thái AI `MOCK / PROVIDER READY`, không hiện `Semrush connected`.
6. Action `Xuất báo cáo trạng thái JSON` để debug/share với Codex mà không cần tài khoản ngoài.

**Quy tắc next action:** xác định từ blocker có tính phụ thuộc cao nhất. Ví dụ nếu 1 file còn `MAPPING_REQUIRED`, ưu tiên `Ghép cột` thay vì `Tạo brief`. Không có hai primary CTA cạnh tranh nhau.

## 6. Màn hình B — Project Setup (form đầy đủ)

**A. Dự án:** name, business goal, target audience, country/locale, language, target article min/max (soft), allowed content type=ARTICLE.

**B. Taxonomy:** Pillar, Topic Code, Topic Name, `Loại topic`, `Trục chia của pillar`, `Chủ đề chính bên trong`, notes. Phải nhập đủ các trường đặc trưng nguồn đã duyệt; không hardcode P01.

**C. Nguồn keyword:** content code, nội dung gốc, primary, secondary multiline, nguồn (`USER_FORM`) và snapshot.

CTA: `Lưu dự án và tiếp tục` — tạo snapshot; sửa nội dung sau đó tạo version. Nếu đổi Topic Pillar khi đã có file nhập, phải hỏi xử lý dự án mới/mapping chứ không tự chuyển gán file sang topic khác.

## 7. Màn hình C — Topic Opportunity Map

- **Đơn vị hiển thị là nhu cầu tìm kiếm**, không phải keyword thô.
- Mỗi card: tên nhóm, nhu cầu, các seed gốc, các seed đề xuất, mối liên hệ taxonomy, code nội dung, `CORE / NEW_WITHIN_PILLAR / CROSS_PILLAR / BOUNDARY`, nguồn evidence, trạng thái duyệt.
- Filter theo status và nguồn. Mọi AI suggestion có `reason`, `source_ref_ids` backend xác minh được, `is_verified=false` khi chưa có Semrush.
- Buttons: `Cho vào danh sách nghiên cứu`, `Chờ duyệt`, `Không nghiên cứu` với audit. Không tự sửa primary nguồn.
- **Prototype:** nhóm mẫu ghi `DEMO` và nhóm do người dùng thêm ghi `USER_FORM`; KHÔNG tuyên bố có AI thật.

## 8. Màn hình D — Semrush Research Center (quan trọng nhất)

User vẫn dùng **Semrush UI của bên thứ ba** như bình thường. Tool hoàn toàn không đăng nhập, không gọi API, không tìm cách can thiệp giao diện bên thứ ba.

Một **Research Request** phải hiển thị:

| Trường UI | Giải thích cho người vận hành |
|---|---|
| Request ID | Gắn file đúng nhiệm vụ, ví dụ `RQ-001` |
| Demand Group / Seed | Từ khóa cần nhập trong Semrush |
| Report type | Keyword Overview, Keyword Magic/Related, Questions, Organic Results nếu có |
| Market / Database | Quốc gia/ngôn ngữ đã chọn, không tự suy luận |
| Required fields | `Keyword`, `Volume`, `KD`, `Intent`, `SERP Features` tùy report |
| Why needed | Muốn kiểm chứng điều gì và bước nào sẽ sử dụng dữ liệu |
| Detailed instructions | 5–7 bước thao tác **mang tính tương đương**, tên menu có thể khác |
| Expected file name | Ví dụ `RQ-001_keyword-overview_vn.csv`, không hardcode bắt buộc |
| Request Status | `WAITING_USER`/`MAPPING_REQUIRED`/`IMPORTED`/`ERROR` |
| Actions | Sao chép hướng dẫn, Gửi file, Xem data/error, Lặp lại nghiên cứu |

**Hướng dẫn Semrush UI mẫu:**

1. Mở giao diện Semrush của bạn (không phải bên trong tool).
2. Tìm tính năng tương đương `Keyword Overview` hoặc `Keyword Magic Tool`.
3. Nhập chính xác seed và chọn database/thị trường được ghi trên phiếu.
4. Chọn báo cáo phù hợp `Overview`, `Related`, `Questions`... nếu giao diện có.
5. Kiểm tra file sẽ có các cột cần thiết. Nếu có cột khác thì vẫn xuất rồi quay lại mapping.
6. Export CSV/XLSX. Không cần đăng nhập/đưa mật khẩu Semrush vào SEO Workbench.
7. Quay lại phiếu `RQ-...`, chọn file đúng report, preview/mapping/confirm.

**Không vẽ nút “Run Semrush”, “Connect Semrush”, “Open Semrush MCP”, “Sync”.**

### Evidence gap loop

- Thiếu `Volume/KD` → request đo metrics, không tự tạo Topic mới.
- Keyword có intent không tương thích với `ARTICLE` → yêu cầu SERP/type evidence, không đoán từ SERP Features.
- Topic coverage thiếu → tạo seed/nhánh mới sau taxonomy checks, chưa tự approved.
- Nếu chỉ có 4 bài có căn cứ và 3 khoảng trống, công bố `4 ready + 3 needs research` thay vì ép 7.

## 9. Màn hình E — Upload Workbench

**Khối 1:** chọn Research Request (bắt buộc), report kind, keyword seed, market/locale, ngày export.

**Khối 2:** upload CSV/XLSX; size/type/extension/MIME constraints; progress `reading/validating` (spinner và byte count nếu có thật). Hiển thị tên, size, SHA-256, sheet name. Chọn workbook tab nếu XLSX nhiều sheet (bản thật).

**Khối 3:** preview 20 dòng, ánh xạ cột bắt buộc và tùy chọn, có override. Ví dụ `KD % → kd`, `Search Volume → volume`.

**Khối 4:** preview kết quả normalize gồm raw value và parsed value, chẳng hạn `9.900` `vi-VN` thành 9900; `9,900` nếu mơ hồ phải REVIEW, không nhập thành số tùy tiện. `null` khác 0.

**Khối 5:** `Confirm Import`. Chỉ khi xác nhận backend mới ghi observation chính thức. Trước confirm request là `MAPPING_REQUIRED` hoặc `FILE_RECEIVED`.

Nếu upload nhầm: `Hủy` xóa bản chờ, KHÔNG xóa batch đã duyệt cũ. Nếu upload cùng file lần nữa: phát hiện checksum và hỏi tránh duplicate.

Error panel theo bảng: `Row/Column/Raw Value/Issue/Next Action` có action xuất lỗi. Không âm thầm bỏ hàng.

## 10. Màn hình F — Data Quality & Evidence Gaps

- Summary counts: rows, valid metrics, `null` Volume, `null` KD, conflicting observations, report/market mismatch, `READY_FOR_SERP` count.
- Chi tiết từng report có status F1/F2 và nguồn metadata.
- Gate cards có `finding → impact → next action`.
- Tabs `File Observations / Conflicts / Missing Data / Research Requests`.
- Buttons `Tạo yêu cầu bổ sung`, `Xem raw source`, `Duyệt xử lý xung đột`.

Không “tổng Volume” bằng cách cộng các biến thể trùng nhu cầu. Không thể kết luận article form chỉ từ `Intent: Informational`.

## 11. Màn hình G — Manual SERP Evidence

- Form keyword, market, locale, device, timestamp, position, title, URL, snippet, page type, source, verification status.
- Nếu người dùng có organic results file, nhập qua parser riêng; nếu không có, nhập từng URL hoặc dán bảng.
- Coverage hiển thị `observed 3/10` khi có 3 URL hợp lệ, **không** báo Top 10 analyzed.
- Page Type: `ARTICLE/TOOL/DOWNLOAD/PRODUCT/SERVICE/UNKNOWN`.
- Không dùng WordPress; kiểm tra trùng chỉ dựa trên nội dung nội bộ app; có thể cho nhập danh sách URL hiện hữu thủ công nhưng là tùy chọn.

## 12. Màn hình H — Article Opportunities & Approval Queue

- Bảng theo Demand Groups, `proposed_primary`, secondary list, page type, source, SERP coverage, metrics, approval status, reason.
- Primary keyword mới phải tạo ChangeProposal; không sửa source primary.
- Nhánh mới trong Topic Pillar cũng cần duyệt nếu chưa nằm trong kế hoạch.
- Filters `READY_FOR_BRIEF`, `REVIEW`, `HOLD`, `OUT_OF_SCOPE`.
- Block official brief khi có approval pending, chủ đề chưa đủ evidence hoặc loại trang không phải ARTICLE.
- Hiện thông báo rõ `Không đối chiếu nội dung website ngoài ứng dụng`.

## 13. Màn hình I — Brief Builder & Export

- Dùng ba bảng logic `Keyword Overview / Keyword Mapping / SEO Content Brief`, nhưng export local XLSX/CSV/JSON/print HTML; không kết nối Google.
- Brief toàn bài: mục tiêu, độc giả, SEO metadata, nguồn, outline H2/H3, internal link (planned hoặc verified), CTA, review.
- Writing Strategy: 13 công thức + 16 chiến thuật, một công thức chính, tối đa hai bổ trợ, 3–6 tactic gợi ý ở **cấp toàn bài**; không gán vào mỗi H2. Có thể mở bài kiểu kể chuyện/tò mò khi phục vụ search intent, không bắt buộc answer-first.
- `Xem bản nháp` có dấu `DRAFT`; `Xuất chính thức` bị vô hiệu hóa khi F7 HOLD, hiển thị lý do và CTA tới nguồn còn thiếu.

## 14. Async & observability khi build engine thật

- Một `WorkflowRun` có `run_id`, `project_id`, `step_id`, `status`, `progress_current`, `progress_total`, `progress_unit`, `started_at`, `updated_at`, `blocked_by`, `next_action`.
- Backend emit event; frontend dùng SSE hoặc polling để cập nhật mà không giả vờ “đang phân tích” khi thực ra đang chờ user thao tác Semrush.
- Nếu không đo được tiến độ, hiển thị **spinner + tên operation**, không show 45%/78% giả.
- Khi server reload hoặc trình duyệt đóng, mở lại project sẽ query trạng thái worker và resume ở bước phù hợp. Không mất status hay file đã confirm.
- Jobs có lỗi cho phép retry; retry không làm mất upload raw, idempotent theo run id và content hash.
- Approval có version concurrency; không tự ghi APPROVED từ AI.

## 15. Prototype hiện có — các thao tác thật và giới hạn

Trong `prototype/`: `index.html`, `styles.css`, `app.js`, `server.py`.

**Đã tương tác được:** nav + stepper, form tạo dự án, nạp demo P01, xem nhóm nhu cầu, thêm nhóm, tạo phiếu Semrush, copy checklist, upload CSV/XLSX, preview & mapping, confirm import, phân tích completeness kỹ thuật mẫu, nhập SERP từng URL, approve/reject demo, xem blockers + activity, xuất trạng thái JSON. Giao diện lưu trạng thái trong localStorage; file upload gốc không được lưu bền vững trong prototype.

**CHƯA làm và tuyệt đối không tuyên bố đã làm:** phân tích AI thật; gọi Semrush; xử lý toàn bộ file lớn; xlsx multi-tab picker; full raw-file provenance/SHA256; kiểm chứng SERP hoặc nội dung website; Mapping & Brief SEO chính thức; xuất XLSX Content Brief. Những việc này thuộc các milestone triển khai bằng Codex theo tài liệu.

**Xem giao diện:**

```sh
cd prototype
python -m pip install -r requirements.txt
python server.py 5173
# mở http://127.0.0.1:5173
```

`python` là Python 3.10+; server bind `127.0.0.1` và chỉ phục vụ máy local. Không cần tài khoản, API key hay connector. Nếu mở HTML trực tiếp, CSV có fallback, nhưng XLSX cần server Python.

## 16. Định nghĩa hoàn thành trước khi bàn giao Codex

- Khi chọn P01 hoặc topic tự nhập bất kỳ, không cần thay code logic.
- Dashboard phản ánh **đúng** thao tác và trở ngại hiện tại sau reload.
- Các thao tác Semrush đều là **công việc giao cho người dùng**; không có nút giả chạy API.
- Từng phiếu file có report/market/seed và upload/link đúng ID; nhầm phiếu phải có cơ chế sửa.
- Chưa map/confirm không ảnh hưởng số liệu và gate.
- Khả năng nhập file `CSV/XLSX` phải hoạt động trong app thật, có sheet picker và locale validation.
- Có thể dừng, xem lỗi, retry và tiếp tục dự án không mất dữ liệu.
- Approval đã lưu trong DB, có timestamp/reviewer/version.
- BRIEF không xuất chính thức khi thiếu evidence/approval.
- Manual workflow vẫn phục vụ P02/P08/P25 hoặc một ngành hoàn toàn khác, không chỉ 'Lương'.
