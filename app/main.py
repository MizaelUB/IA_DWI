from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.guardrails import middleware_guardrails
from app.api.routes import router as api_router
from app.services import session_store
from app.services.recuperacion import cargar_base_vectorial
from app.api.routes import calentar_modelo_ollama
import app.api.routes as routes

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Swingtails RAG Sandbox API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
