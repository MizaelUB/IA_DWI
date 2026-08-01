Como asistente, tienes acceso a la base de datos de la clínica y puedes realizar las siguientes acciones a través de tus herramientas:
REGLAS DE SELECCIÓN DE HERRAMIENTAS:
1. Si la pregunta es sobre la estrategia de mercadotecnia, logo, marca, manuales o procesos generales, llama a 'consultar_manuales_y_procesos_generales'.
2. Si el usuario busca un ANIMAL y te da su nombre, llama a 'buscar_mascota_por_nombre'.
3. Si el usuario busca a una PERSONA/CLIENTE para ver sus mascotas, llama a 'buscar_mascotas_por_dueno'.
4. Si en la pregunta se indica explícitamente un ID numérico de mascota, pásalo en 'pet_id'.
5. Si la pregunta requiere buscar citas por fecha, formatea los argumentos 'fecha_inicio' y 'fecha_fin' ESTRICTAMENTE en YYYY-MM-DD.
6. IMPORTANTE: Puedes calcular fechas relativas (como 'hoy', 'mañana', 'próximo lunes') basándote en la fecha de hoy {fecha_actual} para rellenar los argumentos de fecha.
7. REGLA CRÍTICA DE BÚSQUEDA DE CITAS: Al buscar citas, asume SIEMPRE por defecto que la búsqueda es para la fecha de hoy ({fecha_actual}) a menos que el usuario especifique explícitamente otro día, semana o mes.
8. REGLA CRÍTICA DE FORMATO: Al llenar los argumentos de las herramientas, SIEMPRE usa los valores reales de texto o número. NUNCA devuelvas diccionarios internos con las palabras 'description' o 'type'."""
def construir_prompt_final(nombre_vet: str, db_context_str: str) -> str:
    return f"""Eres el asistente virtual de la clínica veterinaria '{nombre_vet or "Swingtails"}' dirigido EXCLUSIVAMENTE a médicos veterinarios y administradores de la clínica. NUNCA asumas que hablas con un dueño o cliente. Swingtails es una plataforma de gestión de citas veterinarias. Tu única fuente de verdad para esta respuesta es la INFORMACIÓN OBTENIDA abajo.
1. Responde a la pregunta del usuario de manera clara, estructurada, amable y profesional usando ÚNICAMENTE la INFORMACIÓN OBTENIDA.
9. REGLA CRÍTICA DE ÁMBITO: Tienes estrictamente prohibido responder a preguntas o solicitudes que estén fuera de la temática de asistencia veterinaria, gestión de la clínica o la plataforma Swingtails. Esto incluye solicitudes de escribir código, temas de historia general, geografía, ciencia general o charlas casuales externas. Si te piden algo ajeno a tu función, declina responder de manera educada y profesional.
async def api_chat(req: ChatRequest):
            prompt_sistema_final = construir_prompt_final(nombre_vet_activo, db_context_str)
                "context": context_chunks,
                "used_tools": [tc.get("function", {}).get("name") for tc in tool_calls_detected] if tool_calls_detected else [],
