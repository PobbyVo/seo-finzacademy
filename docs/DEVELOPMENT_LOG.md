# DEVELOPMENT LOG

| Milestone | Status | Files changed | Tests executed | Notes |
|---|---|---|---|---|
| M0 | DONE | `apps/web`, `services/api`, `e2e`, ENV, README, Makefile | 22 pytest + 2 browser tests; lint/typecheck/build/migration PASS | Chỉ scaffold local; không mở rộng milestone |
| M0.5 | NOT_STARTED | — | — | Local Workbench UI; chưa triển khai |
| M1 | NOT_STARTED | — | — | Manual data input |
| M2 | NOT_STARTED | — | — | Topic intelligence pre-Semrush |
| M3 | NOT_STARTED | — | — | Manual upload |
| M4 | NOT_STARTED | — | — | F1–F4 |
| M5 | NOT_STARTED | — | — | F5/F6 manual SERP |
| M6 | NOT_STARTED | — | — | Brief/export |
| M7 | NOT_STARTED | — | — | QA/reuse |


## V1.3 UI prototype design (2026-11-20)

- Added interactive static HTML/CSS/JS Workbench dashboard with 8-step workflow, blockers, Next Action, Semrush request cards, manual upload CSV/XLSX mapping, completeness checks, manual SERP and approval demo.
- Added tiny Python HTTP server bound to loopback for CSV/XLSX preview (openpyxl); file not persisted in prototype.
- Added `UX_LOCAL_WORKBENCH_V1_3.md`, `STATE_MACHINE_AND_EVENTS.md` and Codex M0.5 implementation prompt.
- **Not a production implementation**: AI inference, full SEO engine, raw evidence storage and official brief export remain milestones to build.

- Prototype tests: Node `--check` PASS, Python compile PASS, Playwright UI smoke CSV PASS, Playwright custom Topic P99 PASS, HTTP CSV/XLSX parse PASS.

## V1.4 — Topic Source Import prototype
- Added local-only `/api/topic-source-preview` and `prototype/topic_source_import.py` (header recognition and source mappings), separate from Semrush data preview.
- Added setup workbook intake, topic/content selectors, apply-to-form with human confirmation, and `SOURCE_GROUP` seed action in Demand Map.
- Added `fixtures/FINZ_TOPIC_IMPORT_READY.xlsx`, field mappings, Codex prompt, and parser/UI regression tests.
- Verified: original live-exported workbook 25 valid topics + 1 incomplete P26, 299 keywords, 63 codes; generic fixture and topic change P01→P08; local HTTP endpoint tested. No LLM/AI implemented.

## M0 — Next.js + FastAPI + SQLite scaffold (2026-11-21)

