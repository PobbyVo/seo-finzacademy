# CODEX PROMPT — XÂY GIAO DIỆN LOCAL SEO WORKBENCH V1.3

Bạn là senior full-stack engineer và UX engineer. Trong repo này, hãy đọc **theo thứ tự**:

1. `AGENTS.md`
2. `docs/UX_LOCAL_WORKBENCH_V1_3.md`
3. `docs/STATE_MACHINE_AND_EVENTS.md`
4. `docs/SPEC_FULL.md`
5. `docs/DATA_CONTRACTS.md`
6. `docs/IMPLEMENTATION_PLAN.md`
7. `docs/QA_AND_TESTS.md`
8. `prototype/index.html`, `prototype/styles.css`, `prototype/app.js` và `prototype/server.py`

**Mục tiêu milestone hiện tại: M0.5 — xây dashboard & navigation tương tác như bản prototype trong Next.js**, không triển khai toàn bộ SEO engine ngay.

### Những việc bắt buộc

- Dựng layout desktop-first responsive: sidebar, topbar, project switcher, stepper 8 bước, Hero Next Action, Blockers, Activity Log, trạng thái công việc.
- Tạo form nhập Project / Pillar / Topic Pillar (`Loại topic`, `Trục chia`, `Chủ đề chính`) / ContentCode / source keywords. Mọi chủ đề động; P01 là fixture được nạp khi user chọn DEMO.
- Xây Research Request List với phiếu đầy đủ `seed`, loại báo cáo, market, lý do, trường cần xuất, `Copy instructions`, `Attach file`, trạng thái thực. Các bước Semrush luôn là hướng dẫn UI của bên thứ ba; **KHÔNG có API, MCP, sync hoặc login**.
- Upload Workbench: request selector → CSV/XLSX preview (trong tương lai) → mapping cột → validate → user confirm. Nếu chưa thực hiện backend ở milestone này, làm interface với trạng thái `NOT_IMPLEMENTED` rõ ràng; **không gọi demo là upload hoàn chỉnh**.
- Workflow step status, Request status, Gate status phải tách biệt; dùng schema/events trong `STATE_MACHINE_AND_EVENTS.md`.
- Với tác vụ thực sự đang chạy, UI hiển thị tên task + spinner; nếu progress không định lượng được, không tạo % giả. Nếu đang chờ user thao tác bên ngoài, hiển thị `WAITING_USER`, không hiển thị `RUNNING`.
- Tạo Journal và blockers có reason+next_action; tất cả nút phải có hành động hoặc disabled + giải thích rõ.
- Bảo toàn quyền chủ động của Content: Framework/tactics chỉ định hướng cấp toàn bài, không áp vào từng H2.
- Không xây Google Sheets connector, Semrush connector, WordPress connector. Không hardcode P01 logic.

### Mức hoàn thành M0.5

- Dev server mở UI local; một dự án generic mới có thể nhập Topic Pillar bất kỳ mà không cần sửa source.
- Bản DEMO cho phép đi qua giao diện và kiểm thử trạng thái; UI ghi `DEMO / MOCK` rõ.
- Lưu state tạm một cách nhất quán với milestone hiện tại; không tuyên bố có SQLite persistence nếu chưa xây DB.
- Khi chưa có file, dashboard nêu rõ đang chờ người dùng export Semrush và chọn đúng file cho request.
- Khi chưa có SERP hoặc approval, nút xuất brief chính thức disabled và hiển thị lý do.
- Chạy lint/typecheck/tests và ghi **kết quả thật** vào `docs/DEVELOPMENT_LOG.md`.
- Chỉ làm M0.5. Không tự triển khai M1–M7, không tự tạo API/credentials/cloud connection.

### Format báo cáo cuối

- `What was built`
- `Changed files`
- `Manual test journey` (buttons/steps/screens)
- `Commands actually run + results`
- `Blocked/Mock/Not implemented features`
- `Next milestone suggestion`
