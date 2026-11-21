# FINZ SEO ASSISTANT — M0 local scaffold

Nền tảng **Next.js + TypeScript + TailwindCSS**, **FastAPI + Pydantic + SQLAlchemy**, **SQLite + Alembic**. M0 có trang `/projects`, tạo/chọn dự án trống, nạp fixture demo theo lựa chọn, API health và dữ liệu lưu trên máy. Giao diện luôn gắn nhãn **DEMO - CHƯA PHÂN TÍCH AI THỰC**.

Không cần tài khoản hoặc API key. Runtime M0 chỉ gọi backend local, không gọi Semrush, Google Sheets/Drive, WordPress hoặc LLM. Cần internet khi cài thư viện lần đầu; sau khi cài và build có thể chạy local mà không cần các dịch vụ này.

## 1. Chuẩn bị

Cần **Node.js 24 LTS**, npm, **Python 3.12+**. Các lệnh dưới đây dành cho macOS/Linux, chạy từ thư mục gốc dự án:

```sh
cd /Users/vodaiphuoc/Downloads/finz-seo-assistant
cp .env.example .env
python3.12 -m venv services/api/.venv
services/api/.venv/bin/python -m pip install -c services/api/requirements-dev.lock -e './services/api[dev]'
npm --prefix apps/web ci
```

Nếu máy chỉ có Python 3.9 và đã cài `uv`, dùng hai lệnh sau thay cho hai lệnh Python ở trên:

```sh
uv venv --python 3.12 services/api/.venv
uv pip install --python services/api/.venv/bin/python -c services/api/requirements-dev.lock -e './services/api[dev]'
```

Không ghi đè `.env` đã cấu hình. Các giá trị mặc định đủ để chạy M0. Cấu hình `.env.local.example` thuộc prototype cũ, không dùng để bật AI trong M0.

## 2. Khởi động

Tại thư mục gốc, chỉ cần một terminal:

```sh
npm run dev
```

Lệnh tự chạy migration SQLite, đợi backend sẵn sàng rồi mở frontend. Truy cập **http://127.0.0.1:3000/projects**; nhấn `Ctrl+C` để dừng cả hai. Log có nhãn `[DB]`, `[BE]`, `[FE]`. Không cần cài thêm dependency cho launcher; frontend/backend cần được cài một lần theo mục 1. Nếu cổng 3000 hoặc 8000 bận, lệnh báo lỗi để bạn dừng server cũ trước; không tự tắt tiến trình đang chạy.

Có thể chạy riêng từng phần để debug. Terminal thứ nhất, tại thư mục gốc:

```sh
make api
```

Lệnh này chạy `alembic upgrade head` trước khi mở FastAPI tại **http://127.0.0.1:8000**. Tương đương:

```sh
cd services/api
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn finz_api.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal thứ hai, tại thư mục gốc:

```sh
make web
```

Mở **http://127.0.0.1:3000/projects**. Dừng từng server bằng `Ctrl+C`. Nếu không dùng `make`, chạy `npm --prefix apps/web run dev` từ thư mục gốc.

Kiểm tra backend:

```sh
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/api/v1/health
```

Cả hai trả HTTP 200 với `status: "ok"`, `mode: "DEMO"`, `database: "ok"`, `api_version: "v1"`. Tài liệu API local: **http://127.0.0.1:8000/docs**. Nếu thiếu migration, health báo lỗi thực; chạy lại `make migrate`.

Để chạy frontend đã build:

```sh
make build-web
npm --prefix apps/web run start
```

FastAPI vẫn cần chạy ở terminal riêng. Next.js chuyển tiếp `/api/v1/*` tới backend; `API_BASE_URL` trong `apps/web/.env.local` chỉ cần nếu đổi địa chỉ backend (xem `apps/web/.env.example`). Đổi giá trị này thì khởi động lại dev server; nếu chạy production thì build lại. Nếu cổng 3000 bận, dừng tiến trình đang dùng cổng hoặc chọn cổng khác bằng `--port`; mặc định nên dùng đúng 3000.

## 3. Thử giao diện M0

1. Lần đầu danh sách dự án trống, không tự nạp P01.
2. Nhập tên rồi bấm **Tạo dự án**. Dự án trống được lưu thật vào SQLite.
3. Chọn một chủ đề demo rồi bấm **Nạp demo**. Chọn P01 để xem taxonomy, hai mã nội dung và ba keyword trong fixture minh họa hiện có.
4. Volume/KD/Intent/SERP chưa có dữ liệu và vẫn là `null`. Nhãn TOFU/MOFU/BOFU là phễu từ nguồn, không phải Semrush Intent.
5. Tạo dự án thứ hai hoặc chọn chủ đề demo khác trong dự án mới; đổi dự án và reload để kiểm tra dữ liệu độc lập.

Dự án đã nạp demo không được ghi đè bằng chủ đề khác. Tạo dự án mới để thử fixture khác. M0 mới có trường tên dự án; form taxonomy/mục tiêu/độc giả đầy đủ, chỉnh sửa nguồn và CRUD thuộc M1. Fixture demo không phải bộ nguồn đầy đủ trong workbook gốc.

## 4. Kiểm thử

Sau khi cài dependencies:

```sh
make check
make build-web
```

`make check` chạy `pytest`, Ruff, ESLint và TypeScript typecheck. Dependency npm được khóa bằng `package-lock.json`; backend dùng `requirements-dev.lock`. Lệnh riêng:

```sh
make test-api
make lint-api
make lint-web
make typecheck
```

Kiểm thử trình duyệt và hướng dẫn môi trường nằm trong [e2e/README.md](e2e/README.md). Suite dùng SQLite riêng, không cần tài khoản hay gọi dịch vụ SEO/AI. Chạy:

```sh
npm --prefix e2e ci
make test-e2e
```

## 5. Cấu trúc và lưu dữ liệu

```text
apps/web/          Next.js App Router, UI tiếng Việt, API client
services/api/      FastAPI, SQLAlchemy, Pydantic, Alembic, pytest
fixtures/          dữ liệu minh họa; không tự nạp lúc startup
e2e/               smoke tests trình duyệt thật
prototype/         demo tham khảo cũ, không phải ứng dụng Next.js/FastAPI M0
docs/              đặc tả và nhật ký kiểm thử
```

SQLite M0 dùng file riêng theo `DATABASE_URL` trong `.env`; đường dẫn tương đối được tính từ root dự án. Giữ file DB khi muốn giữ dự án. Mỗi lần tạo/nạp demo lưu snapshot và audit; M0 chưa có UI duyệt lịch sử hay backup/restore. Không tự nhập hoặc thay đổi `.finz_local_data/` và dữ liệu của prototype. Để sao lưu SQLite, dừng FastAPI rồi sao chép file DB cùng các file journal/WAL nếu có.

## 6. Phạm vi và tài liệu

**Chỉ M0 đã được triển khai.** Chưa có Workbench tám bước, AI Analyst/Critic, nhập taxonomy/keyword thật, upload CSV/XLSX, Semrush Research Requests, SERP, mapping, approval hay xuất Content Brief. M0 không tuyên bố dữ liệu đã sẵn sàng viết bài.

Nguồn quy tắc: [AGENTS.md](AGENTS.md), [SPEC_FULL.md](docs/SPEC_FULL.md), [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md), [CODEX_START_M0.md](prompts/CODEX_START_M0.md). Hai đường dẫn `docs/FINZ_SEO_ASSISTANT_SPEC.md` và `harness/build/M0-scaffold.md` trong yêu cầu không tồn tại trong bộ nguồn này; các tài liệu tương ứng hiện có được dùng và ghi lại trong [DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md).

UI/workflow các milestone sau theo [UX_LOCAL_WORKBENCH_V1_3.md](docs/UX_LOCAL_WORKBENCH_V1_3.md), [STATE_MACHINE_AND_EVENTS.md](docs/STATE_MACHINE_AND_EVENTS.md), bổ sung source import [V1.4](docs/TOPIC_SOURCE_IMPORT_AND_DEMAND_MAP_V1_4.md) và nghiên cứu [V1.5](docs/V1_5_DB_AI_RESEARCH_LOOP.md). Prototype giữ nguyên, xem [prototype/README.md](prototype/README.md); không dùng khả năng của prototype để đánh giá M0 đã hoàn tất tính năng tương ứng.

Bước được khuyến nghị tiếp theo là **M0.5 — Local Workbench UI**; chỉ thực hiện khi được yêu cầu.
