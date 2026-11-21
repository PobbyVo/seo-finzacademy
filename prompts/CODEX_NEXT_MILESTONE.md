# PROMPT CHẠY PHASE TIẾP THEO

Hãy đọc `AGENTS.md`, `docs/SPEC_FULL.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/QA_AND_TESTS.md` và `docs/DEVELOPMENT_LOG.md`. Kiểm tra trạng thái thực tế của milestone trước bằng code + tests; không tin marker DONE nếu thiếu bằng chứng.

Chỉ thực hiện **milestone mà tôi chỉ định dưới đây**: [THAY_BANG_M1_M2_M3_M4_M5_M6_HOAC_M7].

Không chuyển sang milestone kế tiếp. Không tích hợp Google Sheets API/OAuth/MCP, Semrush API/MCP hay WordPress; form input thủ công + file upload CSV/XLSX + XLSX file export là phương thức dữ liệu cố định.

Mọi logic phải generic cho bất kỳ Topic Pillar; thêm regression tests P01/P02/P08/P25, không có nhánh if topic == P01. Writing Strategy ở cấp toàn bài; không gắn vào H2.

Chạy test/lint/typecheck của phần thay đổi, ghi kết quả có thật, cập nhật log rồi dừng. Nếu thiếu sample file cho importer M3/M4, tạo mock có nhãn DEMO và yêu cầu người dùng dùng file thật ở vòng nghiệm thu, không bịa ra report live.
