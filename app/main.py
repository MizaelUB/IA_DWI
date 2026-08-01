from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from app.core.guardrails import middleware_guardrails
from app.api.routes import router as api_router
from app.services import session_store
from app.services.recuperacion import cargar_base_vectorial
from app.api.routes import calentar_modelo_ollama
import app.api.routes as routes
from app.core.security import limiter, get_real_ip, is_ip_blocked, block_ip

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Swingtails RAG Sandbox API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)
app.state.limiter = limiter
from slowapi.middleware import SlowAPIMiddleware
app.add_middleware(SlowAPIMiddleware)
from fastapi.exceptions import RequestValidationError

# ── Handler custom de RateLimitExceeded con penalización de 10 min ──
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    ip = get_real_ip(request)
    block_ip(ip, 600)  # Bloquear 10 minutos
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMITED",
            "message": "Demasiadas solicitudes. Por favor, espera 10 minutos antes de intentar de nuevo.",
            "retry_after_seconds": 600
        }
    )

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Error de validación en los datos de entrada."},
    )

import os

default_origins = "https://slider-sizzle-sugar.ngrok-free.dev"
allowed_origins = [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", default_origins).split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Middleware: verificar IP bloqueada antes de procesar ──
@app.middleware("http")
async def check_ip_block(request: Request, call_next):
    ip = get_real_ip(request)
    if is_ip_blocked(ip):
        return JSONResponse(
            status_code=429,
            content={
                "error": "RATE_LIMITED",
                "message": "Demasiadas solicitudes. Por favor, espera 10 minutos antes de intentar de nuevo.",
                "retry_after_seconds": 600
            }
        )
    # Rechazar TRACE/CONNECT (métodos inseguros)
    if request.method in ("TRACE", "CONNECT"):
        return JSONResponse(status_code=405, content={"detail": "Método no permitido."})
    return await call_next(request)

@app.middleware("http")
async def check_content_type(request: Request, call_next):
    if request.method in ["POST", "PUT", "PATCH"] and request.url.path.startswith("/api/"):
        ct = request.headers.get("content-type", "")
        if "application/json" not in ct and "multipart/form-data" not in ct:
            return JSONResponse(status_code=400, content={"detail": "Content-Type inválido. Se requiere application/json."})
    return await call_next(request)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    return response

app.middleware("http")(middleware_guardrails)

app.include_router(api_router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_event():
    try:
        session_store.inicializar_db()
        print("Base de datos SQLite de sesiones inicializada.")
    except Exception as e:
        print(f"Error al inicializar la base de datos de sesiones: {e}")
        
    try:
        routes.coleccion = cargar_base_vectorial()
        print("Base vectorial cargada exitosamente en el servidor FastAPI.")
    except Exception as e:
        print(f"Error crítico al cargar base vectorial de pruebas: {e}")
        
    calentar_modelo_ollama()
