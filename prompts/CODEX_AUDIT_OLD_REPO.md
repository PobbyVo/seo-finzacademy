# PROMPT KIỂM TRA VÀ NÂNG CẤP REPO CŨ

Nếu tôi đã dùng bộ Codex V1.0 hoặc V1.1 trước đó và Codex đã tạo source code, đừng tạo project khác ngay. Hãy đọc `AGENTS.md` và `docs/SPEC_FULL.md` của V1.2, sau đó:

1. Audit tất cả Google Sheets, Google Drive, Semrush SDK/MCP, WordPress, SERP auto-provider integrations đang tồn tại; ghi danh mục file/API/config trước khi sửa.
2. Đề xuất migration để thay:
   - Google Sheets Input -> Project/Taxonomy/ContentCode/Keyword FORM lưu SQLite.
   - Semrush API/MCP -> ResearchRequest + CSV/XLSX upload + header mapping + confirm.
   - Google Sheets output -> file export XLSX + HTML print/JSON/CSV.
   - WordPress sync -> **xóa khỏi workflow**. Nội bộ chỉ phát hiện trùng trong app, giới hạn công khai.
3. Không xóa dữ liệu user hiện hữu. Nếu đã có DB, viết migration và backup trước.
4. Xóa các hardcode topic P01/"Lương" khỏi domain/gates/API, giữ fixture cho tests.
5. Triển khai theo milestone ưu tiên chỉ khi tôi giao; nếu mới yêu cầu audit, chỉ báo plan + risks, không tự refactor lớn.