async def api_chat_stream(req: ChatRequest):
    
    ruta = await orquestador_ruteador(pregunta_original, modelo_llm)
    print(f"✔ [Stream] Orquestador decidió ruta: {ruta}")
    
    # Forzar modelo Pro para precisión en RAG y transacciones
    if ruta in ("rag", "transaccional"):
        modelo_llm = "deepseek-v4-pro"
    
    if ruta == "conversacional":
        prompt_sistema_final = f"Eres el asistente virtual de la clínica veterinaria '{nombre_vet_activo or 'Swingtails'}'. El usuario con el que hablas es EXCLUSIVAMENTE personal de la veterinaria (médicos, administradores). NUNCA asumas que hablas con un paciente o cliente. Responde de manera amable, estructurada, profesional y corta. Puedes explicar lo que eres capaz de hacer (ver detalles de citas, cancelaciones, buscar mascotas, dueños, historiales de pacientes, etc. Aclara que no tienes permitido crear/agendar citas). REGLA CRÍTICA: Tienes prohibido responder a preguntas externas al ámbito de la clínica veterinaria o Swingtails, tales como escribir código, historia, geografía, ciencia general u otros temas académicos y no-clínicos. Si te preguntan sobre eso, declina responder de manera educada."
        tool_calls_detected = []
        context_chunks = []
        contiene_rag = False
        history, messages_with_history, limit = construir_historial(
            req, conversation_id, user_id, prompt_sistema_final
        )
        inicio_herramientas = time.time()
    else:
        if ruta == "rag":
            tools_list = [t for t in DB_TOOLS if t["function"]["name"] == "consultar_manuales_y_procesos_generales"]
            prompt_especialista = "Eres el Especialista en Base de Conocimientos (RAG) de Swingtails. Tu única función es consultar manuales y procesos y responder según los resultados."
            tools_list = [t for t in DB_TOOLS if t["function"]["name"] != "consultar_manuales_y_procesos_generales"]
            prompt_especialista = construir_prompt_herramientas(nombre_vet_activo, fecha_actual)
            
        history, messages_with_history, limit = construir_historial(
            req, conversation_id, user_id, prompt_especialista
        )
        inicio_herramientas = time.time()
        tool_calls_detected, llm_text_fallback = await detectar_tools_en_ollama(messages_with_history, modelo_llm, pregunta_original, coleccion, tools_list)
        # Forzar ejecución directa si es RAG y LLM falló al detectar tool
        if ruta == "rag" and not tool_calls_detected:
            tool_calls_detected = [{"function": {"name": "consultar_manuales_y_procesos_generales", "arguments": {"pregunta": pregunta_original}}}]
        context_chunks = []
        contiene_rag = False
        prompt_sistema_final = None
        if tool_calls_detected:
            print(f"✔ Herramientas detectadas por Ollama: {tool_calls_detected}")
            context_chunks, contiene_rag = await asyncio.to_thread(
                detectar_y_ejecutar_tools, tool_calls_detected, pregunta_original, req, año_actual, coleccion
            )
            
            if context_chunks:
                db_context_str = "\n\n".join([c["text"] for c in context_chunks])
                prompt_sistema_final = construir_prompt_final(nombre_vet_activo, db_context_str)
    async def event_stream():
        """Generador de eventos SSE."""
        # 1. Enviar eventos de herramientas detectadas
        for tc in tool_calls_detected:
            func_name = tc["function"]["name"]
            label = TOOL_LABELS.get(func_name, f"Ejecutando {func_name}...")
            yield f"event: tool_start\ndata: {json.dumps({'tool': func_name, 'label': label})}\n\n"
        
            yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'context': [], 'search_mode': 'none', 'concepts': [], 'metrics': {'retrieval_time_ms': int((fin_herramientas - inicio_herramientas) * 1000), 'llm_time_ms': 0, 'total_time_ms': int((fin_herramientas - inicio_total) * 1000), 'chunks_retrieved': 0, 'lexical_matches_count': 0, 'average_distance': 0.0}})}\n\n"
        model_name = "deepseek-v4-flash" if ruta in ("conversacional", "transaccional") else (modelo_llm if modelo_llm in ("deepseek-v4-flash", "deepseek-v4-pro") else "deepseek-v4-pro")
            "model": model_name,
        if model_name == "deepseek-v4-pro":
        
        # 6. Enviar evento done con métricas y contexto
            "context": context_chunks,
            "X-Conversation-Id": conversation_id,
# Endpoint de transcripción de voz
@router.post("/api/voice/transcribe")
async def api_voice_transcribe(audio: UploadFile = File(...)):
    """Recibe un archivo de audio y retorna la transcripción usando Whisper local."""
    return await transcribir_audio(audio)


@router.get("/api/voice/status")
def api_voice_status():
    """Diagnóstico: indica si Whisper está disponible o si se usa Web Speech API como fallback."""
    return voice_status()

def get_chat_history(conversation_id: str | None = None, veterinary_id: int | None = None, user_id: int | None = None):
    user_id = user_id or 1
    if not conversation_id and veterinary_id is not None:
        conversation_id = session_store.obtener_conversacion_activa(veterinary_id, user_id)
    if not conversation_id:
        
    history = session_store.obtener_historial(conversation_id, user_id)
    return {"conversation_id": conversation_id, "history": history}
def delete_chat_history(conversation_id: str | None = None, veterinary_id: int | None = None, user_id: int | None = None):
    user_id = user_id or 1
        return {"status": "success", "message": "History deleted for conversation"}
    elif veterinary_id is not None:
        return {"status": "success", "message": "History deleted for active session"}
    else:
        raise HTTPException(status_code=400, detail="Must provide conversation_id or veterinary_id")


# ============================================================
# ENDPOINTS DEL DASHBOARD WEB (Raw Data)
# ============================================================

from typing import Optional
from app.services.db_client import get_connection

@router.get("/api/dashboard/veterinarias")
def get_dashboard_veterinarias():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, city FROM veterinary ORDER BY id ASC;")
                rows = cur.fetchall()
                vets = [{"id": r[0], "name": r[1], "city": r[2]} for r in rows]
                return {"status": "success", "data": vets}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/dashboard/citas")