- Đọc toàn bộ `AGENTS.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/SPEC_FULL.md`, `prompts/CODEX_START_M0.md`, cùng các contract và bổ sung UX/V1.4/V1.5 liên quan. Hai đường dẫn được yêu cầu `docs/FINZ_SEO_ASSISTANT_SPEC.md`, `harness/build/M0-scaffold.md` không có trong bộ nguồn; dùng các tài liệu tương ứng hiện có, không tự tạo đặc tả thay thế.
- Phạm vi: `/projects`, tạo/chọn dự án trống trong SQLite, health API, nạp demo có chủ đích, snapshot/audit và lỗi tiếng Việt. Fixture P01 có hai mã nội dung, ba keyword minh họa; không phải bộ nguồn workbook đầy đủ. Mọi metric thiếu giữ `null`; funnel nguồn tách khỏi Semrush Intent.
- Tách DB M0 khỏi `.finz_local_data/` của prototype; không sửa hay migrate dữ liệu prototype. Không thêm upload, AI, connector, workflow hoặc brief của milestone sau.
- Files changed: `apps/web/**`, `services/api/**`, `e2e/**`, `.env.example`, `.gitignore`, `.python-version`, `.nvmrc`, `Makefile`, `README.md`, `docs/DEVELOPMENT_LOG.md`.
- Backend verification (Python 3.12.15): `cd services/api && .venv/bin/python -m pytest` — **22 passed, 0 failed**, 0.32s; `.venv/bin/python -m ruff check .` — PASS; `.venv/bin/python -m ruff format --check .` — PASS (14 files); `.venv/bin/python -m alembic upgrade head` — PASS; `.venv/bin/python -m alembic check` — PASS, không có schema change chưa migrate.
- Kiểm tra DB mặc định `data/finz_m0.sqlite3`: revision `0001_m0_scaffold`, **0 dự án**, không tự seed demo. Quét `services/api/finz_api`, `apps/web/src`, `next.config.ts`: không có chuỗi chủ đề P01/Lương/Gross hay client dịch vụ ngoài; frontend chỉ fetch API local qua proxy.
- Browser verification: `npm --prefix e2e test` — **2 passed, 0 failed**, 3.5s, Chrome thật với FastAPI/Next.js/SQLite tạm; `npm --prefix e2e run typecheck` — PASS; `node --check e2e/run.mjs` — PASS. Bao phủ dự án trống, nạp demo chủ động, mọi mã nội dung/vai trò/funnel, metric null, độc lập/reload, lỗi API/retry và layout mobile. Không có request trình duyệt ra ngoài localhost hoặc page error. Đã xem ảnh desktop/mobile; không tràn trang, bảng cuộn trong panel. Launcher dọn các server/DB tạm sau test.
- Frontend verification (Node 24.22.2, Next.js 16.4.6): `npm --prefix apps/web run lint` — PASS, 0 warnings; `npm --prefix apps/web run typecheck` (`next typegen && tsc --noEmit`) — PASS; `npm --prefix apps/web run build` — PASS, 4/4 static pages, routes `/`, `/_not-found`, `/projects`. Build script dùng `next build --webpack`, đã kiểm tra đúng script cuối cùng. Turbopack production build gặp EPERM khi tạo port nội bộ trong môi trường chạy; Webpack là bundler chính thức và chạy thành công. Dev server dùng cấu hình Next mặc định, đã được kiểm chứng trong browser suite.
- Các lỗi đã xử lý: ESLint bắt cập nhật state đồng bộ trong effect và export PostCSS thiếu tên; input tên dự án được căn chỉnh giới hạn 120 ký tự với server. Smoke test retry ban đầu bắt nhầm `role=alert` của Next route announcer; đã giới hạn selector trong `main` rồi chạy lại cả suite thành công. `next typegen` tạo lại type routes mặc định sau E2E để typecheck chạy độc lập từ checkout mới.
- How to run: cài dependencies theo `README.md`; tại root, terminal 1 chạy `make api` (bao gồm migration), terminal 2 chạy `make web`; mở `http://127.0.0.1:3000/projects`. Backend `http://127.0.0.1:8000/health` và `/api/v1/health` trả 200 sau migration. Dependency đã khóa bằng npm lockfiles và `services/api/requirements-dev.lock`. Không cần API key. `make check`, `make build-web`, `make test-e2e` là các shortcut cho lệnh kiểm tra tương ứng.
- Missing inputs: hai đường dẫn tài liệu nêu trên; không cần credentials để chạy M0.
- Known limitations: single-user localhost; form chỉ tạo tên dự án; dữ liệu fixture chỉ đọc, không cho ghi đè topic đã nạp; chưa có UI lịch sử snapshot/backup/restore.
- Recommended next milestone: M0.5 theo `docs/IMPLEMENTATION_PLAN.md`, chỉ khi người dùng yêu cầu. Không tự triển khai.

## M0 — Khởi động FE + BE bằng một lệnh (2026-11-21)

