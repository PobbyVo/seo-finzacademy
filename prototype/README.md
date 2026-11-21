# SEO WORKBENCH — LOCAL INTERACTIVE UI DEMO V1.4

Đây là bản **giao diện mẫu có nút và trạng thái hoạt động**; chưa phải sản phẩm SEO hoàn chỉnh.

## Chạy trên Windows (VS Code / PowerShell)

1. Cài Python 3.10+.
2. Giải nén ZIP, mở thư mục `finz-seo-assistant/prototype` trong VS Code.
3. Mở Terminal và chạy:

```powershell
py -m pip install -r requirements.txt
py server.py 5173
```

4. Mở `http://127.0.0.1:5173` trên trình duyệt của bạn.

Nếu máy dùng `python` thay vì `py`, thay tương ứng. Nếu cổng 5173 bị chiếm, chạy `py server.py 5174`.

## macOS / Linux

```sh
cd finz-seo-assistant/prototype
python3 -m pip install -r requirements.txt
python3 server.py 5173
```

Mở `http://127.0.0.1:5173`. Đóng Terminal bằng `Ctrl+C` để dừng server.

## Thử tính năng mới: upload bộ Topic Pillar + Keywords

1. Từ Google Sheets nguồn, chọn `File → Download → Microsoft Excel (.xlsx)` để tải nguyên workbook (không cần đăng nhập Google trong app). Hoặc dùng file sẵn `../fixtures/FINZ_TOPIC_IMPORT_READY.xlsx`.
2. Trong UI, vào `Thiết lập chủ đề` và bấm `Chọn file từ máy`.
3. Tool kiểm tra schema trong **cả hai tab** theo header, tự phát hiện ngay cả khi header ở dòng 4. Xem tổng số Topic Pillar, mã nội dung, keyword và cảnh báo.
4. Chọn Topic Pillar P01 hoặc bất cứ chủ đề nào. Chọn mã nội dung gốc P01.1-① / P01.2-② (hoặc mã tương ứng của chủ đề đã chọn).
5. Bấm `Điền thông tin vào form` → kiểm tra các trường → bổ sung **mục tiêu kinh doanh** và **độc giả** (không tồn tại trong workbook) → bấm `Lưu dự án`.
6. Mở `Bản đồ nhu cầu` → bấm `Tạo nhóm sơ bộ từ mã nội dung nguồn`. Đây là các **nhóm nguồn**, chưa xác minh Search Intent; cần Semrush/SERP để nghiên cứu tiếp.
7. Nếu thử đổi từ P01 sang P08, tool xóa mục tiêu và độc giả cũ để tránh sai phạm vi.
8. Import nguồn và upload báo cáo Semrush là **hai chức năng hoàn toàn khác nhau**, có endpoint riêng.

## 10 thao tác để tự kiểm tra giao diện

1. Bấm `Nạp dữ liệu minh họa` để nhìn trạng thái P01 hoặc nhập một topic khác ở `Thiết lập chủ đề`.
2. Mở `Tổng quan` kiểm tra bước, điểm nghẽn, việc cần làm tiếp theo.
3. Mở `Bản đồ nhu cầu`; đọc nhóm gốc vs nhóm giao thoa; tự thêm một nhóm nếu muốn.
4. Mở `Yêu cầu Semrush` và bấm `Sao chép hướng dẫn`. **Không có kết nối Semrush.**
5. Bấm `Gửi file đã xuất` ở phiếu RQ-001 rồi chọn `../fixtures/DEMO_NOT_LIVE_SEMRUSH.csv` (dữ liệu MOCK).
6. Kiểm tra các cột tự nhận diện: `Keyword`, `Search Volume`, `KD %`, `Intent`.
7. Bấm `Xác nhận nhập dữ liệu` để cập nhật trạng thái Request.
8. Trong `Kiểm tra dữ liệu`, bấm `Chạy kiểm tra file` để xem số dòng mẫu, thiếu Volume/KD.
9. Mở `Kế hoạch bài viết` để xem dự thảo với nhãn `SERP_NOT_VERIFIED`; không phải nhập URL thủ công.
10. Về `Tổng quan` kiểm tra trạng thái mới, nhật ký, blockers; `Xuất báo cáo trạng thái JSON` để xem trạng thái có thể lưu.

## Cái gì THẬT trong prototype?

