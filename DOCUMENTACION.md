# Documentación Técnica y Guía de API: Swingtails Function Calling Sandbox

Esta guía describe la arquitectura del sistema, la configuración de los modelos de inteligencia artificial y proporciona especificaciones completas para consumir la API de la plataforma.

---

## 1. Descripción General del Sistema
El sistema es una **API de Sandbox para *Function Calling*** construida sobre **FastAPI**. Su propósito es permitir que un LLM (ejecutado localmente mediante Ollama) interactúe de forma autónoma con una base de datos PostgreSQL alojada en Supabase y con una base de datos vectorial local (ChromaDB) mediante "tools" (herramientas).

Adicionalmente, el sistema cuenta con soporte de transcripción de voz local vía **Whisper**, permitiendo al usuario procesar audios y convertirlos a texto directamente antes de interactuar con el chatbot.

---

## 2. Modelos Utilizados

### Motor de Inferencia Principal (LLM)
- **Motor:** Ollama (ejecución local).
- **Modelo por defecto:** `llama3.2:3b` (configurable en los payloads de chat).
- **Ventana de Contexto (`num_ctx`):** `16384` tokens.
- **Mantener cargado en memoria (`keep_alive`):** `-1` (mejora significativamente los tiempos de respuesta al evitar recargar el modelo en RAM/VRAM en cada petición).

### Modelo de Embeddings (RAG)
- **Motor:** Ollama.
- **Modelo:** `nomic-embed-text` (usado para indexar y buscar manuales en la base de conocimientos vectorial ChromaDB).

### Modelo de Transcripción de Voz (Whisper)
- **Motor:** `faster-whisper` (ejecutado de forma local vía CTranslate2).
- **Modelo por defecto:** `medium` (configurable mediante la variable de entorno `WHISPER_MODEL`).

---

## 3. Catálogo de Herramientas (Tool Definitions)

Cuando el LLM analiza la pregunta del usuario, determina si debe invocar una o varias de las siguientes herramientas:

| Nombre de la Herramienta | Destino / Origen de Datos | Parámetros Clave | Descripción |
| :--- | :--- | :--- | :--- |
| `buscar_mascota_por_nombre` | PostgreSQL (Supabase) | `nombre_mascota` (str), `pet_id` (int) | Detalla la ficha clínica de una mascota. |
| `buscar_mascotas_por_dueno` | PostgreSQL (Supabase) | `nombre_dueno` (str) | Lista todas las mascotas pertenecientes a un cliente. |
| `buscar_citas_por_mascota` | PostgreSQL (Supabase) | `nombre_mascota` (str), `pet_id` (int) | Muestra el historial y citas futuras de la mascota. |
| `buscar_veterinarias_por_ciudad_o_nombre`| PostgreSQL (Supabase) | `nombre` (str), `ciudad` (str) | Filtra y encuentra clínicas veterinarias registradas. |
| `ver_servicios_y_productos_veterinaria` | PostgreSQL (Supabase) | `veterinary_id` (int) | Retorna la lista de precios, vacunas, consultas y productos. |
| `ver_resenas_veterinaria` | PostgreSQL (Supabase) | `veterinary_id` (int) | Lee calificaciones y opiniones de clientes sobre la clínica. |
| `ver_citas_por_fecha` | PostgreSQL (Supabase) | `fecha_inicio`, `fecha_fin` | Consulta la agenda del día o rangos de fecha seleccionados. |
| `actualizar_estado_cita` | PostgreSQL (Supabase) | `appointment_id` (int), `nuevo_estado` (str) | Modifica el estatus de una cita (Confirmar/Cancelar/Reagendar). |
| `confirmar_o_rechazar_cita` | PostgreSQL (Supabase) | `appointment_id` (int), `accion` (str) | Wrapper simplificado para la gestión de citas por parte del personal. |
| `buscar_dueno_mascota` | PostgreSQL (Supabase) | `nombre_mascota` (str) | Identifica al dueño o persona de contacto a partir de la mascota. |
| `consultar_manuales_y_procesos_generales`| ChromaDB (RAG local) | `pregunta` (str) | Consulta manuales de marca, procesos generales y políticas internas. |

---

## 4. Endpoints de la API (Consumo)

### `GET /`
- **Descripción:** Sirve la SPA (Single Page Application) estática del panel de control de Swingtails.
- **Respuesta:** `text/html` (archivo `static/index.html`).