- Files changed: root `package.json`, `scripts/dev.mjs`, `Makefile`, `README.md`, nhật ký này.
- Features delivered: chạy `npm run dev` tại root để kiểm tra dependencies/cổng, chạy Alembic, đợi health API rồi mở Next.js. Log gắn nhãn DB/BE/FE; Ctrl+C dừng cả nhóm tiến trình con, kể cả Uvicorn reload và Next server. Nếu một server dừng, dừng server còn lại. Không thêm dependency npm cho launcher.
- How to run: `npm run dev`, mở `http://127.0.0.1:3000/projects`; API tại `http://127.0.0.1:8000/health`. Cài dependencies FE/BE một lần theo README; `make dev` là alias. Giữ các lệnh chạy riêng để debug.
- Test commands + outcomes: `node --check scripts/dev.mjs` PASS; `npm run` nhận script `dev`; `make check` PASS (22 pytest, Ruff, ESLint, Next typegen + TypeScript). Kiểm thử tích hợp bằng Node ESM harness qua stdin với SQLite tạm: chạy đúng `npm run dev`, FE HTTP 200, BE/proxy health HTTP 200, gửi SIGINT tương đương Ctrl+C và kiểm tra hai cổng đã đóng — PASS; giữ một server chiếm cổng 8000 và xác minh không bị tắt — PASS; DATABASE_URL sai làm migration thất bại, launcher thoát khác 0 và không mở server — PASS. Đã sửa xử lý tín hiệu lặp do npm chuyển tiếp SIGINT sau khi lần thử đầu phát hiện tiến trình con còn chạy; lượt chạy lại đạt cả ba trường hợp, DB tạm đã được dọn.
- Missing inputs: không có. Known limitations: launcher được kiểm chứng trên macOS với dependencies đã cài; cổng mặc định FE 3000, BE 8000. Không tự cài thư viện khi khởi động.
- Recommended next milestone: giữ nguyên M0.5; chưa triển khai milestone mới.


## V1.5 — Workflow UX & Validation Feedback (2026-11-21)

- Scope: chỉnh trực tiếp `prototype/` theo task mới; không scaffold lại, không port sang Next.js hoặc xây brief generator.
- Files changed: `prototype/app.js`, `workflow.js` (mới), `index.html`, `styles.css`, `server.py`, `persistent_store.py`, `evidence_engine.py`, `prototype/README.md`; hai entrypoint browser Python chuyển sang Playwright HTTP portable; thêm `tests/test_workflow_feedback.py`, `_browser_server.py`; `e2e/prototype.config.ts`, `prototype/workflow.spec.ts`, `prototype/globals.d.ts`; cập nhật e2e config/typecheck, state machine, tài liệu V1.5 và log.
- Delivered: bảy bước, approvals riêng; bỏ form/route SERP, route cũ chuyển an toàn; kế hoạch dự thảo luôn SERP_NOT_VERIFIED, không suy intent/loại trang/gộp tách hay READY_FOR_BRIEF. Không xóa lịch sử SERP; server hợp nhất lịch sử khi lưu snapshot mới. Topic/primary đổi tạo project ID mới để giữ imports/approvals của dự án cũ.
- ValidationFeedback có code/severity/reason/impact/solution/CTA/blocking/source_ref, card và inline input/mapping; hỗ trợ 15 mã trong task; cảnh báo metrics dựa trên full-file backendStats nếu có, fallback mẫu được ghi rõ. Thêm lựa chọn locale khi mapping. Lỗi API thêm feedback, giữ `error` string tương thích.
- CompletionModal chỉ sau response SQLite có storage/revision; PROCESS_COMPLETED khác QUALITY_APPROVED. Countdown 2 giây, đi tiếp/ở lại/Escape, dialog native giữ focus, reduced-motion. Hủy timer khi đổi trang/dự án/pagehide; guard epoch chống callback cũ; save queue tuần tự; bootstrap đọc DB thay vì âm thầm ghi đè DB bằng localStorage. Không tự chuyển khi preview, approval pending, Critic yêu cầu nghiên cứu lại, tác vụ lỗi hoặc bước nguồn chưa PROCESS_COMPLETED. Request vẫn WAITING_USER sau tạo phiếu.
- Bugs fixed during verification: bootstrap bất đồng bộ có thể ghi đè màn hình/form đang sửa; đã dùng epoch + readiness promise. Lỗi save timer nay được catch và hiện CTA, không unhandled rejection. Không còn hoàn thành bước chỉ vì groups/imports có phần tử. Không dùng Volume/KD threshold để bỏ keyword.
- Tests: `PYTHONPATH=prototype services/api/.venv/bin/python -m pytest prototype/tests -q`: **11 passed**. `node --check prototype/app.js`, `node --check prototype/workflow.js`: PASS. `npm --prefix e2e exec -- playwright test --config e2e/prototype.config.ts`: **7 passed (16.4s)**, bao phủ các điều kiện nghiệm thu theo nhóm ca: 7 steps/no SERP route, lưu/auto-next, lỗi DB/no-next, stay/cancel/switch, legacy SERP, preview/mapping/import, missing KD/duplicates/low volume, approval/HOLD, AI disabled/failure, RUNNING thực và reload. Test server dùng thư mục SQLite tạm và AI disabled; không thao tác DB người dùng.
- Regression: `make check`: **22 pytest passed**, Ruff/ESLint/Next typegen + TypeScript PASS. `npm --prefix e2e test`: **2 passed (3.4s)**. `npm --prefix e2e run typecheck`: PASS, bao gồm browser tests mới. Không gọi model/SEO API thật trong kiểm thử.
- Run: `services/api/.venv/bin/python prototype/server.py 5173`, mở http://127.0.0.1:5173. Cần `openpyxl` từ `prototype/requirements.txt`. `npm run dev` vẫn khởi động ứng dụng M0 riêng ở 3000/8000.
- Limitations: không có parser/gate SERP được xác minh, không tạo brief hoặc kết luận SEO-ready. Không kiểm thử provider LLM thật khi chưa được cấu hình; test bao gồm AI chưa cấu hình và lỗi request. Chỉ metadata/snapshot kỹ thuật được hoàn thành; phê duyệt chất lượng SEO không được tự suy ra.
- Missing inputs: không cần credentials. Không commit/push/deploy trong task này.

