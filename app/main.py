from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import HTMLResponse
from html import escape

from app.api.documents import router as documents_router
from app.store.memory import store

app = FastAPI(
    title="DocSearch API",
    version="0.1.0",
)

app.include_router(documents_router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    docs = store.list()

    def cell(value: str) -> str:
        return escape(value, quote=True)

    rows = "\n".join(
        f"""
        <tr>
          <td class="mono">{cell(d.id)}</td>
          <td>{cell(d.title) if d.title else '<span class="muted">—</span>'}</td>
          <td class="num">{d.version}</td>
          <td class="num">{len(d.text)}</td>
        </tr>
        """.strip()
        for d in docs
    )

    if not rows:
        rows = """
        <tr>
          <td colspan="4" class="muted">No documents yet. Create one via <a href="/docs">/docs</a>.</td>
        </tr>
        """.strip()

    html = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>DocSearch</title>
        <style>
          :root {{
            color-scheme: light dark;
            --bg: #0b1020;
            --panel: rgba(255,255,255,.06);
            --border: rgba(255,255,255,.14);
            --text: rgba(255,255,255,.92);
            --muted: rgba(255,255,255,.64);
            --link: #7dd3fc;
          }}
          body {{
            margin: 0;
            font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Apple Color Emoji",
              "Segoe UI Emoji";
            background: radial-gradient(1200px 800px at 20% 0%, rgba(56, 189, 248, .14), transparent 60%),
              radial-gradient(900px 600px at 80% 20%, rgba(167, 139, 250, .12), transparent 55%),
              var(--bg);
            color: var(--text);
          }}
          .wrap {{
            max-width: 980px;
            margin: 0 auto;
            padding: 28px 18px 42px;
          }}
          header {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 18px;
          }}
          h1 {{
            font-size: 20px;
            margin: 0;
            letter-spacing: .2px;
          }}
          .muted {{ color: var(--muted); }}
          a {{ color: var(--link); text-decoration: none; }}
          a:hover {{ text-decoration: underline; }}
          .panel {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            overflow: hidden;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
          }}
          th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
          }}
          th {{
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: .08em;
            color: var(--muted);
            background: rgba(255,255,255,.04);
          }}
          tr:last-child td {{ border-bottom: none; }}
          .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
          .num {{ text-align: right; white-space: nowrap; }}
          .sub {{
            display: flex;
            gap: 10px;
            align-items: center;
            color: var(--muted);
            font-size: 13px;
          }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <header>
            <div>
              <h1>DocSearch</h1>
              <div class="sub">
                <span>{len(docs)} document(s) in memory</span>
                <span aria-hidden="true">•</span>
                <a href="/docs">API docs</a>
              </div>
            </div>
          </header>

          <div class="panel">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th class="num">Version</th>
                  <th class="num">Chars</th>
                </tr>
              </thead>
              <tbody>
                {rows}
              </tbody>
            </table>
          </div>
        </div>
      </body>
    </html>
    """.strip()

    return HTMLResponse(content=html, status_code=200)


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
