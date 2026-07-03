import sys
import os
import time
import requests
import json
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import Message, ChatRequest
from fastapi import UploadFile, File
import re
import uuid

from app.services.recuperacion import cargar_base_vectorial, extraer_palabras_clave, es_seccion_query, tiene_coincidencia_palabras, normalizar_texto, obtener_conceptos_relacionados
from app.services import db_client
from app.services import session_store
from app.core.guardrails import middleware_guardrails
from app.services.voice_service import transcribir_audio, voice_status

from fastapi import APIRouter

router = APIRouter()



(middleware_guardrails)

coleccion = None
NUM_CTX = 16384

# Mapeo de herramientas a labels legibles para el frontend
TOOL_LABELS = {
    "buscar_mascota_por_nombre": "Buscando expedientes de la mascota...",
    "buscar_mascotas_por_dueno": "Buscando mascotas del dueño...",
    "buscar_citas_por_mascota": "Consultando citas de la mascota...",
    "buscar_veterinarias_por_ciudad_o_nombre": "Buscando veterinarias...",
    "ver_servicios_y_productos_veterinaria": "Consultando servicios y productos...",
    "ver_resenas_veterinaria": "Consultando reseñas de la veterinaria...",
    "ver_citas_por_fecha": "Consultando citas por fecha...",
    "consultar_manuales_y_procesos_generales": "Consultando manuales y procesos...",
    "actualizar_estado_cita": "Actualizando estado de la cita...",
    "buscar_dueno_mascota": "Buscando dueño de la mascota...",
    "confirmar_o_rechazar_cita": "Confirmando o rechazando la cita...",
    "buscar_citas_por_estado": "Buscando citas por estado...",
    "ver_detalles_cita": "Consultando detalles de la cita...",
    "buscar_info_contacto_dueno": "Buscando información de contacto del dueño...",
}


def calentar_modelo_ollama(modelo: str = "llama3.2:3b"):
    """Fuerza a Ollama a cargar el modelo en memoria al iniciar el servidor."""
    print(f"Calentando modelo {modelo} en memoria...")
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": modelo,
        "messages": [{"role": "user", "content": "Hola"}],
        "stream": False,
        "keep_alive": -1,
        "options": {
            "num_ctx": NUM_CTX
        }
    }
    try:
        requests.post(url, json=payload, timeout=120)
        print("✔ Modelo cargado y listo en memoria.")
    except Exception as e:
        print(f"Advertencia: No se pudo calentar el modelo. {e}")

@router.on_event("startup")
def startup_event():
    global coleccion
    try:
        session_store.inicializar_db()
        print("Base de datos SQLite de sesiones inicializada.")
    except Exception as e:
        print(f"Error al inicializar la base de datos de sesiones: {e}")
        
    try:
        coleccion = cargar_base_vectorial()
        print("Base vectorial cargada exitosamente en el servidor FastAPI.")
    except Exception as e:
        print(f"Error crítico al cargar base vectorial de pruebas: {e}")
        
    # Llamamos al warm-up para evitar demoras en la primera consulta
    calentar_modelo_ollama()




def parsear_fecha(fecha_str: str, año_defecto: int) -> str:
    """
    Intenta extraer y normalizar una fecha al formato YYYY-MM-DD.
    Maneja los formatos incorrectos más comunes devueltos por el LLM.
    """
    if not isinstance(fecha_str, str):
        return str(fecha_str)
        
    # Buscar formato YYYY-MM-DD o YYYY/MM/DD
    match_iso = re.search(r'(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})', fecha_str)
    if match_iso:
        return f"{match_iso.group(1)}-{int(match_iso.group(2)):02d}-{int(match_iso.group(3)):02d}"
    
    # Buscar formato DD-MM-YYYY o DD/MM/YYYY (común en LATAM)
    match_lat = re.search(r'(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{4})', fecha_str)
    if match_lat:
        return f"{match_lat.group(3)}-{int(match_lat.group(2)):02d}-{int(match_lat.group(1)):02d}"
        
    # Buscar formato DD-MM (Sin año explícito) -> Se asigna el año actual
    match_short = re.search(r'(\d{1,2})[-\/.](\d{1,2})', fecha_str)
    if match_short:
        return f"{año_defecto}-{int(match_short.group(2)):02d}-{int(match_short.group(1)):02d}"
        
    return fecha_str


