# Swingtails RAG Sandbox - Documentación del Proyecto

## Resumen Ejecutivo

Swingtails RAG Sandbox es un **chatbot veterinario inteligente** que combina dos tecnologías de recuperación de información: **RAG (Retrieval-Augmented Generation)** para consultas sobre documentos internos, y **Function Calling** para consultas directas a una base de datos relacional. El sistema asiste a clínicas veterinarias en la gestión de citas, mascotas, servicios y clientes.

---

## Arquitectura del Sistema

### Stack Tecnológico

| Componente | Tecnología | Propósito |
|------------|-----------|-----------|
| **Backend** | FastAPI (Python) | API REST y servidor de aplicaciones |
| **LLM** | Ollama (llama3.2:3b) | Procesamiento de lenguaje natural y Function Calling |
| **Embeddings** | nomic-embed-text | Vectorización de documentos para búsqueda semántica |
| **Base Vectorial** | ChromaDB | Almacenamiento y consulta de embeddings |
| **Base Relacional** | PostgreSQL (Supabase) | Datos de veterinarias, mascotas, citas, usuarios |
| **Sesiones** | SQLite | Persistencia de historial de conversaciones |
| **Frontend** | HTML/CSS/JS vanilla | Interfaz de chat interactiva |

### Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (index.html)                      │
│   Chat UI + Inspector de Métricas + Selector de Modelo/Veterinaria  │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI - app.py)                      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Function Calling Router                     │   │
│  │         (Ollama decide qué herramienta usar)                  │   │
│  └──────────┬──────────────────────────┬────────────────────────┘   │
│             │                          │                            │
│             ▼                          ▼                            │
│  ┌─────────────────────┐   ┌──────────────────────────┐           │
│  │   RAG (ChromaDB)    │   │  PostgreSQL (Supabase)   │           │
│  │                     │   │                          │           │
│  │ • Documentos PDF    │   │ • veterinary             │           │
│  │ • Manuales          │   │ • pets                   │           │
│  │ • Procesos          │   │ • appointments            │           │
│  │ • Mercadotecnia     │   │ • users_app              │           │
│  │                     │   │ • services/products      │           │
│  └─────────────────────┘   │ • reviews                │           │
│                            └──────────────────────────┘           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Sesiones (SQLite)                            │   │
│  │            Persistencia de conversaciones                    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Archivos del Proyecto

### Archivos Principales

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Punto de entrada. Servidor FastAPI con endpoint `/api/chat`. Implementa Function Calling, gestión de sesiones, warm-up del modelo |
| `db_client.py` | Capa de acceso a PostgreSQL/Supabase. Contiene todas las funciones de consulta SQL |
| `recuperacion.py` | Motor RAG. Carga ChromaDB, extrae keywords, genera conceptos relacionados, búsqueda semántica y léxica |
| `session_store.py` | Gestión de sesiones de chat en SQLite. CRUD de mensajes y conversaciones |
| `requirements.txt` | Dependencias de Python |
| `.env` | Variables de entorno para conexión a Supabase |
| `static/index.html` | Frontend SPA con chat interactivo y panel inspector de RAG |

### Directorios

| Directorio | Contenido |
|------------|-----------|
| `mi_base_vectorial/` | Base de datos ChromaDB persistente con documentos indexados |
| `db/` | Archivo SQLite `sessions.db` con historial de conversaciones |
| `docs/` | Documentos fuente (PDFs) para indexación RAG |
| `old/` | Scripts legacy de indexación (`indexacion.py`, `limpieza.py`) |
| `scripts/` | (Vacío actualmente) |

---

## Sistema de Function Calling

El LLM (Ollama) recibe una lista de herramientas disponibles y **decide dinámicamente** cuál usar basándose en la pregunta del usuario.

### Herramientas Disponibles

