# FinZ SEO Workbench V1.5 — SQLite + AI Demand Intelligence + Manual Semrush Loop

> Cập nhật UX 21/11/2026: luồng chính gồm 7 bước: Thiết lập → Bản đồ nhu cầu → Yêu cầu Semrush → Upload/ghép cột → Kiểm tra dữ liệu → Kế hoạch dự thảo → Brief/xuất (đang khóa). Chờ phê duyệt là màn hình kiểm soát riêng. Không còn route nhập SERP thủ công; tham chiếu cũ bên dưới chỉ mô tả lịch sử. Dữ liệu SERP cũ được giữ trong SQLite, không suy thành SERP đã xác minh.
> Trạng thái kỹ thuật `PROCESS_COMPLETED` chỉ sau xác nhận SQLite; không đồng nghĩa `QUALITY_APPROVED`. Thiếu SERP hiển thị `SERP_NOT_VERIFIED`, được xem dự thảo nhưng không READY_FOR_BRIEF. Popup tự chuyển sau 2 giây chỉ khi navigationEligible, không có preview, approval pending hoặc Critic yêu cầu nghiên cứu lại. Đổi trang/dự án, đóng hoặc ở lại hủy timer.

## Trạng thái implementation

**Đã thực thi bằng mã trong `prototype/`:** lưu/load/list nhiều dự án bằng SQLite, lưu file Semrush gốc và toàn bộ dòng chuẩn hóa (giới hạn 25.000 dòng/file), đếm dòng thiếu dữ liệu, kiểm tra keyword gốc có metric hay chưa từ toàn bộ evidence DB, API chạy AI phân tích nhu cầu và vòng phản biện AI **khi một LLM Provider được cấu hình**, và UI gọi các endpoint tương ứng. Đã kiểm thử unit + HTTP backend với nguồn mẫu.

**Chưa hoàn thiện:** trực tiếp đánh giá SERP top 10 tự động; SERP overlap clustering đã xác minh; sàng lọc content gap theo website; bài viết `READY_FOR_BRIEF`; API async streaming/worker; chứng minh hiệu quả xếp hạng. Việc bật model thật vẫn cần người vận hành cấu hình model có sẵn hoặc API.

## Nguồn dữ liệu và các bất biến

- **Không kết nối** Google Sheets, Semrush API/MCP, WordPress. Nhập file taxonomy/keyword qua form ở bước 01; Semrush được dùng thủ công qua UI bên thứ ba, dữ liệu quay về app qua file CSV/XLSX.
- Taxonomy/Keyword do người dùng nhập là nguồn gốc. Chỉ thay keyword chính khi người dùng phê duyệt. `P01` chỉ là fixture, dữ liệu mới không cần sửa mã nguồn.
- `5–7` bài là mục tiêu mềm; 4 cơ hội + 3 research gaps hợp lệ.
- Không tạo hoặc suy đoán `Volume`, `KD`, `Intent` khi chưa có file.
- Search Intent do AI hoặc nhãn Semrush cung cấp không thay thế kiểm chứng kiểu trang và kết quả Organic SERP.
- Không kết luận đủ điều kiện viết bài nếu thiếu bằng chứng SERP, kiểm tra trùng bài và phê duyệt.
- Đề xuất AI phải lưu lý do + mã nguồn hợp lệ; mã nguồn không hợp lệ bị đánh dấu `UNCERTAIN`.
- Mọi lệnh upload, chạy AI và duyệt do người dùng bấm; không tự lặp vô hạn hay tự xuất bản.

## Luồng 01 — Thiết lập chủ đề lưu DB

1. Tải Excel có các tab `Topic Pillar` + `Keywords`, hoặc nhập bằng form. Tách `Pillar`, `Loại topic`, `Trục chia`, `Chủ đề chính`, mã nội dung và keyword gốc.
2. Chọn Topic Pillar/mã nội dung, xem trước form tự điền; bổ sung mục tiêu kinh doanh và độc giả.
3. Bấm **Lưu dự án**; app đồng bộ JSON state có source snapshot vào SQLite table `projects`, lưu nhật ký sự kiện trong `project_events`.
4. Có thể tạo nhiều dự án, mở lại ở `Thiết lập chủ đề` qua danh sách dự án đã lưu, không mất P01 khi sang P08/P99.
5. `localStorage` chỉ còn là bản nháp dự phòng cho HTML standalone. Khi chạy server Python trên localhost, SQLite là nơi lưu dài hạn.

