import chromadb
from chromadb.utils import embedding_functions
import shutil
import os
from limpieza import ingestar_y_fragmentar_pdf, ingestar_y_fragmentar_txt

def inicializar_base_vectorial():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_db = os.path.join(script_dir, "mi_base_vectorial")
    docs_dir = os.path.abspath(os.path.join(script_dir, "docs"))
    
    if os.path.exists(ruta_db):
        try:
            shutil.rmtree(ruta_db)
            print("🗑 Directorio de base vectorial de pruebas eliminado")
        except Exception as e:
            print(f"⚠ No se pudo eliminar el directorio de la base de datos: {e}")

    print(f"1. Escaneando documentos en: {docs_dir}")
    fragmentos = []
    
    if os.path.exists(docs_dir):
        for archivo in os.listdir(docs_dir):
            ruta_archivo = os.path.join(docs_dir, archivo)
            ext = archivo.lower()
            
            if ext.endswith(".md"):
                print(f"\n📄 Encontrado archivo Markdown: {archivo}")
                nuevos_fragmentos = ingestar_y_fragmentar_txt(ruta_archivo)
                fragmentos.extend(nuevos_fragmentos)
                
            elif ext.endswith(".pdf"):
                print(f"\n📕 Encontrado archivo PDF: {archivo}")
                nuevos_fragmentos = ingestar_y_fragmentar_pdf(ruta_archivo)
                fragmentos.extend(nuevos_fragmentos)
                
            else:
                pass
    else:
        print(f"❌ Error: La carpeta de documentos {docs_dir} no existe.")
        return
        
    if not fragmentos:
        print("❌ Error: No se encontraron fragmentos para indexar.")
        return
        
    print(f"\n2. Total de fragmentos recolectados: {len(fragmentos)}")
    print("Configurando embeddings locales con Ollama (nomic-embed-text)...")
    
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        url="http://localhost:11434/api/embeddings",
        model_name="nomic-embed-text"
    )
    
    client = chromadb.PersistentClient(path=ruta_db)
    try:
        client.delete_collection("contexto_sw")
        print("🗑 Colección anterior 'contexto_sw' eliminada lógicamente")
    except Exception:
        pass
    coleccion = client.get_or_create_collection(
        name="contexto_sw",
        embedding_function=ollama_ef,
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"\n3. Insertando {len(fragmentos)} chunks en la base vectorial...")
    textos = [doc.page_content for doc in fragmentos]
    metadatos = [doc.metadata for doc in fragmentos]
    ids = [f"id_{i}" for i in range(len(fragmentos))]
    
    batch = 100
    for i in range(0, len(textos), batch):
        coleccion.add(
            documents=textos[i:i+batch],
            metadatas=metadatos[i:i+batch],
            ids=ids[i:i+batch]
        )
        print(f"✔ Lote {i//batch + 1} insertado ({min(i+batch, len(textos))}/{len(textos)})")
        
    print("\n✅ Base de datos vectorial de pruebas inicializada correctamente.")

if __name__ == "__main__":
    inicializar_base_vectorial()