## M0.25 — AI Provider Settings (2026-11-21)

- Files: `services/api/finz_api/ai/{gateway,settings}.py`, package init, migration `0002_ai_settings`, API/error handling, pyproject/lockfile, tests; Next `/settings/ai`, sidebar link; e2e Settings/config; README/implementation plan/log.
- Delivered: provider/model dùng chung cho Analyst/Critic; password key nhập backend, OS keyring, metadata/reference-only SQLite. Save/Get/Remove không gọi provider. Test Connection có consent, short prompt và JSON validation; trả CONNECTED chỉ khi response hợp lệ. Hiển thị status/model/test time/latency và lỗi tiếng Việt.
- Gateway: ProviderConfig, AIProviderAdapter, AIProviderRegistry, test_connection, generate_structured_output và shared generate_for_task. HTTP adapters theo API riêng; endpoint cố định, không follow redirect, không retry/fallback. Gemini response đọc steps/model_output/content; Claude có version header riêng. Không tạo metrics, approval, mapping hoặc brief.
- Dependencies: keyring (OS credential manager; không dùng plaintext fallback), jsonschema (validate JSON trước khi dùng); đã khóa phiên bản trong requirements-dev.lock. Không cần ba SDK cho các request MVP.
- Security: không trả key hoặc raw provider error; validation errors không echo input. SecretStr/repr redaction, no-store responses, Origin allowlist, JSON-only mutation. Test payload không chứa dữ liệu dự án. Keychain không sẵn sàng thì fail closed với hướng khắc phục.
- Tests: `cd services/api && .venv/bin/python -m pytest -q` — 49 passed; Ruff check PASS; frontend lint/typecheck PASS; `make build-web` PASS (5 static pages, có /settings/ai); `npm --prefix e2e run typecheck` PASS; `npm --prefix e2e test` — 4 passed (6.1s). Regression prototype — 11 passed. `make migrate` và `alembic check` PASS, không có schema change chưa migrate. Browser test ban đầu bắt nhầm alert của Next route announcer; đã scope vào main rồi chạy lại thành công.
- Verification uses in-memory secrets + mocked HTTP/SDK-equivalent transport; browser Settings mutations use mocked API. Không có request provider thật hoặc key thật trong tests. Không ghi secret vào Keychain trong tests.
- Run: cài backend dependencies theo README, `make migrate`, `npm run dev`, mở http://127.0.0.1:3000/settings/ai. Nhập key/model, Save, consent, Test; dùng Remove Key để xóa.
- Missing inputs: cần key/model có quyền để kiểm tra kết nối thật; không cần cho automated tests.
- Limitations: chưa kiểm thử live provider/OS keychain end-to-end với credentials thật; model riêng từng task chưa có. Production M0 chưa có workflow Analyst/Critic: gateway entrypoint đã sẵn sàng, không triển khai research engine trong milestone này. Prototype không bị thay đổi bởi M0.25.
- Next milestone: M0.5 — chuyển Workbench UI sang Next.js. Không commit/push/deploy trong task này.