# ============================================================
# Herramientas de Function Calling (definición)
# ============================================================
DB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_info_contacto_dueno",
            "description": "Busca y devuelve la información de contacto (número de teléfono, correo electrónico, etc.) de un dueño o cliente a partir de su nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_dueno": {
                        "type": "string",
                        "description": "El nombre completo o parcial del dueño."
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "El ID único del dueño (opcional)."
                    }
                },
                "required": ["nombre_dueno"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "buscar_citas_por_estado",
            "description": "Obtiene una lista de citas filtradas únicamente por su estado (ej. 'Pendiente', 'Cancelada', 'Confirmada') independientemente de la fecha.",
            "parameters": {
                "type": "object",
                "properties": {
                    "estado": {
                        "type": "string",
                        "description": "El estado de las citas a buscar (Pendiente, Confirmada, Cancelada)."
                    },
                    "incluir_pasadas": {
                        "type": "boolean",
                        "description": "Si es False (por defecto), solo devolverá citas de hoy hacia el futuro. Si es True, incluye el historial pasado."
                    }
                },
                "required": ["estado"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_detalles_cita",
            "description": "Obtiene todos los detalles de una cita específica dado su ID, incluyendo la información de la mascota, el dueño y las últimas citas previas de esa mascota.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "El ID numérico de la cita."
                    }
                },
                "required": ["appointment_id"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "buscar_mascota_por_nombre",
            "description": "Usa ESTA herramienta ÚNICAMENTE cuando el usuario da el nombre de la MASCOTA (el animal). NO la uses si el nombre parece ser de una persona o cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_mascota": {
                        "type": "string",
                        "description": "El nombre del animal/mascota."
                    },
                    "pet_id": {
                        "type": "integer",
                        "description": "El ID único de la mascota (opcional)."
                    }
                },
                "required": ["nombre_mascota"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_manuales_y_procesos_generales",
            "description": "Consulta el manual de marca, mercadotecnia o procesos de Swingtails en la base de conocimientos general (RAG/vectorial) cuando no se trate de una consulta directa a la base de datos de la veterinaria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pregunta": {
                        "type": "string",
                        "description": "La pregunta o tema a buscar en los manuales de Swingtails."
                    }
                },
                "required": ["pregunta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_mascotas_por_dueno",
            "description": "Usa ESTA herramienta ÚNICAMENTE cuando el usuario proporciona el nombre del DUEÑO, HUMANO o CLIENTE para saber qué mascotas tiene registradas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_dueno": {
                        "type": "string",
                        "description": "El nombre completo o parcial de la persona (el dueño)."
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "El ID único del dueño (opcional)."
                    }
                },
                "required": ["nombre_dueno"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_citas_por_mascota",
            "description": "Obtiene el historial y próximas citas de una mascota por su nombre o pet_id. Usa esto siempre que pregunten por las citas de un animal o mascota específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_mascota": {
                        "type": "string",
                        "description": "El nombre de la mascota."
                    },
                    "pet_id": {
                        "type": "integer",
                        "description": "El ID único de la mascota (opcional)."
                    },
                    "incluir_pasadas": {
                        "type": "boolean",
                        "description": "Si es False (por defecto), solo devolverá citas de hoy hacia el futuro. Si es True, incluye el historial pasado."
                    }
                },
                "required": ["nombre_mascota"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_veterinarias_por_ciudad_o_nombre",
            "description": "Busca veterinarias registradas y activas por ciudad y/o por nombre de clínica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ciudad": {
                        "type": "string",
                        "description": "La ciudad en la que buscar veterinarias (opcional)."
                    },
                    "nombre": {
                        "type": "string",
                        "description": "El nombre de la veterinaria (opcional)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_servicios_y_productos_veterinaria",
            "description": "Obtiene la lista completa de servicios y productos ofrecidos por una veterinaria específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_veterinaria": {
                        "type": "string",
                        "description": "El nombre de la veterinaria."
                    }
                },
                "required": ["nombre_veterinaria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_resenas_veterinaria",
            "description": "Obtiene las opiniones y calificaciones de los clientes sobre una veterinaria específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_veterinaria": {
                        "type": "string",
                        "description": "El nombre de la veterinaria."
                    }
                },
                "required": ["nombre_veterinaria"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_citas_por_fecha",
            "description": "Obtiene las citas agendadas para una fecha, rango de fechas, o citas futuras/pendientes a partir de hoy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {
                        "type": "string",
                        "description": "La fecha de inicio en formato YYYY-MM-DD. Opcional (si no se especifica se asume el día de hoy)."
                    },
                    "fecha_fin": {
                        "type": "string",
                        "description": "La fecha de fin en formato YYYY-MM-DD para un rango cerrado (opcional)."
                    },
                    "rango_futuro": {
                        "type": "boolean",
                        "description": "Si es True, busca todas las citas a partir de la fecha_inicio en adelante (útil para 'próximas citas' o 'citas futuras')."
                    },
                    "estado": {
                        "type": "string",
                        "description": "Filtra las citas por su estado actual (ej. 'Pendiente', 'Confirmada', 'Cancelada')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "actualizar_estado_cita",
            "description": "Confirma o cancela una cita específica mediante su ID único. Si el estado es 'Cancelada', se puede incluir un motivo de cancelación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "El ID de la cita a confirmar o cancelar."
                    },
                    "nuevo_estado": {
                        "type": "string",
                        "enum": ["Confirmada", "Cancelada"],
                        "description": "El nuevo estado de la cita."
                    },
                    "motivo_cancelacion": {
                        "type": "string",
                        "description": "El motivo por el cual se cancela la cita (opcional)."
                    }
                },
                "required": ["appointment_id", "nuevo_estado"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "confirmar_o_rechazar_cita",
            "description": "Confirma o rechaza una cita médica específica según su ID único.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "El ID de la cita a confirmar o rechazar."
                    },
                    "accion": {
                        "type": "string",
                        "enum": ["confirmar", "rechazar"],
                        "description": "La acción a realizar sobre la cita."
                    },
                    "motivo": {
                        "type": "string",
                        "description": "El motivo por el cual se rechaza/cancela la cita (opcional, solo si la acción es rechazar)."
                    }
                },
                "required": ["appointment_id", "accion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_dueno_mascota",
            "description": "Busca la información del dueño de una mascota específica usando el pet_id o su nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pet_id": {
                        "type": "integer",
                        "description": "El ID de la mascota cuyo dueño se desea buscar (preferido si se conoce)."
                    },
                    "nombre_mascota": {
                        "type": "string",
                        "description": "El nombre de la mascota para buscar a su dueño."
                    }
                }
            }
        }
    }
]


# ============================================================
# Funciones auxiliares reutilizables
# ============================================================

def resolver_sesion(req: ChatRequest) -> tuple:
    """Resuelve conversation_id y gestiona el historial de sesión."""
    conversation_id = req.conversation_id
    user_id = req.user_id or 1
    
    if not conversation_id and req.veterinary_id is not None:
        conversation_id = session_store.obtener_conversacion_activa(req.veterinary_id, user_id)
        
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        
    vet_id_sesion = session_store.obtener_veterinary_id_de_sesion(conversation_id)
    if vet_id_sesion is not None:
        req.veterinary_id = vet_id_sesion

    return conversation_id, user_id


def obtener_nombre_veterinaria(veterinary_id: int | None) -> str | None:
    """Obtiene el nombre de la veterinaria activa por ID."""
    if veterinary_id is None:
        return None
    try:
        res_vet = db_client.buscar_veterinarias_por_ciudad_o_nombre(veterinary_id=veterinary_id)
        if res_vet.get("status") == "success" and res_vet.get("found") and res_vet.get("data"):
            nombre = res_vet["data"][0]["nombre"]
            print(f"[DEBUG] Veterinaria activa seleccionada por ID {veterinary_id}: {nombre}")
            return nombre
    except Exception as e:
        print(f"Error al buscar nombre de veterinaria activa: {e}")
    return None


def construir_historial(req: ChatRequest, conversation_id: str, user_id: int,
                        prompt_herramientas: str) -> tuple:
    """Construye el historial de mensajes y retorna (history, messages_with_history, limit)."""
    history = session_store.obtener_historial(conversation_id, user_id)
    if not history:
        session_store.guardar_mensaje(conversation_id, "system", prompt_herramientas, req.veterinary_id, user_id)
        session_store.guardar_mensaje(conversation_id, "user", req.question, req.veterinary_id, user_id)
        history = [
            {"role": "system", "content": prompt_herramientas},
            {"role": "user", "content": req.question}
        ]
    else:
        session_store.guardar_mensaje(conversation_id, "user", req.question, req.veterinary_id, user_id)
        history.append({"role": "user", "content": req.question})
        
    limit = 5 if req.is_follow_up else 10
    messages_with_history = history[-limit:] if len(history) > limit else history
    if not messages_with_history or messages_with_history[0]["role"] != "system":
        messages_with_history = [{"role": "system", "content": prompt_herramientas}] + messages_with_history
    else:
        messages_with_history = [{"role": "system", "content": prompt_herramientas}] + messages_with_history[1:]

    return history, messages_with_history, limit


