from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        request_id: str,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id


async def app_error_handler(
    request: Request,
    exc: AppError,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "request_id": exc.request_id,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )