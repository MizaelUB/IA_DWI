import sys
import os
import time
import requests
import json
import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recuperacion import cargar_base_vectorial, extraer_palabras_clave, es_seccion_query, tiene_coincidencia_palabras, normalizar_texto, obtener_conceptos_relacionados
import db_client

app = FastAPI(title="Swingtails RAG Sandbox API")
coleccion = None
NUM_CTX = 16384
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

@app.on_event("startup")
def startup_event():
    global coleccion
    try:
        coleccion = cargar_base_vectorial()
        print("Base vectorial cargada exitosamente en el servidor FastAPI.")
    except Exception as e:
        print(f"Error crítico al cargar base vectorial de pruebas: {e}")
        
    # Llamamos al warm-up para evitar demoras en la primera consulta
    calentar_modelo_ollama()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    model: str = "llama3.2:3b"
    concept_model: str = "llama3.2:3b"
    limit_chunks: int = 5
    history: List[Message] = []
    autonomous_search: bool = False
    veterinary_id: int | None = None

def es_saludo(texto):
    saludos = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "como estas", "que tal", "hello", "hi"}
    texto_limpio = re.sub(r'[¿?.,;:!]', '', normalizar_texto(texto)).strip()
    return texto_limpio in saludos or any(texto_limpio.startswith(s + " ") for s in saludos)

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


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    global coleccion
    if coleccion is None:
        raise HTTPException(status_code=500, detail="La base vectorial de pruebas no está cargada.")
        
    inicio_total = time.time()
    pregunta_original = req.question
    modelo_llm = req.model
    
    nombre_vet_activo = None
    if req.veterinary_id is not None:
        try:
            res_vet = db_client.buscar_veterinarias_por_ciudad_o_nombre(veterinary_id=req.veterinary_id)
            if res_vet.get("status") == "success" and res_vet.get("found") and res_vet.get("data"):
                nombre_vet_activo = res_vet["data"][0]["nombre"]
                print(f"[DEBUG] Veterinaria activa seleccionada por ID {req.veterinary_id}: {nombre_vet_activo}")
        except Exception as e:
            print(f"Error al buscar nombre de veterinaria activa: {e}")
    
    if es_saludo(pregunta_original):
        prompt_sistema = "Eres el asistente virtual de Swingtails, una plataforma de gestión de citas veterinarias. Saluda de manera amable, profesional y muy concisa. Dile brevemente que estás listo para responder preguntas sobre Swingtails, procesos de la clínica o mercadotecnia veterinaria."
        inicio_llm = time.time()
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": modelo_llm,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": pregunta_original}
            ],
            "stream": False,
            "keep_alive": -1
        }
        try:
            respuesta = requests.post(url, json=payload, timeout=30)
            answer = respuesta.json()['message']['content']
        except Exception as e:
            answer = f"Error al generar saludo: {e}"
            
        return {
            "answer": answer,
            "context": [],
            "metrics": {
                "retrieval_time_ms": 0,
                "llm_time_ms": int((time.time() - inicio_llm) * 1000),
                "total_time_ms": int((time.time() - inicio_total) * 1000),
                "chunks_retrieved": 0,
                "lexical_matches_count": 0,
                "average_distance": 0.0
            }
        }
        
    # Definición de herramientas para Function Calling
    db_tools = [
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
                "description": "Obtiene el historial y próximas citas de una mascota por su nombre.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre_mascota": {
                            "type": "string",
                            "description": "El nombre de la mascota."
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
                "description": "Obtiene las citas agendadas para una fecha o rango de fechas específico. Obligatorio usar formato YYYY-MM-DD.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fecha_inicio": {
                            "type": "string",
                            "description": "La fecha de inicio de consulta ESTRICTAMENTE en formato YYYY-MM-DD (ej. 2026-05-14)."
                        },
                        "fecha_fin": {
                            "type": "string",
                            "description": "La fecha de fin ESTRICTAMENTE en formato YYYY-MM-DD para un rango (opcional)."
                        }
                    },
                    "required": ["fecha_inicio"]
                }
            }
        }
    ]

    tool_mappers = {
        "buscar_mascota_por_nombre": db_client.buscar_mascota_por_nombre,
        "buscar_mascotas_por_dueno": db_client.buscar_mascotas_por_dueno,
        "buscar_citas_por_mascota": db_client.buscar_citas_por_mascota,
        "buscar_veterinarias_por_ciudad_o_nombre": db_client.buscar_veterinarias_por_ciudad_o_nombre,
        "ver_servicios_y_productos_veterinaria": db_client.ver_servicios_y_productos_veterinaria,
        "ver_resenas_veterinaria": db_client.ver_resenas_veterinaria,
        "ver_citas_por_fecha": db_client.ver_citas_por_fecha,
    }

    url = "http://localhost:11434/api/chat"
    
    año_actual = datetime.date.today().year
    prompt_herramientas = f"""Eres el asistente virtual de la clínica veterinaria '{nombre_vet_activo or "Swingtails"}'. Swingtails es una plataforma de gestión de citas veterinarias.
El año actual es {año_actual}.

REGLAS DE SELECCIÓN DE HERRAMIENTAS:
1. Si la pregunta es sobre la estrategia de mercadotecnia, logo, marca, manuales o procesos generales, llama a 'consultar_manuales_y_procesos_generales'.
2. Si el usuario busca un ANIMAL y te da su nombre, llama a 'buscar_mascota_por_nombre'.
3. Si el usuario busca a una PERSONA/CLIENTE para ver sus mascotas, llama a 'buscar_mascotas_por_dueno'.
4. Si en la pregunta se indica explícitamente un ID numérico de mascota, pásalo en 'pet_id'.
5. Si la pregunta requiere buscar citas por fecha, formatea los argumentos 'fecha_inicio' y 'fecha_fin' ESTRICTAMENTE en YYYY-MM-DD.
6. IMPORTANTE: Como solo conoces el año {año_actual}, si el usuario usa términos relativos ('mañana', 'hoy') sin dar fecha exacta, PÍDELE amablemente el día y mes exacto.
7. REGLA CRÍTICA DE FORMATO: Al llenar los argumentos de las herramientas, SIEMPRE usa los valores reales de texto o número. NUNCA devuelvas diccionarios internos con las palabras 'description' o 'type'."""
    messages_with_history = [{"role": "system", "content": prompt_herramientas}]
    for msg in req.history:
        messages_with_history.append({"role": msg.role, "content": msg.content})
    messages_with_history.append({"role": "user", "content": pregunta_original})

     

    payload_tools = {
        "model": modelo_llm,
        "messages": messages_with_history,
        "tools": db_tools,
        "stream": False,
        "keep_alive": -1,
        "options": {
            "num_ctx": NUM_CTX
        }
    }

    tool_calls_detected = []
    inicio_herramientas = time.time()
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

    if tool_calls_detected:
        print(f"✔ Herramientas detectadas por Ollama: {tool_calls_detected}")
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
                    modelo_conceptos = modelo_llm if req.concept_model == req.__fields__["concept_model"].default else req.concept_model
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
                if func_name == "buscar_mascota_por_nombre":
                    nombre_mascota = func_args.get("nombre_mascota")
                    # Si Ollama serializó un JSON en el string
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
                    
                    # Extracción defensiva del ID del texto de la pregunta
                    if not func_args.get("pet_id"):
                        match_id = re.search(r'\b(?:id|ID|identificador)\s*[:=]?\s*(\d+)\b', pregunta_original)
                        if match_id:
                            func_args["pet_id"] = int(match_id.group(1))

                # ---------------- BLOQUE DE PARSEO DE FECHAS ----------------
                if func_name == "ver_citas_por_fecha":
                    if "fecha_inicio" in func_args and func_args["fecha_inicio"]:
                        func_args["fecha_inicio"] = parsear_fecha(func_args["fecha_inicio"], año_actual)
                    if "fecha_fin" in func_args and func_args["fecha_fin"]:
                        func_args["fecha_fin"] = parsear_fecha(func_args["fecha_fin"], año_actual)
                # ------------------------------------------------------------

                start_db = time.time()
                try:
                    # Ejecutar la consulta en Supabase pasando el veterinary_id
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
        
        if context_chunks:
            db_context_str = "\n\n".join([c["text"] for c in context_chunks])
            
            prompt_sistema_final = f"""Eres el asistente virtual de la clínica veterinaria '{nombre_vet_activo or "Swingtails"}' dirigido a médicos veterinarios, administradores y clientes. Swingtails es una plataforma de gestión de citas veterinarias. Tu única fuente de verdad para esta respuesta es la INFORMACIÓN OBTENIDA abajo.
            
INFORMACIÓN OBTENIDA DE LA CLÍNICA:
{db_context_str}

INSTRUCCIONES DE RESPUESTA:
1. Responde a la pregunta del usuario de manera clara, estructurada, amable y profesional usando ÚNICAMENTE la INFORMACIÓN OBTENIDA.
2. Como eres el asistente de la clínica '{nombre_vet_activo or "Swingtails"}', saluda e interactúa en su nombre.
3. Si la información indica que no se encontraron datos o está vacía, menciónalo de manera educada y clara.
4. NUNCA uses frases como "Según la información de la base de datos", "De acuerdo al contexto" o similares.
5. No uses tu conocimiento general.
6. Organiza la información en listas o tablas Markdown para facilitar su lectura.
7. Si el resultado de buscar mascotas contiene múltiples mascotas con el mismo nombre y el usuario no especificó el parámetro 'pet_id', debes listar todas las mascotas encontradas (con sus respectivos IDs, especie, raza y dueño) y preguntarle explícitamente al usuario que te indique el ID de la mascota específica.
"""
            inicio_llm = time.time()
            payload_final = {
                "model": modelo_llm,
                "messages": [
                    {"role": "system", "content": prompt_sistema_final},
                    {"role": "user", "content": pregunta_original}
                ],
                "stream": False,
                "keep_alive": -1,
                "options": {
                    "num_ctx": NUM_CTX
                }
            }
            
            try:
                res_final = requests.post(url, json=payload_final, timeout=90)
                if res_final.status_code == 200:
                    answer = res_final.json()['message']['content']
                else:
                    answer = f"Error al generar respuesta final (HTTP {res_final.status_code})"
            except Exception as e:
                answer = f"Falla de conexión al generar respuesta final con Ollama: {e}"
                
            fin_total = time.time()
            return {
                "answer": answer,
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
    return {
        "answer": "No pude identificar la información solicitada ni una herramienta adecuada para buscarla. ¿Podrías ser más específico o reformular tu pregunta?",
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

@app.get("/", response_class=HTMLResponse)
def get_home():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_file = os.path.join(script_dir, "static", "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    else:
        return "<h1>Error: frontend index.html no encontrado.</h1>"