def construir_prompt_herramientas(nombre_vet: str, fecha_actual: str) -> str:
    return f"""Eres el asistente virtual de la clínica veterinaria '{nombre_vet or "Swingtails"}'. Swingtails es una plataforma de gestión de citas veterinarias.
La fecha de hoy es {fecha_actual}.

CAPACIDADES Y HERRAMIENTAS:
Como asistente, tienes acceso a la base de datos de la clínica y puedes realizar las siguientes acciones a través de tus herramientas:
- Buscar y listar pacientes (mascotas) y dueños por nombre o ID.
- Obtener información de contacto de los clientes (teléfono, correo).
- Consultar el historial, notas y citas agendadas de cualquier mascota.
- Buscar citas filtrando por fecha, o ver todas las citas en estados específicos (Pendiente, Confirmada, Cancelada).
- Aprobar (confirmar) o rechazar (cancelar) citas existentes mediante su ID.
- Ver los detalles exhaustivos de una cita en particular, así como servicios, productos y reseñas de la clínica.
- Consultar manuales de marca o procesos operativos de Swingtails mediante la base de conocimientos documental.

REGLAS DE SELECCIÓN DE HERRAMIENTAS:
1. Si la pregunta es sobre la estrategia de mercadotecnia, logo, marca, manuales o procesos generales, llama a 'consultar_manuales_y_procesos_generales'.
2. Si el usuario busca un ANIMAL y te da su nombre, llama a 'buscar_mascota_por_nombre'.
3. Si el usuario busca a una PERSONA/CLIENTE para ver sus mascotas, llama a 'buscar_mascotas_por_dueno'.
4. Si en la pregunta se indica explícitamente un ID numérico de mascota, pásalo en 'pet_id'.
5. Si la pregunta requiere buscar citas por fecha, formatea los argumentos 'fecha_inicio' y 'fecha_fin' ESTRICTAMENTE en YYYY-MM-DD.
6. IMPORTANTE: Puedes calcular fechas relativas (como 'hoy', 'mañana', 'próximo lunes') basándote en la fecha de hoy {fecha_actual} para rellenar los argumentos de fecha.
7. REGLA CRÍTICA DE FORMATO: Al llenar los argumentos de las herramientas, SIEMPRE usa los valores reales de texto o número. NUNCA devuelvas diccionarios internos con las palabras 'description' o 'type'."""


def construir_prompt_final(nombre_vet: str, db_context_str: str) -> str:
    return f"""Eres el asistente virtual de la clínica veterinaria '{nombre_vet or "Swingtails"}' dirigido a médicos veterinarios, administradores y clientes. Swingtails es una plataforma de gestión de citas veterinarias. Tu única fuente de verdad para esta respuesta es la INFORMACIÓN OBTENIDA abajo.
            
INFORMACIÓN OBTENIDA DE LA CLÍNICA:
{db_context_str}

INSTRUCCIONES DE RESPUESTA:
1. Responde a la pregunta del usuario de manera clara, estructurada, amable y profesional usando ÚNICAMENTE la INFORMACIÓN OBTENIDA.
2. Como eres el asistente de la clínica '{nombre_vet or "Swingtails"}', saluda e interactúa en su nombre.
3. Si la información indica que no se encontraron datos o está vacía, menciónalo de manera educada y clara.
4. NUNCA uses frases como "Según la información de la base de datos", "De acuerdo al contexto" o similares.
5. No uses tu conocimiento general.
6. Organiza la información en listas o tablas Markdown para facilitar su lectura.
7. Si el resultado de buscar mascotas contiene múltiples mascotas con el mismo nombre y el usuario no especificó el parámetro 'pet_id', debes listar todas las mascotas encontradas (con sus respectivos IDs, especie, raza y dueño) y preguntarle explícitamente al usuario que te indique el ID de la mascota específica.
"""


