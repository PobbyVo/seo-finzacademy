from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException


class AppError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message_vi: str,
        next_action_vi: str,
        fields: list[str] | None = None,
    ):
        self.status = status
        self.code = code
        self.message_vi = message_vi
        self.next_action_vi = next_action_vi
        self.fields = fields or []


def response(request: Request, error: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status,
        content={
            "error": {
                "code": error.code,
                "message_vi": error.message_vi,
                "fields": error.fields,
                "next_action_vi": error.next_action_vi,
                "request_id": request.state.request_id,
            }
        },
    )


def register_handlers(app):
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError):
        return response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        fields = [".".join(map(str, item["loc"][1:])) or "body" for item in exc.errors()]
        return response(
            request,
            AppError(
                422,
                "VALIDATION_ERROR",
                "Dữ liệu không hợp lệ. Tên dự án cần từ 1 đến 120 ký tự; "
                "mã topic không được trống.",
                "Kiểm tra các trường được chỉ ra và gửi lại.",
                fields,
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return response(
            request,
            AppError(
                exc.status_code,
                "HTTP_ERROR",
                "Không tìm thấy tài nguyên hoặc thao tác.",
                "Kiểm tra đường dẫn và phương thức HTTP.",
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, _exc: SQLAlchemyError):
        return response(
            request,
            AppError(
                503,
                "DATABASE_UNAVAILABLE",
                "Cơ sở dữ liệu local chưa sẵn sàng.",
                "Chạy alembic upgrade head trong services/api rồi thử lại.",
            ),
        )