---

### `POST /api/chat`
Procesa las preguntas del usuario evaluando herramientas de forma síncrona y devolviendo la respuesta final del LLM de una sola vez.

- **Cuerpo de la Solicitud (JSON):**
```json
{
  "question": "Muestra los datos de la mascota llamada Firulais",
  "model": "llama3.2:3b",
  "veterinary_id": 1,
  "conversation_id": "opcional-uuid-de-sesion",
  "user_id": 1
}
```
- **Respuesta Exitosa (JSON):**
```json
{
  "answer": "El expediente de Firulais (ID: 4) indica que es un perro de raza Golden Retriever de 3 años, cuyo dueño es Juan Pérez.",
  "conversation_id": "b3e0d860-96f7-4148-be2a-9cb2ef37d2f9",
  "context": [
    {
      "text": "Resultado de buscar_mascota_por_nombre con argumentos {\"nombre_mascota\": \"Firulais\"}: ...",
      "distance": 0.0,
      "theme": "Consulta BD (buscar_mascota_por_nombre)",
      "source": "PostgreSQL (Supabase)",
      "type": "database"
    }
  ],
  "search_mode": "database",
  "concepts": [],
  "metrics": {
    "retrieval_time_ms": 120,
    "llm_time_ms": 1450,
    "total_time_ms": 1570,
    "chunks_retrieved": 1,
    "lexical_matches_count": 0,
    "average_distance": 0.0
  }
}
```

---

### `POST /api/chat/stream`
Mismo flujo de procesamiento que `/api/chat`, pero transmite la respuesta token por token en tiempo real usando Server-Sent Events (SSE).

- **Cuerpo de la Solicitud (JSON):** *(Igual a `/api/chat`)*
- **Respuesta:** `text/event-stream`
- **Formato del Flujo de Eventos:**
  - **`event: tool_start`**: Indica el inicio de la ejecución de una herramienta.
    `data: {"tool": "buscar_mascota_por_nombre", "label": "Buscando expedientes de la mascota..."}`
  - **`event: token`**: Envía cada token del texto generado por el LLM.
    `data: {"token": "El "}`
  - **`event: done`**: Envía las métricas finales y estructura de contexto al finalizar.
    `data: {"conversation_id": "...", "context": [...], "search_mode": "database", "metrics": {...}}`
  - **`event: error`**: Ocurre en caso de fallos.
    `data: {"message": "Descripción del error"}`

---

### `POST /api/voice/transcribe`
Recibe archivos de audio en formato multipart/form-data y retorna el texto transcrito de forma local.

- **Parámetros (Multipart Form):**
  - `audio`: Archivo binario (soporta formatos `.wav`, `.mp3`, `.webm`, `.m4a`, `.ogg`).
- **Respuesta (JSON):**
```json
{
  "text": "quiero ver las citas de la veterinaria para el dia de hoy",
  "language": "es",
  "confidence": 0.985
}
```

---

### `GET /api/voice/status`
Permite verificar la disponibilidad y estado de carga de Whisper en el servidor.

- **Respuesta (JSON):**
```json
{
  "whisper_installed": true,
  "whisper_loaded": true,
  "device": "cuda (device 0)"
}
```

---

### `GET /api/chat/history`
Recupera el historial completo de interacciones guardado localmente en SQLite.

- **Parámetros Query:**
  - `conversation_id` (str, opcional)
  - `veterinary_id` (int, opcional)
  - `user_id` (int, opcional)
- **Respuesta (JSON):**
```json
{
  "conversation_id": "uuid-conversacion-consultada",
  "history": [
    {
      "role": "user",
      "content": "Hola"
    },
    {
      "role": "assistant",
      "content": "¡Hola! ¿En qué puedo ayudarte hoy?"
    }
  ]
}
```

---

### `DELETE /api/chat/history`
Borra el historial de conversaciones de la base de datos local.

- **Parámetros Query:**
  - `conversation_id` (str, opcional): Borra una conversación específica.
  - `veterinary_id` (int, opcional): Borra la conversación activa vinculada a la veterinaria.
  - `user_id` (int, opcional): ID del usuario de la sesión.
- **Respuesta (JSON):**
```json
{
  "status": "success",
  "message": "History deleted for conversation"
}
```