def detectar_y_ejecutar_tools(tool_calls_detected, pregunta_original, req, año_actual, coleccion):
    """Detecta herramientas, las ejecuta y retorna (context_chunks, contiene_rag)."""
    tool_mappers = {
        "buscar_mascota_por_nombre": db_client.buscar_mascota_por_nombre,
        "buscar_mascotas_por_dueno": db_client.buscar_mascotas_por_dueno,
        "buscar_citas_por_mascota": db_client.buscar_citas_por_mascota,
        "buscar_veterinarias_por_ciudad_o_nombre": db_client.buscar_veterinarias_por_ciudad_o_nombre,
        "ver_servicios_y_productos_veterinaria": db_client.ver_servicios_y_productos_veterinaria,
        "ver_resenas_veterinaria": db_client.ver_resenas_veterinaria,
        "ver_citas_por_fecha": db_client.ver_citas_por_fecha,
        "actualizar_estado_cita": db_client.actualizar_estado_cita,
        "buscar_dueno_mascota": db_client.buscar_dueno_mascota,
        "confirmar_o_rechazar_cita": db_client.confirmar_o_rechazar_cita,
        "buscar_citas_por_estado": db_client.buscar_citas_por_estado,
        "ver_detalles_cita": db_client.ver_detalles_cita,
        "buscar_info_contacto_dueno": db_client.buscar_info_contacto_dueno,
    }
    
    context_chunks = []
    contiene_rag = False
    
    for tc in tool_calls_detected:
        func_name = tc["function"]["name"]
        func_args = tc["function"]["arguments"]
        
        if func_name == "consultar_manuales_y_procesos_generales":
            contiene_rag = True
            pregunta_rag = func_args.get("pregunta", pregunta_original)
            pregunta_optimizada = extraer_palabras_clave(pregunta_rag)
            query_texts = [pregunta_rag, pregunta_optimizada]
            conceptos_generados = []
            
            if req.autonomous_search:
                modelo_conceptos = req.model if req.concept_model == req.__fields__["concept_model"].default else req.concept_model
                conceptos_generados = obtener_conceptos_relacionados(pregunta_rag, req.history, modelo_conceptos)
                if conceptos_generados:
                    query_texts.extend(conceptos_generados)
                    
            n = 15 if es_seccion_query(pregunta_rag) else 12
            try:
                resultados = coleccion.query(
                    query_texts=query_texts,
                    n_results=n,
                    include=["documents", "distances", "metadatas"]
                )
                docs_unicos = []
                for i in range(len(resultados['documents'])): 
                    for j, doc in enumerate(resultados['documents'][i]):
                        dist = resultados['distances'][i][j]
                        meta = resultados['metadatas'][i][j]
                        tema = meta.get("tema", "Sin Tema")
                        archivo = meta.get("archivo", "Desconocido")
                        
                        if doc not in docs_unicos:
                            docs_unicos.append(doc)
                            context_chunks.append({
                                "text": doc,
                                "distance": float(dist),
                                "theme": tema,
                                "source": archivo,
                                "type": "vectorial"
                            })
            except Exception as err:
                print(f"Error en consulta RAG interna: {err}")
                
        elif func_name in tool_mappers:
            if func_name in ("buscar_mascotas_por_dueno", "buscar_info_contacto_dueno"):
                if not func_args.get("user_id"):
                    match_id = re.search(r'\b(?:id|ID|identificador)\s*[:=]?\s*(\d+)\b', pregunta_original)
                    if match_id:
                        func_args["user_id"] = int(match_id.group(1))

            if func_name in ("buscar_mascota_por_nombre", "buscar_citas_por_mascota", "buscar_dueno_mascota"):
                nombre_mascota = func_args.get("nombre_mascota")
                if isinstance(nombre_mascota, str) and nombre_mascota.strip().startswith("{"):
                    try:
                        import json as json_mod
                        parsed = json_mod.loads(nombre_mascota)
                        if "pet_id" in parsed and parsed["pet_id"]:
                            func_args["pet_id"] = int(parsed["pet_id"])
                        if "nombre_mascota" in parsed:
                            func_args["nombre_mascota"] = parsed["nombre_mascota"]
                        elif "nombre" in parsed:
                            func_args["nombre_mascota"] = parsed["nombre"]
                    except Exception as parse_err:
                        print(f"Error al parsear JSON malformado en nombre_mascota: {parse_err}")
                
                if not func_args.get("pet_id"):
                    match_id = re.search(r'\b(?:id|ID|identificador)\s*[:=]?\s*(\d+)\b', pregunta_original)
                    if match_id:
                        func_args["pet_id"] = int(match_id.group(1))

            if func_name == "ver_citas_por_fecha":
                if "fecha_inicio" in func_args and func_args["fecha_inicio"]:
                    func_args["fecha_inicio"] = parsear_fecha(func_args["fecha_inicio"], año_actual)
                if "fecha_fin" in func_args and func_args["fecha_fin"]:
                    func_args["fecha_fin"] = parsear_fecha(func_args["fecha_fin"], año_actual)

            try:
                result = tool_mappers[func_name](**func_args, veterinary_id=req.veterinary_id)
            except Exception as err:
                result = {"status": "error", "message": str(err)}
            
            result_str = json.dumps(result, indent=2, ensure_ascii=False)
            context_chunks.append({
                "text": f"Resultado de {func_name} con argumentos {json.dumps(func_args)}:\n{result_str}",
                "distance": 0.0,
                "theme": f"Consulta BD ({func_name})",
                "source": "PostgreSQL (Supabase)",
                "type": "database"
            })
    
    return context_chunks, contiene_rag


