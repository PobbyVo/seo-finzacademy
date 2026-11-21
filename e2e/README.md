# Kiểm thử trình duyệt M0

Cài dependency frontend/backend theo README ở thư mục gốc, rồi cài bộ test:

```sh
npm --prefix e2e ci
```

Nếu máy chưa có Google Chrome (tự nhận trên macOS), cài Chromium dùng riêng cho Playwright:

```sh
cd e2e
npx playwright install chromium
cd ..
```

Từ thư mục gốc, chạy:

```sh
npm --prefix e2e run typecheck
npm --prefix e2e test
```

`npm test` tự tạo SQLite tạm, chạy Alembic migration, mở FastAPI tại `127.0.0.1:18000` và Next.js tại `127.0.0.1:13000`, kiểm thử rồi dừng các tiến trình và xóa DB tạm. Dữ liệu dự án đang dùng không bị thay đổi. Next.js dùng thư mục build `.next-e2e` riêng.

Có thể đổi cổng bằng `E2E_API_PORT` / `E2E_WEB_PORT`, đổi Python bằng đường dẫn `FINZ_PYTHON`, chọn Chrome đã cài bằng `PLAYWRIGHT_CHANNEL=chrome`. Mặc định Python ở `services/api/.venv/bin/python` (Windows: `.venv/Scripts/python.exe`).

Các test kiểm tra tạo dự án trống, nạp demo theo click, giữ vai trò/giai đoạn từ nguồn, metric thiếu, nhiều dự án độc lập, tải lại, layout mobile và lỗi kết nối/retry. Trình duyệt cũng được kiểm tra không phát sinh request tới domain bên ngoài.

Để test server do bạn tự chạy thay cho launcher:

```sh
E2E_BASE_URL=http://127.0.0.1:3000 PLAYWRIGHT_CHANNEL=chrome npm --prefix e2e run test:external
```

Chế độ `test:external` tạo hai dự án kiểm thử trong DB của server đã chọn; dùng server/DB thử nghiệm riêng. `E2E_EXPECT_EMPTY=1` bật kiểm tra DB ban đầu rỗng (launcher tự đặt biến này).
