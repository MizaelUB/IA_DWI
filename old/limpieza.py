import fitz
import re
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def ingestar_y_fragmentar_pdf(ruta_pdf):
    print(f"Iniciando el procesamiento de: {ruta_pdf}")
    documento = fitz.open(ruta_pdf)
    chunks = []
    
    nombre_archivo = os.path.basename(ruta_pdf)
    
    for i, pagina in enumerate(documento):
        texto_crudo = pagina.get_text("text")
        
        texto = re.sub(r'Página \d+ de \d+', '', texto_crudo)
        texto = re.sub(r'\n\d+\n', '\n', texto)
        texto = re.sub(r'\n{3,}', '\n\n', texto)
        texto = re.sub(r' +', ' ', texto)
        texto = texto.strip()
        
        if texto:
            chunks.append(Document(
                page_content=texto, 
                metadata={
                    "source": ruta_pdf, 
                    "archivo": nombre_archivo,
                    "tema": f"Documento: {nombre_archivo} - Página {i+1}"
                }
            ))
            
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    final_chunks = splitter.split_documents(chunks)
    print(f"✓ Chunks finales (por hoja/tema): {len(final_chunks)}")
    return final_chunks

def ingestar_y_fragmentar_txt(ruta_txt):
    print(f"Iniciando el procesamiento de: {ruta_txt}")
    with open(ruta_txt, 'r', encoding='utf-8') as f:
        texto = f.read()
        
    nombre_archivo = os.path.basename(ruta_txt)
    secciones_crudas = texto.split('\n## ')
    chunks = []
    
    for i, seccion in enumerate(secciones_crudas):
        seccion = seccion.strip()
        if not seccion:
            continue
        if i > 0:
            seccion = "## " + seccion
            
        lineas = seccion.split('\n')
        titulo = lineas[0].replace('## ', '').replace('# ', '').strip()
        if not titulo:
            titulo = f"Seccion_{i}"
            
        chunks.append(Document(
            page_content=seccion, 
            metadata={
                "source": ruta_txt, 
                "archivo": nombre_archivo,
                "tema": titulo
            }
        ))
        
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
    final_chunks = splitter.split_documents(chunks)
    print(f"✓ Chunks finales de texto separados por tema estricto: {len(final_chunks)}")
    return final_chunks