def detectar_tools_en_ollama(messages_with_history, modelo_llm, pregunta_original, coleccion):
    """Llama a Ollama para detectar tool calls. Retorna lista de tool_calls detectados."""
    url = "http://localhost:11434/api/chat"
    
    payload_tools = {
        "model": modelo_llm,
        "messages": messages_with_history,
        "tools": DB_TOOLS,
        "stream": False,
        "keep_alive": -1,
        "options": {
            "num_ctx": NUM_CTX
        }
    }

    tool_calls_detected = []
    try:
        res_tools = requests.post(url, json=payload_tools, timeout=45)
        if res_tools.status_code == 200:
            res_tools_json = res_tools.json()
            message_resp = res_tools_json.get("message", {})
            if "tool_calls" in message_resp:
                tool_calls_detected = message_resp["tool_calls"]
    except Exception as e:
        print(f"Error al detectar herramientas en Ollama: {e}")

    if "swingtails" in normalizar_texto(pregunta_original):
        tiene_rag_tool = any(tc.get("function", {}).get("name") == "consultar_manuales_y_procesos_generales" for tc in tool_calls_detected)
        if not tiene_rag_tool:
            tool_calls_detected.append({
                "function": {
                    "name": "consultar_manuales_y_procesos_generales",
                    "arguments": {"pregunta": pregunta_original}
                }
            })

    return tool_calls_detected


def generar_respuesta_ollama(messages_final, modelo_llm):
    """Genera una respuesta completa (sin streaming) desde Ollama."""
    url = "http://localhost:11434/api/chat"
    payload_final = {
        "model": modelo_llm,
        "messages": messages_final,
        "stream": False,
        "keep_alive": -1,
        "options": {
            "num_ctx": NUM_CTX
        }
    }
    
    try:
        res_final = requests.post(url, json=payload_final, timeout=90)
        if res_final.status_code == 200:
            return res_final.json()['message']['content']
        else:
            return f"Error al generar respuesta final (HTTP {res_final.status_code})"
    except Exception as e:
        return f"Falla de conexión al generar respuesta final con Ollama: {e}"


