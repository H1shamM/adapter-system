from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.api.main import app


async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.staus_code,
        content={"content": exc.detail}
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return await http_exception_handler(
        request= request,
        exc=HTTPException(400, str(exc))
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

class NotFoundException(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=404, detail=detail)

# Add handler
@app.exception_handler(NotFoundException)
async def not_found_handler(request, exc):
    return await http_exception_handler(request, exc)
