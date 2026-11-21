# V1.4 — Nhập bộ chủ đề nguồn và Bản đồ nhu cầu

> Áp dụng cho **bất kỳ Topic Pillar / mã nội dung / ngành hàng nào**, không hardcode P01. Đây là tính năng **import file local**, KHÔNG kết nối API Google Sheets, Semrush hay WordPress. Source Excel chỉ dùng để chuẩn bị dữ liệu đầu vào; bản thân nó không chứng minh nhu cầu SEO.

## 1. Hai workbook KHÔNG có cùng vai trò

**Input**: Workbook `Bộ key FinZ` — tab `Topic Pillar` và `Keywords`. Nguồn: https://docs.google.com/spreadsheets/d/1IFOHVnw44zNvTQw7t3Dwo0q1Tm9snq4Uatga40ZMu2s/edit .

**Output tham chiếu**: Workbook `bảng nghiên cứu Keyword và kiểm tra SERP` — tab `SEO Content Brief - Luong`. Nguồn: https://docs.google.com/spreadsheets/d/1T9YFUeDxc8IDVkXR6X2LNNqiF8GdxqlrjiqV-2-QPLo/edit?gid=725194806 .

Workbook đầu tiên cung cấp taxonomy, keyword Chính/Phụ, TOFU/MOFU/BOFU, mã nội dung, tiêu đề nội dung gốc. Nó **không** cung cấp business goal, audience, keyword metrics Semrush, SERP evidence, keyword mapping đã duyệt, CTA, outline SEO, Writing Strategy. Không được tự điền hoặc kết luận các trường còn thiếu từ dữ liệu gốc.

Workbook thứ hai là **mẫu đích xuất kết quả**, không dùng làm dữ liệu đầu vào cho màn hình thiết lập chủ đề. Hiện có overview tại B6:J10 và các block brief chi tiết phía dưới; BR02 là công cụ, BR04 là file Excel, cả hai không tính vào quota ARTICLE. BR01 overview P1/Đang viết xung đột với phần detail P0/Chờ xác minh SERP — phải có QA đồng bộ trước khi export. Keyword chính gốc P01.1 `lương gross net là gì` và proposed output `lương gross là gì` cũng cần decision trong Approval Queue; không được thay tự động.

## 2. Kết quả đọc nguồn ngày 20/11/2026

- Topic Pillar: header bắt đầu tại A4; 25 Topic Pillar P01–P25 đủ các trường cốt lõi; thêm P26 nhưng thiếu Loại topic, Trục chia, Chủ đề chính => REVIEW, không tự điền.
- Keywords: header A1, 299 dòng keyword, tạo thành 63 mã nội dung. P01 có hai mã P01.1-① (1 Chính + 5 Phụ), P01.2-② (1 Chính + 5 Phụ).
- TOFU/MOFU/BOFU là phễu/hành trình nội dung **từ nguồn**; không phải `Intent (Semrush)`.
- Không có Volume, KD/Intent Semrush, không suy đoán.

## 3. Ánh xạ các trường nguồn vào màn hình Thiết lập chủ đề

| Tab/cột nguồn | Field nội bộ | Form hiển thị | Ràng buộc |
|---|---|---|---|
| `Topic Pillar`.`Mã` | `topicCode` | Mã Topic Pillar | Bắt buộc, duy nhất |
| `Topic Pillar`.`Topic pillar` | `topicName` | Tên Topic Pillar | Bắt buộc |
| `Topic Pillar`.`Pillar` | `pillar` | Pillar | Bắt buộc |
| `Topic Pillar`.`Loại topic` | `topicType` | Loại topic | Bắt buộc |
| `Topic Pillar`.`Trục chia của pillar` | `axis` | Trục chia | Bắt buộc |
| `Topic Pillar`.`Chủ đề chính bên trong` | `mainTopics` | Các chủ đề được cho phép | Bắt buộc |
| `Keywords`.`Mã nội dung gốc` | `contentCode` | Mã nội dung | Chọn theo Topic Pillar |
| `Keywords`.`Chủ đề` | `contentTitle` | Tên nội dung | Theo mã nội dung |
| `Keywords`.`Nội dung gốc` | `originalTitle` | Bản mô tả mục tiêu gốc | Lưu theo nguồn |
| `Keywords`.`Key` + `Loại` | `primary`, `secondaries` | Keyword chính/phụ | Giữ vai trò gốc, 1 Chính nếu có |
| `Keywords`.`Giai đoạn` | `funnelSource` | Nhãn nguồn | Giữ TOFU/MOFU/BOFU, KHÔNG phải Semrush Intent |
| `Keywords`.`Kiểm chứng` | `verificationSource` | Ghi chú từ nguồn | Không coi là SERP đã chứng minh |
| Không có | `businessGoal`, `audience` | Mục tiêu & đối tượng | Người dùng nhập thủ công, không tự đoán |
| Không có | `volume`,`kd`,`semrushIntent` | Không điền lúc thiết lập | Chỉ lấy từ Semrush file upload bước sau |

## 4. Luồng upload/preview/confirm

1. Bước 1 **Thiết lập chủ đề**: nút `Chọn file từ máy`. Chấp nhận `.xlsx` (ưu tiên đủ hai tab) hoặc `.csv` (một bảng trên một file; có thể gửi bảng thứ hai để ghép).
2. Server local `POST /api/topic-source-preview` nhận bytes <=5MB, giải mã UTF-8/cp1258 CSV hoặc đọc XLSX bằng openpyxl; chỉ đọc trong RAM. Không truyền dữ liệu lên SaaS.
3. Tìm dòng header theo các alias (không hardcode tên tab/tọa độ; hỗ trợ header ở dòng 4). Chỉ phân loại schema `taxonomy` và `keywords`, bỏ qua Course Structure, Lesson Package, Checklist Lesson.
4. Validate topic bắt buộc, mã lặp, mã nội dung không match, số keyword Chính theo mã. Hiển thị cảnh báo có nguồn tab/dòng, đặc biệt P26 chưa đủ trường.
5. Hiển thị số liệu về số Topic Pillar, mã nội dung và keyword đã đọc; cho chọn Topic Pillar và mã nội dung trong dropdown. Ví dụ P01 hiển thị P01.1 và P01.2.
6. Nút `Điền thông tin vào form` chỉ đưa dữ liệu vào bản nháp (`setupDraft`). Chưa tự lưu project; người dùng kiểm tra `businessGoal`, `audience`, seed và nhấn `Lưu dự án`.
7. Khi đổi Topic Pillar từ P01 sang P08, **xóa mục tiêu/độc giả cũ**; không để dữ liệu kinh doanh thuộc topic trước đi theo.
8. Lưu toàn bộ nhóm mã nguồn cùng Topic Pillar trong project để bước sau tham khảo; không chỉ lưu mã đang chọn. Giữ dòng dữ liệu, tab, filename, trạng thái và version.
9. Lệnh `Tạo nhóm sơ bộ từ mã nội dung nguồn` tạo các SOURCE_GROUP để người dùng nhìn cấu trúc. Đó **không** phải các Search Intent đã xác minh.
10. Không dùng cùng route với import Semrush. `POST /api/import-preview` chỉ dành cho metric report.

## 5. Bản đồ nhu cầu là gì, tại sao cần bước này?

**Keyword** là chuỗi chữ người dùng tìm. **Nhu cầu (search need)** là vấn đề thực chất họ muốn giải quyết. Hai cụm keyword khác nhau có thể phục vụ **cùng một nhu cầu**; một mã nội dung gốc có thể bao gồm **nhiều nhu cầu**.

Ví dụ trong P01.1, file có `lương gross net là gì`, `cách đọc phiếu lương`, `công cụ tính lương gross sang net`. Người dùng có thể lần lượt muốn: hiểu khái niệm, đọc chứng từ, hoặc dùng một công cụ. Không thể mặc định cả ba thuộc cùng một bài ARTICLE hay ba bài ARTICLE. Cần kiểm chứng SERP.

### Mục tiêu
1. Bảo đảm gợi ý AI không vượt ra khỏi Pillar / Loại topic / Trục chia / Chủ đề chính.
2. Gom các keyword đồng intent để tránh cannibalization và trùng nội dung.
3. Phát hiện nhánh nhu cầu cần bổ sung, ví dụ thuế TNCN **từ lương** hợp P01, còn thuế freelancer thuộc P02.
4. Xác định yêu cầu dữ liệu Semrush phù hợp với từng nhóm, giảm số lần bạn phải xuất file.
5. Quyết định nhóm nào có khả năng trở thành bài độc lập sau kiểm chứng SERP; có thể chỉ 4 bài và 3 khoảng trống nghiên cứu, không ép đủ 7.

### Input → Output → Gate
- **Input:** taxonomy + tất cả mã nội dung/keyword nguồn đã nhập + mục tiêu/độc giả + các quyết định duyệt trước đó.
- **Output:** DemandGroup `{user_need, representative_seed, source_keyword_refs, taxonomy_evidence, topic_scope, overlap_candidates, research_questions, evidence_state}`.
- **Gate:** Provisional source group `SOURCE_GROUP` khác với validated demand group. AI chưa kết nối ở prototype; người dùng có thể tạo nhóm thủ công. Khi có AI, mọi đề xuất vẫn phải được review.