- M0.25 bổ sung AI_GATEWAY_MODE=mock: không gọi transport, không giả CONNECTED; browser runner ép mock để tránh outbound ngoài ý muốn. Unit test kiểm tra transport không được gọi. Backend live chỉ gửi request sau consent. OS backend nhận diện trên máy: keyring.backends.macOS; chưa ghi/thử key thật. API metadata và trang Settings trên 3000/8000 trả HTTP 200. `pip check` không có dependency bị lỗi.

## M0.25 — Gemini request compatibility follow-up (2026-11-21)

- Added `Api-Revision: 2026-05-20` to the Gemini Interactions adapter to match the user's supplied request; model still comes from Settings and store remains false. Response parser remains steps/model_output/content.
- Regression: provider/settings suite 28 passed; Ruff and git diff --check PASS. Test asserts exact Gemini endpoint, auth/revision headers, chosen model and payload. No credential in source/tests/log.
- User-authorized live check: saved the supplied Gemini credential through the local Settings API into OS Keychain, then attempted Test Connection once. Save HTTP 200; test HTTP 504 / CONNECTION_TIMEOUT after the configured timeout. Connection is not marked CONNECTED; key/model validity remains unverified. No project or Semrush data sent.

## M0.25 — Gemini PROVIDER_UNAVAILABLE diagnosis (2026-11-21)

- Traced frontend Settings → Next proxy → versioned FastAPI Test endpoint → SQLite metadata/OS Keychain → Registry → Gemini fixed HTTPS POST. Request construction and timeout unchanged because no proven payload/credential retrieval bug was found.
- Original request ID 521d0a80-ec52-4e0d-a8ae-7d304729d2f5 has no correlated historical upstream log. New diagnostic request fba81e90-302a-4c20-a604-15b66fe141a2 reproduced upstream HTTP 503 / service_unavailable in 1194 ms; application now returns 503 and preserves upstream evidence. Project/snapshot/audit hashes unchanged.
- Fixed HTTP 400/503 status loss, wrapped-timeout misclassification and generic network/provider error conflation. Added safe structured diagnostics, request-context correlation and private rotating local log. Raw exception, headers, key, payload and raw provider messages never logged. UI shows correlation ID/upstream fields and retains original test error if metadata refresh fails.
- Files: `services/api/finz_api/ai/{gateway,diagnostics}.py`, `main.py`, new `tests/test_ai_diagnostics.py`, existing settings tests; `/settings/ai` error presentation, e2e settings test; diagnosis document and development log. No changes to credential storage, migrations or project logic.
- Verification: 66 backend tests PASS; Ruff PASS; frontend lint/typecheck/build PASS. Browser/typecheck final results recorded below after completion. Tests include status 400/401/403/404/429/503/504, DNS/TLS/refused/reset, wrapped timeout, local/upstream ID correlation and secret-echo redaction. Exactly one live diagnostic test, no project content submitted.
- Full evidence, classification and reproduction: `docs/AI_PROVIDER_DIAGNOSTICS.md`.
- Final browser regression: 5 passed (6.6s); e2e TypeScript PASS. `git diff --check` PASS. The new test confirms that a failing metadata refresh cannot hide the original upstream status/code/Request ID.
