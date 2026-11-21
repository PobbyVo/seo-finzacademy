# AGENTS.md — FINZ SEO ASSISTANT V1.4 — LOCAL WORKBENCH + SOURCE IMPORT

Bạn là Codex đang phát triển một ứng dụng phân tích SEO local, **không phải** chatbot có quyền truy cập các dịch vụ bên ngoài.

## Nguồn sự thật
1. `docs/UX_LOCAL_WORKBENCH_V1_3.md` (ưu tiên số 1 về UI), `docs/STATE_MACHINE_AND_EVENTS.md` (ưu tiên số 1 về workflow), sau đó `docs/SPEC_FULL.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/DATA_CONTRACTS.md`, `docs/QA_AND_TESTS.md`.
2. Dữ liệu người dùng khai báo bằng form trong UI mới là source của project. P01/P02/P08/P25 chỉ là fixture minh họa.
3. `README.md` và `config/defaults.example.json` chỉ là ví dụ phát triển.

## Bổ sung V1.4 — Source import priority

- `docs/TOPIC_SOURCE_IMPORT_AND_DEMAND_MAP_V1_4.md` là chuẩn mới nhất cho upload taxonomy/keywords, tự điền form và định nghĩa Bản đồ nhu cầu. Không được bỏ qua khi chuyển prototype sang Next.js.
- Source workbook (`Topic Pillar` + `Keywords`) là **user input**; output brief workbook là **template xuất**, tuyệt đối không trộn hai schema.
- Nghiêm cấm coi `Giai đoạn` TOFU/MOFU/BOFU là Semrush Intent. Mọi metric chưa có => null.
- Import file chỉ tạo preview và form draft; không tự ghi đè saved project hoặc approve keyword.
- Mỗi Topic Pillar có thể gồm nhiều mã nội dung; lưu các mã này trong project, không chỉ contentCode đang chọn.
- `SOURCE_GROUP` từ mã nội dung chưa phải DemandGroup intent có SERP evidence.
- Khi đổi topic, xóa businessGoal/audience cũ thay vì mặc định giữ lại.

## HARD CONSTRAINTS
- **Không implement bất cứ Google Sheets/Drive OAuth/MCP/API connector nào.** Chỉ form nhập dữ liệu trong app và xuất XLSX file local.
- **Không implement Semrush MCP/API/automatic client.** Chỉ upload CSV/XLSX do người dùng tự xuất từ Semrush Local.
- **Không implement WordPress REST/crawl/sync, đăng bài hoặc bước bắt buộc kiểm tra WP.**
- Không phụ thuộc MCP, kể cả Codex MCP, để chạy app. Nếu Codex IDE có MCP đó là môi trường dev, không phải ứng dụng runtime.
- Không hardcode P01, "Lương", "Gross/Net", Google Sheet ID, domain FinZ, trường báo cáo hoặc tên tab trong domain/agents/gates/routes. Tất cả topic/giao diện chọn động bằng DB; fixture được phép chứa P01.
- Không tự bịa Volume/KD/Intent/SERP, luật, số BHXH/TNCN, case thực tế. Null != 0.
- Chỉ xuất ARTICLE brief. Không tạo TOOL/DOWNLOAD/LANDING. 5–7 bài là mục tiêu mềm.
- Chọn công thức viết + chiến thuật **cấp toàn bài**, không áp dụng cho từng H2/H3. Không ép câu mở bài phải trả lời ngay lập tức.
- Không thay user-source primary hoặc tự duyệt nhánh mới. LLM không thể tự set APPROVED.
- Không cho hành vi upload/import làm mất file gốc hoặc ghi đè quyết định của người dùng.

- UI phải làm rõ `WAITING_USER` khi user thao tác Semrush bên ngoài; `RUNNING` chỉ khi worker thực sự làm việc. Không dùng % tiến độ giả.
- Chỉ có một CTA Next Action ưu tiên theo blocker; mỗi phiếu Semrush gồm seed, report, thị trường, mục đích, hướng dẫn, required columns, file/status.
- `prototype/` là UI demo tương tác bằng JS localStorage + server Python nhỏ đọc file; KHÔNG được nhận nó là ứng dụng thật, SEO logic hoặc chuẩn production.
- M0.5: port giao diện demo sang Next.js sau M0, đọc `prompts/CODEX_BUILD_WORKBENCH_UI.md`. Không xây engine hay connector mới ở M0.5.

## Workflow lập trình
- Bắt đầu M0, chỉ làm một milestone mỗi lượt; `docs/IMPLEMENTATION_PLAN.md` là checklist.
- Backend `FastAPI/Pydantic/SQLAlchemy/SQLite`, frontend `Next.js/TypeScript/Tailwind`, kiểm thử bằng pytest + typecheck/lint.
- V0.1 chạy DEMO không cần credentials. AI thực sử dụng một LLMProvider cấu hình rõ ràng, có cơ chế opt-in gửi dữ liệu ra ngoài; không gọi dịch vụ bên ngoài khi mock.
- Có API version, validation errors tiếng Việt, lưu audit trail/source references, migrations và project snapshots.
- Xây API/UI với business logic server; không để frontend quyết định trạng thái gate hoặc approval hợp lệ.
- Trước khi hoàn tất milestone: chạy lint/test/typecheck, báo lệnh & kết quả thật; cập nhật `docs/DEVELOPMENT_LOG.md`.
- Không tự commit/push/deploy, không cài API key không rõ nguồn, không bỏ qua tests.

## Format báo cáo kết thúc mỗi milestone
`Files changed / Features delivered / How to run / Test commands + outcomes / Missing inputs / Known limitations / Recommended next milestone`.

## ADDENDUM V1.5 (OVERRIDES ANY OLDER CONFLICTING TEXT)
- SQLite is the primary storage when served at localhost; browser localStorage is emergency/offline demo fallback. Multiple topic projects must persist independently.
- The first AI loop is `Analyst -> Critic -> manually approved Semrush requests`; second loop is `upload -> full-file evidence validator -> AI Critic -> bounded re-research`. No Semrush/Google Sheets/WordPress APIs or MCP.
- The system must never declare SEO/content-brief readiness merely because Volume/KD/Intent exist. Require SERP and human mapping approval.
- Only reference verified taxonomy fields/source refs. Any uncertain scope needs human review. New keywords are HYPOTHESIS until research.
- See `docs/V1_5_DB_AI_RESEARCH_LOOP.md` and `prompts/CODEX_V1_5_IMPLEMENT_RESEARCH_LOOP.md`.
