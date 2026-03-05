from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.documents import router as documents_router

app = FastAPI(
    title="DocSearch API",
    version="0.1.0",
)

app.include_router(documents_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    # Ensure consistent {error, code} response shape.
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "code": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    # FastAPI defaults to 422 with {"detail": ...}; convert to the required-ish shape.
    # Keep `details` for debugging (optional).
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "code": 422, "details": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    # Avoid leaking internals; in a real system you'd log `exc` with stacktrace.
    return JSONResponse(status_code=500, content={"error": "Internal server error", "code": 500})