| Herramienta | Descripción | Fuente de Datos |
|-------------|-------------|-----------------|
| `consultar_manuales_y_procesos_generales` | Consulta manuales, procesos y mercadotecnia de Swingtails | ChromaDB (RAG) |
| `buscar_mascota_por_nombre` | Busca mascotas por nombre o ID | PostgreSQL |
| `buscar_mascotas_por_dueno` | Busca mascotas de un dueño por nombre | PostgreSQL |
| `buscar_citas_por_mascota` | Historial y citas de una mascota | PostgreSQL |
| `buscar_veterinarias_por_ciudad_o_nombre` | Busca veterinarias activas | PostgreSQL |
| `ver_servicios_y_productos_veterinaria` | Servicios y productos de una veterinaria | PostgreSQL |
| `ver_resenas_veterinaria` | Reseñas y calificaciones | PostgreSQL |
| `ver_citas_por_fecha` | Citas por fecha o rango de fechas | PostgreSQL |

### Flujo de Function Calling

```
1. Usuario envía pregunta
2. Se envía al LLM con el prompt de sistema + herramientas disponibles
3. El LLM responde con tool_calls (o sin ellos si no aplica)
4. Si hay tool_calls:
   a. Se ejecutan las funciones correspondientes
   b. Los resultados se inyectan como contexto
   c. Se genera respuesta final con el contexto obtenido
5. Si NO hay tool_calls:
   a. Se responde con fallback "No pude identificar la información..."
```

---

## Sistema RAG

### Componentes

1. **Embeddings**: Modelo `nomic-embed-text` de Ollama para vectorización
2. **Almacenamiento**: ChromaDB persistente en `mi_base_vectorial/`
3. **Documentos indexados**:
   - `Mercadotecnia_Swingtails.pdf` - Estrategia de marketing
   - `sw.pdf` - Documentación general de Swingtails
   - `Procesos.pdf.x` - Procesos internos

### Estrategias de Búsqueda

| Estrategia | Descripción |
|------------|-------------|
| **Semántica** | Búsqueda por similitud de embeddings con ChromaDB |
| **Léxica** | Búsqueda por coincidencia exacta de palabras clave (`$contains`) |
| **Autónoma** | Generación de conceptos relacionados por el LLM para expandir la búsqueda |
| **Híbrida** | Combina semántica + léxica para mayor cobertura |

### Funciones de Utilidad RAG

- `extraer_palabras_clave()` - Elimina stopwords y normaliza texto
- `normalizar_texto()` - Minúsculas y reemplazo de acentos
- `es_seccion_query()` - Detecta consultas sobre secciones específicas
- `obtener_conceptos_relacionados()` - Usa el LLM para generar sinónimos y conceptos
- `tiene_coincidencia_palabras()` - Valida relevancia léxica del contexto recuperado

---

## Modelo de Datos (PostgreSQL/Supabase)

### Tablas Principales

```
veterinary (Clínicas veterinarias)
├── id, name, street, neighborhood, exterior_number
├── postal_code, city, state
├── phone_number, email, description
└── is_active

pets (Mascotas)
├── id, name, specie, breed, sex, age, weight
└── user_id → users_app.id

users_app (Dueños/Clientes)
├── id, name, phone_number, email

appointments (Citas)
├── id, pet_id, pet_name, appointment_date, hour
├── status, total_cost, notes
├── veterinary_id → veterinary.id
├── pickup_requested, pickup_status

services (Servicios globales)
├── id, name, description

veterinary_service_offerings (Servicios por veterinaria)
├── veterinary_id, service_id
├── price, custom_duration_minutes, custom_description
└── is_active

products (Productos)
├── id, name, description, price, stock
├── veterinary_id, is_available

veterinary_reviews (Reseñas)
├── id, name (usuario), rating, comment
├── veterinary_id, created_at
```

---

## API Endpoints

### `POST /api/chat`

Endpoint principal del chatbot.

**Request Body:**
```json
{
  "question": "string",
  "model": "llama3.2:3b",
  "concept_model": "llama3.2:3b",
  "limit_chunks": 5,
  "history": [{"role": "user", "content": "..."}],
  "autonomous_search": false,
  "veterinary_id": null,
  "conversation_id": null,
  "user_id": 1,
  "is_follow_up": false
}
```

