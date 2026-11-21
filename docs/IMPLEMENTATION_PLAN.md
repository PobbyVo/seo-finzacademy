# IMPLEMENTATION PLAN — V1.3 LOCAL WORKBENCH / MANUAL WORKFLOW

> Mỗi milestone phải có code chạy, tests/lint/typecheck và log thật. Không tự chuyển giai đoạn hoặc claim DONE chỉ vì tài liệu đã viết.

## Milestone 0 — Repo/Runtime Scaffold

- Next.js + TS + Tailwind frontend; FastAPI + Pydantic + SQLite + migrations backend.
- Health API, error handling, API client, root `/projects` UI, demo/mock badge, dữ liệu P01 ở fixture chỉ khi user bấm `Nạp demo`.
- `.env.example`, `.gitignore`, README local commands, test/lint config.
- **Không:** Google auth, Semrush adapter API, WordPress, LLM live, file upload thật.
- DoD: UI mở local, API health 200, chọn được project trống, tests green.

## Milestone 0.5 — Local Workbench UI + Workflow Observability (NEW V1.3)

- Đọc `docs/UX_LOCAL_WORKBENCH_V1_3.md` và `docs/STATE_MACHINE_AND_EVENTS.md` trước khi triển khai.
- Dựng sidebar, dashboard KPI, stepper 8 bước, blockers, one Next Action, activity journal, manual Semrush Research Request cards.
- Dùng `prototype/` làm visual/interaction reference; port sang Next.js component đúng cấu trúc.
- Có trạng thái riêng cho workflow/request/gate; hiển thị `WAITING_USER` thay vì giả `RUNNING` khi user xuất dữ liệu ngoài app.
- Form generic cho mọi Topic Pillar; P01 chỉ là DEMO do người dùng bấm nạp.
- Import preview/mapping và official brief chưa thực thi thì thông báo NOT IMPLEMENTED rõ; button disabled nếu không có hành động thật.
- Test flow `new project → steps → blockers → manual request → file upload (nếu backend đã có) → status → journal`.
- DoD: UI local hoạt động, mọi action được phản hồi, không có API Semrush/Google/WP, không có phần trăm tiến độ giả, lint/typecheck/tests pass.

## Milestone 1 — FORM taxonomy/source keywords

- Wizard Project → Pillar/Topic Pillar → Content Codes/Keywords; CRUD, validation và SQLite persistence.
- Taxonomy Snapshot + immutable source keyword snapshot, edit tạo version và audit.
- Test tự nhập P01, P02, P08, P25, generic topic mới không sửa code.
- DoD: reload vẫn giữ data; không có Google Sheets connector hoặc hardcoded taxonomy logic.

## Milestone 2 — V0.1 Topic Intelligence (ưu tiên chất lượng trước Semrush)

- LLMProvider interface + MockProvider deterministic, E0 taxonomy evidence + E1 quality + E2 demand group dedup; Topic Opportunity Map.
- Optional AI thực khi được user cấu hình; source refs server verified.
- Approval Queue new branch/primary + research request builder.
- DoD: nhóm nhu cầu khác keyword variants; no invented metrics; P01/P02/P08/P25 boundaries đúng fixture; requests biết lấy file nào và vì sao.

## Milestone 3 — Manual Semrush Upload UI

- Form request metadata, multipart CSV/XLSX file upload, preview, select sheet, CSV delimiter/encoding override, header mapping, persisted ImportProfile.
- Raw file checksum, size/type checks, upload lifecycle.
- DoD: không gọi Semrush API/MCP; upload có preview & mapping; confirm before metrics influence decisions.

## Milestone 4 — F1/F2/F3/F4 + evidence gaps

- Pandera/Pydantic import validation, locale numeric, missing/zero, conflicting rows, preserve provenance, dedup keyword, relevance/priority.
- Missing data re-request đúng report; expanding topic only for true coverage gap.
- DoD: number `9.900`/`9,900` xử lý theo locale, no summed volume, per-row errors, no invisible row removal.

## Milestone 5 — F5/F6 Manual SERP + Article Mapping

- Upload SERP organic report hoặc manual form nhập ranked URLs, titles, snippets; format evidence and uncertainty.
- Article Opportunities, soft goal 5–7; 4+3 gaps output valid; approval queue final mapping.
- **Không có WordPress step**. Internal duplicate check chỉ dựa trên dữ liệu đã lưu trong app, cảnh báo giới hạn.
- DoD: chưa đủ top URLs không giả dạng top 10; tool/download ngoài quota; primary change approval required.

## Milestone 6 — F7 Brief + Writing Strategy + Offline Export

- ContentBrief from approved article, SEO fields, H2/H3 editorial coverage; catalog 13 frameworks & 16 tactics global.
- Generic XLSX renderer 3 logical sheets, CSV/JSON, HTML print; no Google Sheets API, không phải phụ thuộc workbook bên ngoài.
- DoD: no frameworks/tactics in H2; draft watermark when incomplete; user can download valid XLSX; overview/detail consistent; finance claim check.

## Milestone 7 — Quality, security, reusable export

- Regression suite multiple topics, import security, audit/backup/restore local JSON, performance limits, accessibility.
- Test generic P01/P02/P08/P25 + topic completely new via UI.
- DoD: không chứa source strings chủ đề trong code logic; no Google/MCP/WP connectors; no external secrets or unapproved calls.

## Definition of Done mỗi phase

- Features thực chạy trên local qua command ghi trong README.
- Tests với kết quả thật, lint/typecheck, migrations hoàn thành.
- UI báo lỗi và success thật; không fake connector READY.
- `docs/DEVELOPMENT_LOG.md` cập nhật.
- Không tự push/commit/deploy; không tự mở các bước tiếp theo.


## V1.4 — Source Topic Import (prototype đã có, production chưa có)
- Implement parser auto-detect `Topic Pillar` + `Keywords` header alias, handle row4, no Google auth.
- UI choose Topic Pillar and content code, preview sources/warnings, apply-to-form draft, review and save.
- Full persistence, version snapshots, delta-import UI, CSV two-part merge, SHA256 and role preservation belong production M1.
- Step 02 seeded `SOURCE_GROUP` must not be reported as validated Search Intent.
- Regression tests: P01/P08/P25 + completely different taxonomy Z42; source P26 is incomplete.
- Reference: `TOPIC_SOURCE_IMPORT_AND_DEMAND_MAP_V1_4.md`.
