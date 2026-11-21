# PROMPT ĐẦU TIÊN DÀNH CHO CODEX — M0

Hãy đóng vai Senior Full-stack Engineer và thực thi **chỉ Milestone M0** của sản phẩm FINZ SEO ASSISTANT V1.2 trong thư mục này.

**Bắt buộc đọc**: `AGENTS.md`, `docs/SPEC_FULL.md`, `docs/DATA_CONTRACTS.md`, `docs/UX_SCREENS.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/QA_AND_TESTS.md`.

**ĐIỀU KIỆN ĐÃ CHỐT, KHÔNG ĐƯỢC THAY:**
1. Không kết nối Google Sheets; dữ liệu Pillar, Topic Pillar, keywords sẽ nhập bằng form UI và lưu local DB.
2. Không kết nối Semrush Local bằng API/MCP; phiên bản tiếp theo chỉ import CSV/XLSX theo form + manual Research Request.
3. Không có bước WordPress nào, không kết nối/crawl/check WP.
4. Không hardcode `P01`, `Lương`, mã Google Sheet, domain FinZ vào nghiệp vụ. P01 chỉ là fixture cho DEMO.
5. Ứng dụng không cần bất cứ MCP nào để chạy. Phân biệt Codex dev tool với runtime integration.

**CHỈ PHẠM VI M0:**
- Tạo monorepo `apps/web` (Next.js App Router, TypeScript, TailwindCSS) và `services/api` (FastAPI, Pydantic, SQLAlchemy, SQLite + Alembic).
- API `GET /health` hoạt động, frontend có trang `/projects` demo với `Tạo dự án` và topic selector nhận dữ liệu từ fixture/demo repository; các topic mới sẽ được tạo trong M1, đừng giả vờ form đã lưu thật nếu chưa làm.
- Config/ENV/README cho local, `pytest`, lint, typecheck và smoke tests. Khi chưa có LLM, banner rõ `DEMO - CHƯA PHÂN TÍCH AI THỰC`.
- Không dựng Semrush uploader, không tích hợp Google API, không làm Brief, không dùng WordPress.
- Không gọi dịch vụ trả phí, không hỏi API key để chạy M0.

**CÁCH LÀM:**
1. Inspect repo trước, lập checklist nhỏ. Nếu đã có code, giữ phần hợp lệ, không ghi đè vô tội vạ.
2. Code M0 thực, tổ chức folder sạch và đáp ứng UX cơ bản.
3. Tự chạy commands kiểm thử có thể thực thi tại máy, sửa lỗi trong phạm vi M0; đừng báo PASS nếu chưa chạy.
4. Cập nhật `docs/DEVELOPMENT_LOG.md` với file đổi, lệnh test, kết quả thật.
5. Dừng sau M0 và báo: files changed, run commands, tests pass/fail, limitations và đề xuất M1. Không tự làm M1 nếu chưa được giao.