- Các nút điều hướng, form, thêm nhóm, tạo phiếu, hướng dẫn Semrush, đọc CSV/XLSX bằng Python local, mapping cột, confirm import, kiểm tra completeness mẫu,  quyết định approval demo, nhật ký và JSON export.
- Khi chạy server, trạng thái và raw file đã upload lưu trong SQLite/thư mục local; localStorage chỉ là bản nháp dự phòng. Dữ liệu chưa xác nhận mất khi reload: cần upload lại.
- Không dùng API key, Google Sheets, WordPress hoặc Semrush MCP.

## Cái gì CHƯA CÓ?

- Phân tích AI thật, crawl SERP tự động, đánh giá keyword và dạng trang SEO thực sự, lưu toàn bộ file và bằng chứng, chọn nhiều sheet trong một XLSX **đối với Semrush**, Content Brief chính thức, xuất XLSX plan/brief, backup DB, worker SSE. `Content Brief` bị khóa trong demo là **cố ý**.
- CSV fallback hoạt động khi mở HTML trực tiếp, nhưng XLSX chỉ đọc khi chạy `server.py` cùng `openpyxl`.
- Import xác nhận đọc tối đa **25.000 dòng**, giao diện preview giữ tối đa 200 dòng. Sản phẩm chính thức phải xử lý đầy đủ file, kiểm tra SHA-256 và lưu immutable raw evidence trong SQLite.

## An toàn dữ liệu

- Local server chỉ lắng nghe `127.0.0.1`; file CSV/XLSX gửi tới **server local trên máy bạn**, không gửi cho Semrush hay AI cloud.
- Không upload dữ liệu nhạy cảm hoặc credential vào bản demo; localStorage không được mã hóa và có thể bị xóa khi xóa dữ liệu trình duyệt.
- Khi đưa sản phẩm vào sử dụng nội bộ, phải có kiểm thử bảo mật upload, version & permission thật trước khi lưu thông tin nhạy cảm.

## Tài liệu cho Codex

- `../docs/UX_LOCAL_WORKBENCH_V1_3.md` — đặc tả từng màn.
- `../docs/STATE_MACHINE_AND_EVENTS.md` — trạng thái, blocker, event, async.
- `../prompts/CODEX_BUILD_WORKBENCH_UI.md` — prompt yêu cầu Codex port prototype sang Next.js + FastAPI.

## Ghi chú V1.4

Topic import parser hoạt động trên server Python local (`topic_source_import.py`) và không cần AI. `P26` trong file nguồn chưa đầy đủ dữ liệu sẽ ở danh sách cảnh báo. Bản prototype chưa lưu raw XLSX vào DB, nên hãy giữ file gốc của bạn.

## V1.5 extension

The prototype now has SQLite persistence and optional live LLM Analyst/Critic endpoints. Use the Python server (not file://) for the SQLite functions. `persistent_store.py` holds project/workflow state and full imported Semrush rows; `evidence_engine.py` checks data quality and missing seed metrics; `ai_demand_engine.py` sends requests only to a user-configured OpenAI-compatible model endpoint. Read `../docs/V1_5_DB_AI_RESEARCH_LOOP.md` for the manual research loop, safety and limits. The system does not connect to Semrush/Google Sheets/WordPress APIs or MCP.

## Workflow UX & Validation Feedback (21/11/2026)

Bảy bước nghiên cứu; Chờ phê duyệt độc lập. Lưu SQLite thành công mới có popup PROCESS_COMPLETED; thiếu bằng chứng không thành QUALITY_APPROVED. Nút Ở lại/Escape hủy timer, đổi trang/dự án hủy popup. File preview chưa confirm không kích hoạt thành công import. Card lỗi nêu nguyên nhân, ảnh hưởng, giải pháp và CTA. Không xác minh intent/SERP hay tạo brief mới.

Chạy từ root (dùng Python 3.12 đã cài dependencies M0, thêm openpyxl nếu chưa có):

```sh
services/api/.venv/bin/python -m pip install -r prototype/requirements.txt
services/api/.venv/bin/python prototype/server.py 5173
```

Mở http://127.0.0.1:5173. `npm run dev` ở root vẫn chạy scaffold Next.js/FastAPI M0 tại 3000/8000; bản nâng cấp này ở Workbench V1.5.

Kiểm thử:

```sh
PYTHONPATH=prototype services/api/.venv/bin/python -m pytest prototype/tests/test_v15_backend.py prototype/tests/test_topic_source_import.py prototype/tests/test_workflow_feedback.py -q
npm --prefix e2e exec -- playwright test --config e2e/prototype.config.ts
```

Browser suite tự mở server 5193 với SQLite tạm, tắt AI, không sử dụng DB người dùng. Mặc định dùng Chrome đã cài; đặt PLAYWRIGHT_CHANNEL để chọn browser khác.
