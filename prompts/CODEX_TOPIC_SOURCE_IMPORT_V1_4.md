# PROMPT CODEX — Tiếp tục phát triển Topic Import + Demand Map

Bạn đang ở thư mục gốc repo `finz-seo-assistant`. Hãy đọc `AGENTS.md`, `docs/TOPIC_SOURCE_IMPORT_AND_DEMAND_MAP_V1_4.md`, `prototype/topic_source_import.py`, `prototype/server.py`, `prototype/app.js` và `prototype/tests/test_topic_source_import.py`.

**Mục tiêu:** hoàn thiện chức năng upload workbook `Topic Pillar` + `Keywords` lên local và tự điền `Thiết lập chủ đề` cho bất kỳ taxonomy nào; giữ mọi giá trị và nguồn gốc. Không cần Google Sheets OAuth/API; không kết nối Semrush API/MCP hoặc WordPress.

Bắt buộc kiểm tra:
1. Không có hardcode P01 hoặc tên topic trong parser, mapping hay quyết định.
2. Tự phát hiện header hàng 4 (Topic Pillar) và hàng 1 (Keywords) của workbook nguồn; hỗ trợ alias header, bất kể thứ tự tab.
3. Tệp `.xlsx` hai tab: upload → chọn topic → chọn mã nội dung → preview → auto-fill form → người dùng bổ sung businessGoal/audience → Save.
4. Không tự lưu project khi vừa chọn file. Cảnh báo nếu thay taxonomy đã có dữ liệu nghiên cứu.
5. Bảo tồn toàn bộ `keyword role`, `contentCode`, `funnelSource` và `sourceRow`; không nhầm TOFU/MOFU/BOFU với Search Intent của Semrush.
6. Topic lỗi như P26 phải có warning, không tự điền.
7. `SOURCE_GROUP` khi vào Bản đồ nhu cầu là nhóm tạm theo mã nội dung, **không phải Search Intent đã xác minh**.
8. Chuyển P01 sang P08: xóa các trường businessGoal/audience thuộc topic cũ, không cần sửa code.
9. Giữ upload Semrush tách biệt khỏi upload topic source.
10. Chạy các unit tests và UI smoke có sẵn; bổ sung test generic P99 và CSV thiếu một tab; báo rõ giới hạn và những bài kiểm thử không thể chạy.

Không làm: gửi dữ liệu ra SaaS, gọi Semrush API, giả lập Volume/KD, tự tạo brief chính thức, xóa source cũ khi chưa được duyệt, dùng Wordpress, sửa domain nghiệp vụ hoặc hardcode logic dành riêng cho ngành lương.

Sau khi hoàn tất, đưa ra lệnh chạy trên Windows, danh sách file đã thay đổi, test results và giới hạn còn lại. Nếu phải phát triển sang Next.js/FastAPI, chỉ thực hiện theo milestone đã duyệt, không viết lại tất cả trong một lần.