# ============================================================
# Endpoint original /api/chat (sin streaming)
# ============================================================
@router.post("/api/chat")
def api_chat(req: ChatRequest):
    global coleccion
    if coleccion is None:
        raise HTTPException(status_code=500, detail="La base vectorial de pruebas no está cargada.")
        
    inicio_total = time.time()
    pregunta_original = req.question
    modelo_llm = req.model
    conversation_id, user_id = resolver_sesion(req)
    nombre_vet_activo = obtener_nombre_veterinaria(req.veterinary_id)

    fecha_actual = str(datetime.date.today())
    año_actual = datetime.date.today().year
    prompt_herramientas = construir_prompt_herramientas(nombre_vet_activo, fecha_actual)
    
    history, messages_with_history, limit = construir_historial(
        req, conversation_id, user_id, prompt_herramientas
    )

    inicio_herramientas = time.time()
    tool_calls_detected = detectar_tools_en_ollama(messages_with_history, modelo_llm, pregunta_original, coleccion)

    if tool_calls_detected:
        print(f"✔ Herramientas detectadas por Ollama: {tool_calls_detected}")
        context_chunks, contiene_rag = detectar_y_ejecutar_tools(
            tool_calls_detected, pregunta_original, req, año_actual, coleccion
        )
        
        if context_chunks:
            db_context_str = "\n\n".join([c["text"] for c in context_chunks])
            prompt_sistema_final = construir_prompt_final(nombre_vet_activo, db_context_str)
            
            inicio_llm = time.time()
            messages_final = history[-limit:] if len(history) > limit else history
            if not messages_final or messages_final[0]["role"] != "system":
                messages_final = [{"role": "system", "content": prompt_sistema_final}] + messages_final
            else:
                messages_final = [{"role": "system", "content": prompt_sistema_final}] + messages_final[1:]

            answer = generar_respuesta_ollama(messages_final, modelo_llm)
                
            session_store.guardar_mensaje(conversation_id, "assistant", answer, req.veterinary_id, user_id)
                
            fin_total = time.time()
            return {
                "answer": answer,
                "conversation_id": conversation_id,
                "context": context_chunks,
                "search_mode": "rag" if contiene_rag else "database",
                "concepts": [],
                "metrics": {
                    "retrieval_time_ms": int((time.time() - inicio_herramientas) * 1000),
                    "llm_time_ms": int((time.time() - inicio_llm) * 1000),
                    "total_time_ms": int((fin_total - inicio_total) * 1000),
                    "chunks_retrieved": len(context_chunks),
                    "lexical_matches_count": 0,
                    "average_distance": 0.0
                }
            }

    # CIERRE DE SEGURIDAD (SIN FALLBACK RAG)
    fin_total = time.time()
    answer_fallback = "No pude identificar la información solicitada ni una herramienta adecuada para buscarla. ¿Podrías ser más específico o reformular tu pregunta?"
    session_store.guardar_mensaje(conversation_id, "assistant", answer_fallback, req.veterinary_id, user_id)
    return {
        "answer": answer_fallback,
        "conversation_id": conversation_id,
        "context": [],
        "search_mode": "none",
        "concepts": [],
        "metrics": {
            "retrieval_time_ms": int((time.time() - inicio_herramientas) * 1000),
            "llm_time_ms": 0,
            "total_time_ms": int((fin_total - inicio_total) * 1000),
            "chunks_retrieved": 0,
            "lexical_matches_count": 0,
            "average_distance": 0.0
        }
    }