def get_dashboard_citas(veterinary_id: Optional[int] = None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT a.id, a.pet_name, a.appointment_date, a.hour, a.status, 
                           u.name as dueno, v.name as vet, a.notes
                    FROM appointments a
                    LEFT JOIN pets p ON a.pet_id = p.id
                    LEFT JOIN users_app u ON p.user_id = u.id
                    LEFT JOIN veterinary v ON a.veterinary_id = v.id
                    WHERE (%s::integer IS NULL OR a.veterinary_id = %s)
                    ORDER BY a.appointment_date DESC, a.hour DESC
                    LIMIT 100;
                """
                cur.execute(query, (veterinary_id, veterinary_id))
                rows = cur.fetchall()
                citas = [{"id": r[0], "mascota": r[1], "fecha": str(r[2]), "hora": str(r[3]), "estado": r[4], "dueno": r[5] or "N/A", "veterinaria": r[6], "notas": r[7] or ""} for r in rows]
                return {"status": "success", "data": citas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/dashboard/mascotas")
def get_dashboard_mascotas(veterinary_id: Optional[int] = None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT DISTINCT p.id, p.name, p.specie, p.breed, u.name as dueno
                    FROM pets p
                    JOIN users_app u ON p.user_id = u.id
                    JOIN appointments a ON p.id = a.pet_id
                    WHERE (%s::integer IS NULL OR a.veterinary_id = %s)
                    ORDER BY p.id DESC
                    LIMIT 100;
                """
                cur.execute(query, (veterinary_id, veterinary_id))
                rows = cur.fetchall()
                mascotas = []
                for r in rows:
                    pet_id = r[0]
                    appt_query = """
                        SELECT id, appointment_date, hour, status, notes
                        FROM appointments
                        WHERE pet_id = %s AND (%s::integer IS NULL OR veterinary_id = %s)
                        ORDER BY appointment_date DESC, hour DESC;
                    """
                    cur.execute(appt_query, (pet_id, veterinary_id, veterinary_id))
                    appt_rows = cur.fetchall()
                    citas_pet = [{
                        "id": ar[0],
                        "fecha": str(ar[1]),
                        "hora": str(ar[2]),
                        "estado": ar[3],
                        "notas": ar[4] or ""
                    } for ar in appt_rows]
                    
                    mascotas.append({
                        "id": pet_id,
                        "nombre": r[1],
                        "especie": r[2],
                        "raza": r[3] or "N/A",
                        "dueno": r[4],
                        "citas": citas_pet
                    })
                return {"status": "success", "data": mascotas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/dashboard/clientes")
def get_dashboard_clientes(veterinary_id: Optional[int] = None):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT DISTINCT u.id, u.name, u.phone_number, u.email
                    FROM users_app u
                    JOIN pets p ON u.id = p.user_id
                    JOIN appointments a ON p.id = a.pet_id
                    WHERE (%s::integer IS NULL OR a.veterinary_id = %s)
                    ORDER BY u.id DESC
                    LIMIT 100;
                """
                cur.execute(query, (veterinary_id, veterinary_id))
                rows = cur.fetchall()
                clientes = [{"id": r[0], "nombre": r[1], "telefono": r[2] or "N/A", "email": r[3] or "N/A"} for r in rows]
                return {"status": "success", "data": clientes}
    except Exception as e:
        return {"status": "error", "message": str(e)}
# ENDPOINTS DE AUTENTICACION LOCAL

class LoginRequest(BaseModel):
    username: str
    password: str
@router.post("/api/auth/login")
def api_auth_login(req: LoginRequest):
    import sqlite3
    from app.services.session_store import DB_PATH
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, veterinary_id, veterinary_name FROM dashboard_users WHERE username = ? AND password = ?;",
                (req.username, req.password)
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
            return {
                "status": "success",
                "username": row["username"],
                "veterinary_id": row["veterinary_id"],
                "veterinary_name": row["veterinary_name"]
            }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
def api_auth_guest():
    # Asignamos la veterinaria "Prueba IA" (ID 113) por defecto a los invitados
    # Generamos un ID de usuario único temporal para evitar que se mezclen
    guest_user_id = random.randint(10000000, 99999999)
    guest_username = f"Invitado_{guest_user_id}"
        "username": guest_username,
        "veterinary_id": 113,
        "veterinary_name": "Prueba IA",
        "user_id": guest_user_id

@router.get("/", response_class=HTMLResponse)
def get_home():
    from app.core.config import STATIC_DIR
    static_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    else:
        return "<h1>Error: frontend index.html no encontrado.</h1>"
