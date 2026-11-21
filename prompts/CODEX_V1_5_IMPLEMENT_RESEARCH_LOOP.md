# Prompt giao Codex hoàn thiện V1.5

Bạn là full-stack engineer + SEO systems architect. Đọc `AGENTS.md`, `docs/V1_5_DB_AI_RESEARCH_LOOP.md`, `docs/SPEC_FULL.md`, `prototype/README.md` trước khi sửa code. Đây là **repo V1.5 đã có source**, không scaffold dự án khác.

## Hiện trạng đã có

- `prototype/server.py`: local HTTP endpoints
- `prototype/persistent_store.py`: SQLite state/projects/import rows/AI runs
- `prototype/evidence_engine.py`: full-file manual Semrush CSV/XLSX parsing + metric provenance
- `prototype/ai_demand_engine.py`: optional OpenAI-compatible LLM cho Analyst + Critic; không gọi Semrush/Google/MCP
- `prototype/app.js`: nút UI dùng SQLite, AI Research và full-file uploads

## Việc cần làm tiếp theo, theo thứ tự

1. Đọc và chạy toàn bộ tests. Chỉ sửa lỗi được kiểm chứng, không tự xóa dữ liệu cũ của người dùng. Đảm bảo migration từ V1.4 localStorage sang SQLite không tạo project trùng ID.
2. Xây UI multi-project hoàn chỉnh (tạo/sửa/nhân bản/chuyển Topic Pillar, nhập toàn bộ keyword của các mã), tránh mất dữ liệu khi đổi scope. Thêm DB revision conflict guard và backup/restore.
3. Xây workflow state machine rõ `WAITING_USER`, `RUNNING_AI`, `RESEARCH_REQUIRED`, `METRICS_AVAILABLE`, `SERP_REQUIRED`, `REVIEW`, `HOLD`; tách `PROCESS_COMPLETED` khỏi `QUALITY_APPROVED`.
4. Hoàn thiện Semrush import: chọn tab XLSX, header aliases, full-file warnings, locale ambiguity, snapshot/source hash, idempotency, xử lý Organic Results khi export thiếu cột Keyword (gắn seed của Research Request sau khi xác minh), error recovery. **Không kết nối API/MCP Semrush.**
5. Hoàn thiện API LLM cho Ollama / OpenAI-compatible: strict typed Pydantic schemas, validation JSON, retries giới hạn, timeout, error UI; kiểm tra mọi `source_ref` bằng DB, thêm một Critic kiểm tra phản biện độc lập. Không đưa thông tin nhạy cảm cho provider bên ngoài khi chưa xin consent người dùng.
6. AI Research Request generator dựa vào `taxonomy + gap`, tránh hỏi lại báo cáo đã có, ưu tiên các seed thiếu bằng chứng. Tạo hướng dẫn thao tác Semrush theo loại báo cáo, VN locale và cột cần export. Cho phép người dùng chọn và xác nhận từng phiếu.
7. AI Critic sau mỗi lần import: kiểm tra phạm vi taxonomy, business intent, metrics, SERP/page type, nguy cơ cannibalization; trả các action `MORE_RESEARCH` / `SERP_REVIEW` / `HUMAN_REVIEW`. Không tự đánh dấu READY_FOR_BRIEF chỉ vì đủ Volume/KD.
8. Xây unit tests và Playwright integration cho P01, P02, P08, P25, và chủ đề không liên quan như P99. Chạy thực test, không ghi PASS nếu chưa test.

## Ràng buộc

- Bỏ Google Sheets/WordPress APIs khỏi runtime. Dữ liệu đi qua form và local files.
- Không hardcode P01 hoặc một mức KD/Volume toàn cục để loại tự động; ưu tiên giá trị kinh doanh và sự khác biệt về intent.
- Giữ file raw immutable, source provenance, trạng thái duyệt của người dùng.
- Không thay keyword chính gốc không qua approval.
- Không ép đủ 5–7 bài và không nhập TOOL/EXCEL vào ARTICLE quota.
- Writing Strategy cấp toàn bài, không gán vào H2.
- Giải thích mọi lỗi bằng tiếng Việt, có bước xử lý tiếp theo.

## Kết quả yêu cầu

Tổng hợp từng file đã sửa, các API/UI đã test, bảng PASS/FAIL thật, ảnh chụp màn hình local (nếu môi trường cho phép), và những rủi ro/việc còn lại. Không tự deploy, không push git, không cài Semrush MCP.