# ============================================================
# Endpoint con Streaming SSE /api/chat/stream
# ============================================================
@router.post("/api/chat/stream")
def api_chat_stream(req: ChatRequest):
    global coleccion
    if coleccion is None:
        raise HTTPException(status_code=500, detail="La base vectorial de pruebas no está cargada.")
        
    inicio_total = time.time()
    pregunta_original = req.question
    modelo_llm = req.model
    conversation_id, user_id = resolver_sesion(req)
    nombre_vet_activo = obtener_nombre_veterinaria(req.veterinary_id)

    fecha_actual = str(datetime.date.today())
    año_actual = datetime.date.today().year
    prompt_herramientas = construir_prompt_herramientas(nombre_vet_activo, fecha_actual)
    
    history, messages_with_history, limit = construir_historial(
        req, conversation_id, user_id, prompt_herramientas
    )

    inicio_herramientas = time.time()
    tool_calls_detected = detectar_tools_en_ollama(messages_with_history, modelo_llm, pregunta_original, coleccion)

    context_chunks = []
    contiene_rag = False
    prompt_sistema_final = None

    if tool_calls_detected:
        print(f"✔ Herramientas detectadas por Ollama: {tool_calls_detected}")
        context_chunks, contiene_rag = detectar_y_ejecutar_tools(
            tool_calls_detected, pregunta_original, req, año_actual, coleccion
        )
        
        if context_chunks:
            db_context_str = "\n\n".join([c["text"] for c in context_chunks])
            prompt_sistema_final = construir_prompt_final(nombre_vet_activo, db_context_str)

    def event_stream():
        """Generador de eventos SSE."""
        fin_herramientas = time.time()
        
        # 1. Enviar eventos de herramientas detectadas
        for tc in tool_calls_detected:
            func_name = tc["function"]["name"]
            label = TOOL_LABELS.get(func_name, f"Ejecutando {func_name}...")
            yield f"event: tool_start\ndata: {json.dumps({'tool': func_name, 'label': label})}\n\n"
        
        # 2. Si no hay contexto suficiente, enviar fallback
        if not prompt_sistema_final:
            answer_fallback = "No pude identificar la información solicitada ni una herramienta adecuada para buscarla. ¿Podrías ser más específico o reformular tu pregunta?"
            session_store.guardar_mensaje(conversation_id, "assistant", answer_fallback, req.veterinary_id, user_id)
            yield f"event: error\ndata: {json.dumps({'message': answer_fallback})}\n\n"
            yield f"event: done\ndata: {json.dumps({'conversation_id': conversation_id, 'context': [], 'search_mode': 'none', 'concepts': [], 'metrics': {'retrieval_time_ms': int((fin_herramientas - inicio_herramientas) * 1000), 'llm_time_ms': 0, 'total_time_ms': int((fin_herramientas - inicio_total) * 1000), 'chunks_retrieved': 0, 'lexical_matches_count': 0, 'average_distance': 0.0}})}\n\n"
            return

        # 3. Construir mensajes finales
        messages_final = history[-limit:] if len(history) > limit else history
        if not messages_final or messages_final[0]["role"] != "system":
            messages_final = [{"role": "system", "content": prompt_sistema_final}] + messages_final
        else:
            messages_final = [{"role": "system", "content": prompt_sistema_final}] + messages_final[1:]

        # 4. Streaming desde Ollama
        url = "http://localhost:11434/api/chat"
        payload_final = {
            "model": modelo_llm,
            "messages": messages_final,
            "stream": True,
            "keep_alive": -1,
            "options": {
                "num_ctx": NUM_CTX
            }
        }

        inicio_llm = time.time()
        respuesta_completa = ""
        
        try:
            with requests.post(url, json=payload_final, timeout=120, stream=True) as res:
                if res.status_code != 200:
                    error_msg = f"Error al generar respuesta (HTTP {res.status_code})"
                    session_store.guardar_mensaje(conversation_id, "assistant", error_msg, req.veterinary_id, user_id)
                    yield f"event: error\ndata: {json.dumps({'message': error_msg})}\n\n"
                    return
                
                for line in res.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            token = chunk["message"]["content"]
                            respuesta_completa += token
                            # Enviar token como evento SSE
                            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
                        
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            error_msg = f"Falla de conexión al generar respuesta con Ollama: {e}"
            session_store.guardar_mensaje(conversation_id, "assistant", error_msg, req.veterinary_id, user_id)
            yield f"event: error\ndata: {json.dumps({'message': error_msg})}\n\n"
            return

        # 5. Guardar respuesta completa en la sesión
        if respuesta_completa:
            session_store.guardar_mensaje(conversation_id, "assistant", respuesta_completa, req.veterinary_id, user_id)
        
        fin_total = time.time()
        
        # 6. Enviar evento done con métricas y contexto
        done_data = {
            "conversation_id": conversation_id,
            "context": context_chunks,
            "search_mode": "rag" if contiene_rag else "database",
            "concepts": [],
            "metrics": {
                "retrieval_time_ms": int((fin_herramientas - inicio_herramientas) * 1000),
                "llm_time_ms": int((fin_total - inicio_llm) * 1000),
                "total_time_ms": int((fin_total - inicio_total) * 1000),
                "chunks_retrieved": len(context_chunks),
                "lexical_matches_count": 0,
                "average_distance": 0.0
            }
        }
        yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============================================================
# Endpoint de transcripción de voz
# ============================================================
@router.post("/api/voice/transcribe")
async def api_voice_transcribe(audio: UploadFile = File(...)):
    """Recibe un archivo de audio y retorna la transcripción usando Whisper local."""
    return await transcribir_audio(audio)


@router.get("/api/voice/status")
def api_voice_status():
    """Diagnóstico: indica si Whisper está disponible o si se usa Web Speech API como fallback."""
    return voice_status()


@router.get("/api/chat/history")
def get_chat_history(conversation_id: str | None = None, veterinary_id: int | None = None, user_id: int | None = None):
    user_id = user_id or 1
    if not conversation_id and veterinary_id is not None:
        conversation_id = session_store.obtener_conversacion_activa(veterinary_id, user_id)
    
    if not conversation_id:
        return {"conversation_id": None, "history": []}
        
    history = session_store.obtener_historial(conversation_id, user_id)
    return {"conversation_id": conversation_id, "history": history}

@router.delete("/api/chat/history")
def delete_chat_history(conversation_id: str | None = None, veterinary_id: int | None = None, user_id: int | None = None):
    user_id = user_id or 1
    if conversation_id:
        session_store.eliminar_historial(conversation_id, user_id)
        return {"status": "success", "message": "History deleted for conversation"}
    elif veterinary_id is not None:
        session_store.eliminar_historial_por_sesion(veterinary_id, user_id)
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


# ============================================================
# ENDPOINTS DE AUTENTICACION LOCAL
# ============================================================

from pydantic import BaseModel

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

@router.get("/", response_class=HTMLResponse)
def get_home():
    from app.core.config import STATIC_DIR
    static_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    else:
        return "<h1>Error: frontend index.html no encontrado.</h1>"