**Rủi ro lưu trữ:** Chưa có locking tối ưu cho nhiều tab và recovery sau xung đột; ứng dụng chỉ dành cho single-user local. Không xóa folder `.finz_local_data/` khi muốn giữ dữ liệu. Nên backup định kỳ (SQLite + thư mục `uploads`).

## Luồng 02A — AI Demand Intelligence trước Semrush

- UI bấm **AI phân tích nhu cầu**; backend đọc state từ SQLite.
- Analyst đề xuất `DemandGroup`, seed mới, nhóm đang thiếu, phân loại phạm vi, kiểu trang giả định, và những báo cáo cần lấy thủ công.
- Critic là lượt gọi LLM thứ hai, phản biện: phạm vi taxonomy, nguy cơ trùng nhu cầu, keyword không phù hợp business, yêu cầu SERP, công cụ so với blog.
- Backend lọc JSON, kiểm tra `source_refs` đúng các mã có thật, không tin số liệu tưởng tượng từ model.
- UI hiển thị nhóm như `RESEARCH_CANDIDATE` và cho phép người dùng **đưa nhóm vào bản đồ** hoặc **tạo phiếu Semrush** bằng thao tác riêng; không auto-publish.

## Luồng 02B — Bạn xuất báo cáo trong Semrush UI

Mẫu phiếu yêu cầu:

```json
{
  "seed": "lương gross net là gì",
  "report": "KEYWORD_OVERVIEW",
  "market": "VN",
  "instructions": "Mở Semrush UI -> tìm đúng keyword -> chọn database Việt Nam -> xuất CSV/XLSX với Keyword, Volume, KD, Intent, SERP Features -> upload theo request ID",
  "purpose": "Kiểm tra nhu cầu tìm kiếm/độ khó; chưa xác nhận Search Intent bằng SERP"
}
```

Các report type: `KEYWORD_OVERVIEW`, `RELATED`, `QUESTIONS`, `ORGANIC_RESULTS`. Nếu Semrush UI bên thứ ba không xuất được đủ cột/URL, tool chỉ yêu cầu các trường có thể lấy và để người dùng nhập SERP thủ công. Tuyệt đối không yêu cầu token hoặc quyền truy cập tài khoản Semrush bên thứ ba.

## Luồng 02C — Full-file evidence & Critic sau upload

1. Chọn đúng Research Request và upload CSV/XLSX.
2. Xem trước 200 dòng + chọn mapping cột. Sau xác nhận, server đọc **toàn bộ** file đến 25.000 dòng và ghi `file_uploads`, `research_batches`, `evidence_rows` vào SQLite. Dữ liệu gốc không mất.
3. Bộ kiểm tra số lượng/định dạng nhận diện Volume sai locale, KD ngoài 0–100, Intent thiếu, keyword trùng. Số liệu thiếu để `null`, không thay thành zero.
4. Bấm **Kiểm tra keyword gốc trong DB** để tìm chính xác seed thiếu dữ liệu bằng cách quét tất cả observation đã lưu, không chỉ mẫu 300 dòng cho model.
5. Nếu còn thiếu: tạo phiếu Overview/Related/Questions phù hợp, lặp lại upload. Nếu đã có Volume/KD/Intent: chuyển trạng thái `SERP_REQUIRED`, không tự tuyên bố `READY_FOR_BRIEF`.
6. Bấm **AI phản biện dữ liệu Semrush** (cần LLM), model nhận tóm tắt evidence, đối chiếu giả định và đề nghị kiểm tra tiếp. UI giới hạn mặc định **2 lượt** phản biện trong một chu kỳ, không tự chạy thêm.
7. Sau khi có SERP và approval, mới triển khai F5/F6 (SERP clustering/mapping) ở milestone sau. V1.5 chưa đánh dấu bài chính thức đủ điều kiện.

## Quy tắc đánh giá SEO

**Tách trạng thái, không tính một điểm số bí ẩn:**

| Gate | Bằng chứng | Trạng thái |
|---|---|---|
| Taxonomy | Pillar/Topic/Scope và mã nguồn | PASS / REVIEW / OUT_OF_SCOPE |
| Metric source | File Semrush + locale + provenance | RESEARCH_REQUIRED / METRICS_AVAILABLE |
| Business relevance | Mục tiêu/đối tượng và vấn đề cần giải quyết | REVIEW / PASS |
| SERP | URL organic, dominant page type, trùng intent | SERP_REQUIRED / REVIEW / PASS |
| Cannibalization | Kế hoạch nội bộ và URL mục tiêu | REVIEW / PASS |
| Human approval | Quyết định thực hiện của bạn | PENDING / APPROVED |