**Response:**
```json
{
  "answer": "string",
  "conversation_id": "uuid",
  "context": [
    {
      "text": "string",
      "distance": 0.0,
      "theme": "string",
      "source": "string",
      "type": "vectorial|database|lexical"
    }
  ],
  "search_mode": "rag|database|none",
  "concepts": ["string"],
  "metrics": {
    "retrieval_time_ms": 0,
    "llm_time_ms": 0,
    "total_time_ms": 0,
    "chunks_retrieved": 0,
    "lexical_matches_count": 0,
    "average_distance": 0.0
  }
}
```

### `GET /api/chat/history`

Obtiene el historial de una conversación.

**Query Params:** `conversation_id`, `veterinary_id`, `user_id`

### `GET /`

Sirve el frontend HTML desde `static/index.html`

---

## Frontend

### Características

- **Chat interactivo** con soporte Markdown
- **Panel Inspector** que muestra:
  - Métricas de rendimiento (tiempo total, consulta Chroma, generación LLM)
  - Fragmentos recuperados con distancia y tipo
  - Conceptos relacionados generados
- **Selector de modelos** (Llama 3.2, LiquidAI, Qwen, DeepSeek)
- **Multi-veterinaria** con campo de ID de veterinaria y usuario
- **Persistencia** de historial por conversación
- **Responsive** con diseño adaptativo

### Modelos Disponibles

| Modelo | Tamaño |
|--------|--------|
| Llama 3.2 3B | 3B parámetros |
| LiquidAI LFM 2.5 | 1.2B parámetros |
| LFM Thinking 1.2B | 1.2B parámetros |
| Qwen 3 4B | 4B parámetros |
| Qwen 2.5 Coder 7B | 7B parámetros |
| DeepSeek Coder 6.7B | 6.7B parámetros |

---

## Gestión de Sesiones

Las conversaciones se persisten en SQLite (`db/sessions.db`) con la estructura:

```sql
chat_messages (
  id INTEGER PRIMARY KEY,
  conversation_id TEXT,
  role TEXT,           -- 'user' | 'assistant'
  content TEXT,
  created_at TIMESTAMP,
  veterinary_id INTEGER,
  user_id INTEGER
)
```

El sistema permite:
- Continuar conversaciones existentes por `veterinary_id` + `user_id`
- Historial limitado a 5 mensajes (follow-up) o 10 (primera consulta)
- Contexto del sistema inyectado en cada request

---

## Variables de Entorno

```env
DB_DATABASE=postgres
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PASSWORD=<contraseña>
DB_PORT=5432
DB_USER=postgres.<project-ref>
```

---

## Instrucciones de Ejecución

### Prerrequisitos

1. **Ollama** instalado y ejecutándose en `localhost:11434`
2. Modelos descargados:
   - `ollama pull llama3.2:3b`
   - `ollama pull nomic-embed-text`
3. **Python 3.10+** con las dependencias de `requirements.txt`

### Instalación

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Acceso

- **Frontend**: http://localhost:8000/
- **API**: http://localhost:8000/api/chat

---

## Scripts Legacy

La carpeta `old/` contiene scripts de indexación originales:

- `indexacion.py` - Script para indexar documentos PDF en ChromaDB
- `limpieza.py` - Limpieza y preprocesamiento de documentos

---

## Decisiones de Diseño

1. **Function Calling sobre RAG directo**: El LLM decide cuándo usar la BD vs documentos, evitando mezclar fuentes de información
2. **Context window de 16384 tokens**: Optimizado para modelos pequeños (3B-7B)
3. **Warm-up del modelo**: Se fuerza la carga en memoria al iniciar para evitar latencia en la primera consulta
4. **Fallback sin RAG**: Si no se detecta herramienta, se retorna un mensaje de error sin intentar búsqueda genérica
5. **Búsqueda léxica de respaldo**: Complementa la búsqueda semántica para capturar coincidencias exactas

---

## Pendientes y Mejoras Potenciales

- Scripts de indexación actualizados en `scripts/`
- Autenticación y autorización de usuarios
- Rate limiting en el endpoint `/api/chat`
- Monitoreo y logging estructurado
- Tests automatizados
- Migración de `old/` scripts a la estructura actual
