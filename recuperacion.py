import chromadb
from chromadb.utils import embedding_functions
import requests
import re
import os

def cargar_base_vectorial():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_db = os.path.join(script_dir, "mi_base_vectorial")
    
    print(f"Cargando base vectorial desde: {ruta_db}")
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text"
    )
    client = chromadb.PersistentClient(path=ruta_db)
    coleccion = client.get_collection(
        name="contexto_sw",
        embedding_function=ollama_ef
    )
    return coleccion

def normalizar_texto(texto):
    texto = texto.lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u"
    }
    for orig, rep in replacements.items():
        texto = texto.replace(orig, rep)
    return texto

def es_seccion_query(texto):
    return re.search(r'secci[oó]n\s*\d+', texto.lower())

def extraer_palabras_clave(pregunta_usuario):
    stopwords = {
        "que", "como", "cuando", "donde", 
        "por", "cual", "cuales", "es", "son", "el", "la", 
        "los", "las", "un", "una", "unos", "unas", "de", "del", "en", "para", 
        "a", "y", "o", "con", "sobre", "este", "esta", "estos", "estas", 
        "dime", "hablame", "explicame", "acerca"
    }
    texto_normalizado = normalizar_texto(pregunta_usuario)
    texto_limpio = re.sub(r'[¿?.,;:!]', '', texto_normalizado)
    palabras = texto_limpio.split()
    palabras_clave = [p for p in palabras if p not in stopwords]
    resultado = " ".join(palabras_clave)
    return resultado if resultado else pregunta_usuario

def tiene_coincidencia_palabras(pregunta_palabras, contexto):
    contexto_normalizado = normalizar_texto(contexto)
    contexto_limpio = re.sub(r'[¿?.,;:!\-\*#\n]', ' ', contexto_normalizado)
    palabras_contexto = set(contexto_limpio.split())
    
    pregunta_normalizada = normalizar_texto(pregunta_palabras)
    palabras_pregunta = set(pregunta_normalizada.split())
    palabras_pregunta_filtradas = {p for p in palabras_pregunta if len(p) > 2}
    if not palabras_pregunta_filtradas:
        palabras_pregunta_filtradas = palabras_pregunta
        
    return len(palabras_pregunta_filtradas.intersection(palabras_contexto)) > 0


def limpiar_conceptos(texto_crudo: str) -> list:
    texto_limpio = re.sub(r'(?i)^\s*(conceptos relacionados|conceptos|palabras clave|terminos de busqueda|respuesta|conceptos clave|terminos):\s*', '', texto_crudo)
    
    lineas = texto_limpio.strip().split('\n')
    conceptos = []
    for linea in lineas:
        linea_limpia = linea.strip()
        if not linea_limpia:
            continue
        linea_limpia = re.sub(r'^[\d\-\*\u2022\.]+\s*', '', linea_limpia)
        linea_limpia = re.sub(r'(?i)^\s*(conceptos relacionados|conceptos|palabras clave|terminos de busqueda|respuesta|conceptos clave|terminos):\s*', '', linea_limpia)
        linea_limpia = linea_limpia.strip().strip('"\'`')
        if not linea_limpia:
            continue
        if ',' in linea_limpia:
            partes = [p.strip().strip('"\'`') for p in linea_limpia.split(',') if p.strip()]
            conceptos.extend(partes)
        else:
            conceptos.append(linea_limpia)
            
    conceptos_filtrados = []
    for c in conceptos:
        c_low = c.lower()
        if len(c.split()) > 4 or len(c) > 30:
            continue
        
        c_sin_punto = re.sub(r'\.$', '', c).strip()
        
        if not re.match(r'^[a-zA-Z0-9áéíóúüñÁÉÍÓÚÜÑ\s\-]+$', c_sin_punto):
            continue
            
        conversacionales = {"hola", "gracias", "adios", "avísame", "avisame", "entendido", "ok", "claro", "por favor"}
        if c_sin_punto.lower() in conversacionales:
            continue
        
        if any(verbo in c_low for verbo in [" es un ", " es una ", " son los ", " se refiere ", " sirve para ", " permite que "]):
            continue
            
        if any(intro in c_low for intro in ["aqui tienes", "conceptos relacionados", "respuesta:", "segun la", "temas clave"]):
            continue
            
        if len(c_sin_punto) > 1:
            conceptos_filtrados.append(c_sin_punto)
            
    return conceptos_filtrados[:4]

def obtener_conceptos_relacionados(pregunta: str, historial: list = None, modelo_llm: str = "llama3.2:3b") -> list:
    prompt_sistema = """Tu única tarea es extraer o generar de 2 a 4 conceptos clave o términos de búsqueda muy cortos (de 1 a 3 palabras cada uno) separados por comas, basados en la pregunta del usuario.

REGLAS CRÍTICAS:
1. Responde ÚNICAMENTE con los conceptos separados por comas.
2. NO escribas oraciones completas, NO expliques nada, NO des definiciones ni párrafos.
3. Si la pregunta es sobre una palabra o tema, responde solo con esa palabra y de 1 a 3 sinónimos o conceptos muy relacionados.
4. NUNCA respondas con una explicación del término.
5. El proyecto se llama Swingtails, podria ser relevante como concepto si la pregunta es sobre la plataforma, gestión veterinaria o temas relacionados. (ej, de que trata -> de que trata swingtails)
6. Si la pregunta contiene nombres propios de personas, mascotas, clínicas o entidades específicas (ej. "María Elena", "Toby", "Bruno", "Sofia", "Pet Health"), CADA uno de los conceptos generados DEBE obligatoriamente contener ese nombre propio para asegurar que las búsquedas sean específicas y no genéricas.

Ejemplos de respuesta correcta:
Pregunta: ¿Cómo se maneja una queja de cliente?
protocolo de quejas, servicio al cliente, resolución de conflictos, atención al cliente

Pregunta: ¿Qué vacunas necesita un gato cachorro?
calendario de vacunación felina, inmunización de cachorros, vacunas para gatos

Pregunta: ¿Quién es Toby?
Toby, mascota toby, expediente toby, dueño toby

Pregunta: Swingtails
Swingtails, plataforma digital, gestión veterinaria, veterinarias México
"""
    mensajes = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": f"Pregunta: {pregunta}"}
    ]
    
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": modelo_llm,
        "messages": mensajes,
        "stream": False,
        "keep_alive": -1, # CORREGIDO: Evita que el modelo se apague
        "options": {
            "num_ctx": 8000 
        }
    }
    
    try:
        respuesta = requests.post(url, json=payload, timeout=20)
        if respuesta.status_code == 200:
            texto_respuesta = respuesta.json()['message']['content']
            return limpiar_conceptos(texto_respuesta)
    except Exception as e:
        print(f"Error generando conceptos relacionados: {e}")
    return []