**Cấm** `READY_FOR_BRIEF` từ các gate trên nếu thiếu bất cứ bằng chứng bắt buộc nào. Không có KD hay Volume nào bảo đảm thứ hạng: ưu tiên chiến lược liên tục cân bằng volume, khả năng cạnh tranh, nhu cầu thực, B2B value và nguồn lực.

## GitHub reference architecture — không đưa trực tiếp vào runtime

1. [Black-coffe/sito](https://github.com/Black-coffe/sito): local-first import/clean/enrich/group/restore/snapshot, MIT, v0.1 nên review trước khi tích hợp.
2. [johnoconnor0/keyword-clustering](https://github.com/johnoconnor0/keyword-clustering): Python semantic + TF-IDF + SERP clustering, MIT; chi phí embed model cần xem xét và test keyword Việt.
3. [iannuttall/seo](https://github.com/iannuttall/seo): data provenance, file import, findings/evidence; Apache 2.0, CLI/MCP optional.
4. [semrush/skills](https://github.com/semrush/skills): tham khảo checklist keyword-research/serp-analysis; runtime gốc cần Semrush MCP nên không sao chép cơ chế thực thi.

## API local (đã triển khai)

| Endpoint | Mục đích |
|---|---|
| `GET /api/health` | Trạng thái backend, DB, AI provider (không lộ key) |
| `GET /api/projects/list` | Liệt kê dự án đã lưu |
| `GET /api/projects/{id}` | Nạp trạng thái dự án |
| `POST /api/projects/save` | Lưu/sửa dự án SQLite |
| `POST /api/topic-source-preview` | Xem trước taxonomy Excel |
| `POST /api/import-preview` | Xem trước Semrush export + lưu raw file chờ xác nhận |
| `POST /api/import-confirm` | Mapping + ghi đủ dòng normalized vào DB |
| `POST /api/research/gaps` | Thiếu metrics nào, cần report nào? |
| `GET /api/research/evidence?projectId=...` | Evidence sample, thống kê full-file |
| `GET /api/ai/status` | Model cấu hình chưa |
| `POST /api/ai/topic` | Analyst + Critic trước Semrush |
| `POST /api/ai/critic` | Critic dựa trên file Semrush đã lưu |

## Cấu hình AI thật

AI không tự bật vì không được biết API key của bạn. Chọn một trong hai:

**Ollama trên máy (dùng API tương thích OpenAI, không cần Semrush API):**

```dotenv
AI_PROVIDER=ollama
AI_BASE_URL=http://127.0.0.1:11434/v1/chat/completions
AI_MODEL=<tên mô hình đã cài trên Ollama>
AI_API_KEY=
```

**Một nhà cung cấp OpenAI-compatible qua HTTPS:**

```dotenv
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://<provider-endpoint>/v1/chat/completions
AI_MODEL=<model-id>
AI_API_KEY=<api-key>
```

Lưu vào `.env.local` tại thư mục gốc dự án và chạy lại server. **Chỉ nhập endpoint của nhà cung cấp tin cậy**. Với provider ngoài máy, taxonomy, keyword và dữ liệu evidence chọn lọc sẽ rời máy tới provider; cân nhắc dữ liệu kinh doanh bí mật. File `.env.local` đã được gitignore. `AI_PROVIDER=disabled` mặc định và không sinh kết quả AI giả.

## Kiểm thử đề nghị trước khi dùng thật

- Mở P01 và P08 ở hai project riêng, reload trình duyệt vẫn còn.
- Tải file Semrush >200 dòng, sau import phải lưu đủ dòng trong SQLite và `stats` đếm trên toàn file.
- Thiếu Volume, KD, Intent: chỉ xuất `RESEARCH_REQUIRED`, không tự điền số.
- Có đủ metrics: chuyển `SERP_REQUIRED`, không tự xuất Content Brief.
- Thử keyword giao thoa P01/P25: AI phải đánh dấu review, không tự nhập vào P01.
- Thử mô hình AI tắt: nút AI bị khóa và UI không tuyên bố đã phân tích.
- Thử provider AI thật có JSON schema; output thiếu hoặc lỗi phải hiển thị rõ và không tạo đề xuất từ một phần dữ liệu.