### Không phải việc của Bản đồ nhu cầu
- Không tính Volume/KD; không định nghĩa SERP từ tưởng tượng; không chọn keyword chính chỉ vì Volume cao; không tự tạo đủ 7 brief; không thay vai trò keyword gốc.

## 6. Phân biệt nhóm nguồn với nhóm nhu cầu

**Bộ nguồn P01** chứa 2 mã nội dung và 12 keyword. Sau import và click `Tạo nhóm sơ bộ`, app hiển thị **2 SOURCE_GROUP**. Đây là số mã nội dung, **không phải** bằng chứng P01 chỉ có hai nhu cầu, không phải hai bài đã đủ điều kiện viết. Module AI ở milestone tiếp theo mới phân tích tách/gộp các nhu cầu và đánh dấu các điểm phải kiểm chứng.

## 7. Rule và bảo vệ

- Không hardcode `P01`, `Luong`, `FinZ` trong parser/gate; P01 chỉ là fixture.
- Bắt buộc nhận diện schema bằng nội dung header; không dựa vào `active sheet` hoặc `sheet1`.
- Dữ liệu gốc không phải Semrush verified metrics. `reportedVolume` ở tab Keywords vẫn là nguyên bản nguồn, không nâng cấp thành Semrush Volume.
- Mọi đề xuất thay keyword chính, chuyển pillar hoặc tách/gộp article đều cần approval.
- File upload được nhận trên 127.0.0.1; giới hạn kích thước, loại file; không gửi lên mạng. Prototype chỉ lưu JSON/metadata trong localStorage, không lưu bản raw XLSX và chưa có SQLite.
- Cần xử lý an toàn khi file có cột lạ, thiếu header, mã trùng; hiển thị warnings. Không xoá dữ liệu source bị lỗi âm thầm.
- Test chuyển P01 → P08 không sửa code; P26 không tự điền; 299 keywords vẫn giữ đủ.

## 8. Kiến trúc code

```text
prototype/
  server.py              # 2 endpoint độc lập: source preview và semrush preview
  topic_source_import.py # tự dò header + phân nhóm các content code
  app.js                 # thao tác upload / chọn topic / áp vào form / tạo SOURCE_GROUP
  index.html, styles.css
  tests/test_topic_source_import.py
```

### Backend API

`POST /api/topic-source-preview` Content-Type `application/octet-stream` + header `X-File-Name` trả JSON:

```json
{
  "formatVersion": 1,
  "detected": {"taxonomyTab": "Topic Pillar", "taxonomyHeaderRow": 4, "keywordTab": "Keywords", "keywordHeaderRow": 1},
  "topics": [], "incompleteTopics": [], "contentGroups": [], "orphanKeywords": [],
  "stats": {"validTopics": 25, "incompleteTopics": 1, "keywordRows": 299, "contentCodes": 63, "orphanKeywords": 0, "complete": true},
  "warnings": []
}
```

`POST /api/import-preview` tiếp tục dành riêng cho báo cáo Semrush, không thay đổi.

## 9. Hướng dẫn sử dụng

```
cd prototype
py -m pip install -r requirements.txt
py server.py 5173
```

Mở http://127.0.0.1:5173 → `Thiết lập chủ đề` → `Chọn file từ máy` → chọn `Bộ key FinZ.xlsx` (export nguyên workbook) hoặc `fixtures/FINZ_TOPIC_IMPORT_READY.xlsx` (bản chuẩn hóa) → chọn P01/P08/... và mã nội dung → `Điền thông tin vào form` → thêm mục tiêu và độc giả → `Lưu dự án` → `Bản đồ nhu cầu` → `Tạo nhóm sơ bộ từ mã nội dung nguồn`.

## 10. Bước phát triển tiếp với Codex

- Thay localStorage bằng SQLite + Alembic để giữ snapshot từng lần import, filename, SHA256, source row, approvals.
- Cho người dùng quản lý nhiều dự án mà không phải xóa/reset state của dự án khác.
- Bổ sung trang so sánh data source trước/sau, chọn gộp/trùng mã nội dung và rollback import.
- Sau khi xong data intake, tích hợp LLM provider để đề xuất DemandGroup với bằng chứng taxonomy; nguồn Semrush vẫn là CSV/XLSX upload thủ công.
- Riêng xuất Content Brief: dùng template layout output, nhưng thông tin metrics/intent/brief không lấy trực tiếp từ nguồn Topic Pillar, chỉ tạo sau các gate F1–F7.