def consultar_rag(pregunta: str, coleccion, modelo_llm: str = "llama3.2:3b", autonomous_search: bool = False, historial: list = None):
    """Función independiente para hacer pruebas en consola local."""
    pregunta_optimizada = extraer_palabras_clave(pregunta)
    query_texts = [pregunta, pregunta_optimizada]
    conceptos_generados = []
    
    if autonomous_search:
        print("\nGenerando conceptos relacionados de forma autónoma con el LLM...")
        conceptos_generados = obtener_conceptos_relacionados(pregunta, historial, modelo_llm)
        if conceptos_generados:
            print(f"✔ Conceptos identificados por la IA: {conceptos_generados}")
            query_texts.extend(conceptos_generados)
            
    print(f"\nBuscando similitudes para los términos: {query_texts}...")
    
    n = 12 if es_seccion_query(pregunta) else 8
        
    resultados = coleccion.query(
        query_texts=query_texts,
        n_results=n,
        include=["documents", "distances", "metadatas"]
    )
    
    docs_unicos = []
    mejores_distancias = []
    temas_unicos = []
    
    for i in range(len(resultados['documents'])): 
        for j, doc in enumerate(resultados['documents'][i]):
            dist = resultados['distances'][i][j]
            meta = resultados['metadatas'][i][j]
            tema = meta.get("tema", "Sin Tema")
            
            if doc not in docs_unicos:
                docs_unicos.append(doc)
                mejores_distancias.append(dist)
                temas_unicos.append(tema)
                
    USAR_BUSQUEDA_LEXICA = True
    docs_lexicos_añadidos = 0
    
    if USAR_BUSQUEDA_LEXICA:
        palabras_clave = [p for p in pregunta_optimizada.lower().split() if len(p) > 3]
        for palabra in palabras_clave:
            variantes = {palabra, palabra.capitalize(), palabra.upper()}
            for var in variantes:
                try:
                    res_lex = coleccion.get(where_document={"$contains": var})
                    if res_lex and res_lex['documents']:
                        for doc, meta in zip(res_lex['documents'], res_lex['metadatas']):
                            if doc not in docs_unicos:
                                docs_unicos.append(doc)
                                mejores_distancias.append(0.0)
                                temas_unicos.append(meta.get("tema", "Búsqueda Léxica"))
                                docs_lexicos_añadidos += 1
                except Exception as e:
                    pass
                
    if docs_lexicos_añadidos > 0:
        print(f"✔ Búsqueda léxica de respaldo añadió {docs_lexicos_añadidos} fragmentos con coincidencia exacta.")

    if not docs_unicos:
        return "No tengo información en la base de datos para responder a esto."
        
    contexto_recuperado = "\n\n".join(docs_unicos)
    
    filtro_palabras = pregunta_optimizada
    if autonomous_search and conceptos_generados:
        filtro_palabras = pregunta_optimizada + " " + " ".join(conceptos_generados)
        
    if not tiene_coincidencia_palabras(filtro_palabras, contexto_recuperado):
        return "No tengo información en la base de datos."
        
    for idx, (doc, tema, dist) in enumerate(zip(docs_unicos, temas_unicos, mejores_distancias)):
        print(f"\n--- Fragmento #{idx+1} [Origen/Tema: {tema}] [Distancia: {dist:.4f}] ---")
        lineas_doc = doc.split('\n')
        preview = '\n'.join(lineas_doc[:4]) + ("\n..." if len(lineas_doc) > 4 else "")
        print(preview)
    
    docs = sorted(docs_unicos, key=len, reverse=True)
    contexto_recuperado_ordenado = "\n\n".join(docs)
    
    prompt_sistema = f"""
Eres un asistente virtual de Swingtails sumamente estricto, diseñado para brindar soporte y guiar a médicos veterinarios en la gestión y procesos de sus clínicas. Tu única fuente de verdad es el CONTEXTO proporcionado. No menciones que tienes un contexto.

CONTEXTO:
{contexto_recuperado_ordenado}

INSTRUCCIONES DE RESPUESTA:
1. Responde a los médicos veterinarios de forma directa, objetiva y concisa utilizando ÚNICAMENTE la información del CONTEXTO.
2. Si respondes la pregunta utilizando el CONTEXTO, no agregues aclaraciones sobre lo que NO está, ni digas que te falta información adicional.
3. Si el CONTEXTO no contiene la información para responder a la pregunta, debes contestar única y exclusivamente con esta frase exacta, sin añadir nada más: "No tengo información en la base de datos".
4. No uses tu conocimiento general. No inventes, deduzcas ni supongas nada que no esté explícitamente escrito.
5. Si el usuario te hace preguntas banales, personales, de conversación casual, o sin relación directa con el proyecto Swingtails y el contexto clínico/mercadotecnia proporcionado, debes responder única y exclusivamente con la frase exacta: "No tengo información en la base de datos".
"""
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": modelo_llm,
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pregunta}
        ],
        "stream": False,
        "keep_alive": -1, # CORREGIDO: Evita que el modelo se apague
    }
    
    try:
        respuesta = requests.post(url, json=payload, timeout=120)
        return respuesta.json()['message']['content']
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    coleccion_db = cargar_base_vectorial()
    MI_MODELO = "llama3.2:3b" # Actualizado para hacer match con tu backend
    
    print(f"Iniciando consulta interactiva con el modelo: {MI_MODELO}")
    while True:
        consulta = input("\nHaz una pregunta (o 'salir'): ")
        if consulta.lower() in ['salir', 'exit']:
            break
        print("\nRESPUESTA:", consultar_rag(consulta, coleccion_db, MI_MODELO))