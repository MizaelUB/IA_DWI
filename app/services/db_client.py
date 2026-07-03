import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno del .env en la raíz del proyecto
from app.core.config import DOTENV_PATH
dotenv_path = DOTENV_PATH
load_dotenv(dotenv_path)

def get_connection():
    """Establece y retorna una conexión a la base de datos PostgreSQL de Supabase."""
    db_name = os.environ.get("DB_DATABASE", "postgres")
    db_host = os.environ.get("DB_HOST", "aws-0-us-east-1.pooler.supabase.com")
    db_port = os.environ.get("DB_PORT", "5432")
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "")
    
    return psycopg2.connect(
        dbname=db_name,
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password
    )

def buscar_mascotas_por_dueno(nombre_dueno: str, veterinary_id: int = None) -> dict:
    """
    Busca todas las mascotas que pertenecen a un dueño según el nombre parcial o completo,
    opcionalmente filtrado por el ID de la clínica veterinaria.
    """
    query = """
        SELECT DISTINCT
            u.name as dueno_nombre,
            u.phone_number,
            u.email,
            p.name as mascota_nombre,
            p.specie,
            p.breed,
            p.sex,
            p.age,
            p.weight
        FROM users_app u
        JOIN pets p ON u.id = p.user_id
        LEFT JOIN appointments a ON p.id = a.pet_id
        WHERE u.name ILIKE %s
          AND (%s::integer IS NULL OR a.veterinary_id = %s);
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (f"%{nombre_dueno}%", veterinary_id, veterinary_id))
                rows = cur.fetchall()
                
                if not rows:
                    return {"status": "success", "found": False, "data": []}
                
                mascotas = []
                for row in rows:
                    mascotas.append({
                        "dueno": row[0],
                        "telefono_dueno": row[1],
                        "email_dueno": row[2],
                        "nombre": row[3],
                        "especie": row[4],
                        "raza": row[5] if row[5] else "No especificada",
                        "sexo": row[6],
                        "edad": row[7],
                        "peso": float(row[8]) if row[8] is not None else None
                    })
                return {"status": "success", "found": True, "data": mascotas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def buscar_citas_por_mascota(nombre_mascota: str, veterinary_id: int = None) -> dict:
    """
    Busca el historial y citas agendadas de una mascota por su nombre,
    opcionalmente filtrado por el ID de la clínica veterinaria.
    """
    query = """
        SELECT 
            a.id,
            a.pet_name,
            a.appointment_date,
            a.hour,
            a.status,
            a.total_cost,
            a.notes,
            v.name as veterinaria_nombre,
            a.pickup_requested,
            a.pickup_status,
            a.pet_id
        FROM appointments a
        LEFT JOIN veterinary v ON a.veterinary_id = v.id
        WHERE (a.pet_name ILIKE %s OR a.pet_id IN (SELECT id FROM pets WHERE name ILIKE %s))
          AND (%s::integer IS NULL OR a.veterinary_id = %s)
        ORDER BY a.appointment_date DESC, a.hour DESC;
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                pattern = f"%{nombre_mascota}%"
                cur.execute(query, (pattern, pattern, veterinary_id, veterinary_id))
                rows = cur.fetchall()
                
                if not rows:
                    return {"status": "success", "found": False, "data": []}
                
                citas = []
                for row in rows:
                    citas.append({
                        "id": row[0],
                        "mascota": row[1],
                        "fecha": str(row[2]),
                        "hora": str(row[3]),
                        "estado": row[4],
                        "costo_total": float(row[5]) if row[5] is not None else 0.0,
                        "notas": row[6] if row[6] else "",
                        "veterinaria": row[7] if row[7] else "Desconocida",
                        "recoleccion_solicitada": bool(row[8]),
                        "recoleccion_estado": row[9] if row[9] else "No aplica",
                        "pet_id": row[10]
                    })
                return {"status": "success", "found": True, "data": citas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def buscar_veterinarias_por_ciudad_o_nombre(ciudad: str = None, nombre: str = None, veterinary_id: int = None) -> dict:
    """
    Busca veterinarias por ciudad, nombre o filtra por su ID.
    """
    query = """
        SELECT 
            id, name, street, neighborhood, exterior_number, postal_code, city, state, phone_number, email, description
        FROM veterinary
        WHERE is_active = TRUE
          AND (%s::integer IS NULL OR id = %s)
          AND (%s IS NULL OR city ILIKE %s)
          AND (%s IS NULL OR name ILIKE %s);
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                city_param = f"%{ciudad}%" if ciudad else None
                name_param = f"%{nombre}%" if nombre else None
                cur.execute(query, (veterinary_id, veterinary_id, city_param, city_param, name_param, name_param))
                rows = cur.fetchall()
                
                if not rows:
                    return {"status": "success", "found": False, "data": []}
                
                vets = []
                for row in rows:
                    vets.append({
                        "id": row[0],
                        "nombre": row[1],
                        "direccion": f"{row[2]}, No. {row[4]}, Col. {row[3]}, C.P. {row[5]}",
                        "ciudad": row[6],
                        "estado": row[7],
                        "telefono": row[8],
                        "email": row[9],
                        "descripcion": row[10]
                    })
                return {"status": "success", "found": True, "data": vets}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ver_servicios_y_productos_veterinaria(nombre_veterinaria: str = None, veterinary_id: int = None) -> dict:
    """
    Busca una veterinaria por nombre o ID y obtiene la lista de sus servicios y productos ofrecidos.
    """
    vet_query = """
        SELECT id, name FROM veterinary 
        WHERE is_active = TRUE
          AND (%s::integer IS NULL OR id = %s)
          AND (%s IS NULL OR name ILIKE %s)
        LIMIT 1;
    """
    
    services_query = """
        SELECT s.name, s.description, vso.price, vso.custom_duration_minutes, vso.custom_description
        FROM veterinary_service_offerings vso
        JOIN services s ON vso.service_id = s.id
        WHERE vso.veterinary_id = %s AND vso.is_active = TRUE;
    """
    
    products_query = """
        SELECT name, description, price, stock, is_available
        FROM products
        WHERE veterinary_id = %s AND is_available = TRUE;
    """
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Obtener la veterinaria
                name_param = f"%{nombre_veterinaria}%" if nombre_veterinaria else None
                cur.execute(vet_query, (veterinary_id, veterinary_id, name_param, name_param))
                vet_row = cur.fetchone()
                if not vet_row:
                    term = f"ID: {veterinary_id}" if veterinary_id else f"nombre: {nombre_veterinaria}"
                    return {"status": "success", "found": False, "message": f"No se encontró veterinaria activa con: {term}"}
                
                vet_id, vet_name = vet_row
                
                # 2. Obtener servicios
                cur.execute(services_query, (vet_id,))
                service_rows = cur.fetchall()
                servicios = []
                for r in service_rows:
                    servicios.append({
                        "nombre": r[0],
                        "descripcion_general": r[1],
                        "precio": float(r[2]),
                        "duracion_minutos": r[3],
                        "descripcion_personalizada": r[4] if r[4] else ""
                    })
                
                # 3. Obtener productos
                cur.execute(products_query, (vet_id,))
                product_rows = cur.fetchall()
                productos = []
                for r in product_rows:
                    productos.append({
                        "nombre": r[0],
                        "descripcion": r[1] if r[1] else "",
                        "precio": float(r[2]),
                        "stock": r[3],
                        "disponible": bool(r[4])
                    })
                
                return {
                    "status": "success",
                    "found": True,
                    "veterinaria": vet_name,
                    "servicios": servicios,
                    "productos": productos
                }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ver_resenas_veterinaria(nombre_veterinaria: str = None, veterinary_id: int = None) -> dict:
    """
    Obtiene las reseñas y calificaciones de una veterinaria por su nombre o ID.
    """
    query = """
        SELECT vr.name, vr.rating, vr.comment, vr.created_at, v.name
        FROM veterinary_reviews vr
        JOIN veterinary v ON vr.veterinary_id = v.id
        WHERE (%s::integer IS NULL OR v.id = %s)
          AND (%s IS NULL OR v.name ILIKE %s)
        ORDER BY vr.created_at DESC;
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                name_param = f"%{nombre_veterinaria}%" if nombre_veterinaria else None
                cur.execute(query, (veterinary_id, veterinary_id, name_param, name_param))
                rows = cur.fetchall()
                
                if not rows:
                    return {"status": "success", "found": False, "data": []}
                
                resenas = []
                for row in rows:
                    resenas.append({
                        "usuario": row[0],
                        "calificacion": row[1],
                        "comentario": row[2] if row[2] else "",
                        "fecha": str(row[3]) if row[3] else "",
                        "veterinaria": row[4]
                    })
                return {"status": "success", "found": True, "data": resenas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def ver_citas_por_fecha(fecha_inicio: str = None, fecha_fin: str = None, veterinary_id: int = None, rango_futuro: bool = False, estado: str = None) -> dict:
    """
    Obtiene las citas agendadas para una fecha, rango de fechas, o citas futuras/pendientes desde hoy.
    """
    import datetime
    si_no_se_dieron_fechas = not fecha_inicio and not fecha_fin

    if not fecha_inicio:
        fecha_inicio = str(datetime.date.today())
        
    if si_no_se_dieron_fechas:
        rango_futuro = False
        fecha_fin = str(datetime.date.today() + datetime.timedelta(days=30))

    if rango_futuro:
        query = """
            SELECT 
                a.id,
                a.pet_name,
                a.appointment_date,
                a.hour,
                a.status,
                a.total_cost,
                a.notes,
                v.name as veterinaria_nombre,
                a.pickup_requested,
                a.pickup_status,
                a.pet_id
            FROM appointments a
            LEFT JOIN veterinary v ON a.veterinary_id = v.id
            WHERE a.appointment_date >= %s::date
              AND (%s::integer IS NULL OR a.veterinary_id = %s)
              AND (%s IS NULL OR a.status ILIKE %s)
            ORDER BY a.appointment_date ASC, a.hour ASC;
        """
    else:
        if not fecha_fin:
            if si_no_se_dieron_fechas:
                fecha_fin = str(datetime.date.today() + datetime.timedelta(days=30))
            else:
                fecha_fin = fecha_inicio
        query = """
            SELECT 
                a.id,
                a.pet_name,
                a.appointment_date,
                a.hour,
                a.status,
                a.total_cost,
                a.notes,
                v.name as veterinaria_nombre,
                a.pickup_requested,
                a.pickup_status,
                a.pet_id
            FROM appointments a
            LEFT JOIN veterinary v ON a.veterinary_id = v.id
            WHERE a.appointment_date BETWEEN %s::date AND %s::date
              AND (%s::integer IS NULL OR a.veterinary_id = %s)
              AND (%s IS NULL OR a.status ILIKE %s)
            ORDER BY a.appointment_date ASC, a.hour ASC;
        """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if rango_futuro:
                    cur.execute(query, (fecha_inicio, veterinary_id, veterinary_id, estado, estado))
                else:
                    cur.execute(query, (fecha_inicio, fecha_fin, veterinary_id, veterinary_id, estado, estado))
                rows = cur.fetchall()
                
                if not rows:
                    return {"status": "success", "found": False, "data": []}
                
                citas = []
                for row in rows:
                    citas.append({
                        "id": row[0],
                        "mascota": row[1],
                        "fecha": str(row[2]),
                        "hora": str(row[3]),
                        "estado": row[4],
                        "costo_total": float(row[5]) if row[5] is not None else 0.0,
                        "notas": row[6] if row[6] else "",
                        "veterinaria": row[7] if row[7] else "Desconocida",
                        "recoleccion_solicitada": bool(row[8]),
                        "recoleccion_estado": row[9] if row[9] else "No aplica",
                        "pet_id": row[10]
                    })
                return {"status": "success", "found": True, "data": citas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def buscar_mascota_por_nombre(nombre_mascota: str = None, veterinary_id: int = None, pet_id: int = None) -> dict:
    """
    Busca mascotas por nombre parcial o completo filtrando únicamente por la veterinaria.
    Si se proporciona pet_id, se hace una búsqueda exacta por dicho ID.
    """
    query = """
        SELECT DISTINCT
            p.id as mascota_id,
            p.name as mascota_nombre,
            p.specie,
            p.breed,
            p.sex,
            p.age,
            p.weight,
            u.name as dueno_nombre,
            u.phone_number as dueno_telefono
        FROM pets p
        JOIN users_app u ON p.user_id = u.id
        LEFT JOIN appointments a ON p.id = a.pet_id
        WHERE (%s::integer IS NULL OR p.id = %s)
          AND (%s IS NULL OR p.name ILIKE %s)
          AND (%s::integer IS NULL OR a.veterinary_id = %s);
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                name_param = f"%{nombre_mascota}%" if nombre_mascota else None
                cur.execute(query, (pet_id, pet_id, name_param, name_param, veterinary_id, veterinary_id))
                rows = cur.fetchall()
                
                if not rows:
                    return {"status": "success", "found": False, "data": []}
                
                mascotas = []
                for row in rows:
                    mascotas.append({
                        "id": row[0],
                        "nombre": row[1],
                        "especie": row[2],
                        "raza": row[3] if row[3] else "No especificada",
                        "sexo": row[4],
                        "edad": row[5],
                        "peso": float(row[6]) if row[6] is not None else None,
                        "dueno": row[7],
                        "telefono_dueno": row[8]
                    })
                return {"status": "success", "found": True, "data": mascotas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def actualizar_estado_cita(appointment_id: int, nuevo_estado: str, motivo_cancelacion: str = None, veterinary_id: int = None) -> dict:
    query = """
        UPDATE appointments
        SET status = %s,
            cancellation_reason = %s,
            cancelled_at = CASE WHEN %s = 'Cancelada' THEN CURRENT_TIMESTAMP ELSE cancelled_at END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s AND (%s::integer IS NULL OR veterinary_id = %s);
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (nuevo_estado, motivo_cancelacion, nuevo_estado, appointment_id, veterinary_id, veterinary_id))
                conn.commit()
                if cur.rowcount == 0:
                    return {"status": "success", "updated": False, "message": "No se encontró la cita o no pertenece a esta clínica."}
                return {"status": "success", "updated": True, "message": f"Cita {appointment_id} actualizada a estado: {nuevo_estado}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def confirmar_o_rechazar_cita(appointment_id: int, accion: str, motivo: str = None, veterinary_id: int = None) -> dict:
    nuevo_estado = "Confirmada" if accion.lower() == "confirmar" else "Cancelada"
    return actualizar_estado_cita(appointment_id=appointment_id, nuevo_estado=nuevo_estado, motivo_cancelacion=motivo, veterinary_id=veterinary_id)

def buscar_dueno_mascota(pet_id: int = None, nombre_mascota: str = None, veterinary_id: int = None) -> dict:
    query = """
        SELECT DISTINCT
            u.id as dueno_id,
            u.name as dueno_nombre,
            u.phone_number as dueno_telefono,
            u.email as dueno_email,
            p.id as mascota_id,
            p.name as mascota_nombre,
            p.specie as mascota_especie,
            p.breed as mascota_raza
        FROM pets p
        JOIN users_app u ON p.user_id = u.id
        LEFT JOIN appointments a ON p.id = a.pet_id
        WHERE (%s::integer IS NULL OR p.id = %s)
          AND (%s IS NULL OR p.name ILIKE %s)
          AND (%s::integer IS NULL OR a.veterinary_id = %s);
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                name_param = f"%{nombre_mascota}%" if nombre_mascota else None
                cur.execute(query, (pet_id, pet_id, name_param, name_param, veterinary_id, veterinary_id))
                rows = cur.fetchall()
                if not rows:
                    return {"status": "success", "found": False, "data": []}
                
                owners = []
                for row in rows:
                    owners.append({
                        "dueno_id": row[0],
                        "dueno_nombre": row[1],
                        "dueno_telefono": row[2],
                        "dueno_email": row[3],
                        "mascota_id": row[4],
                        "mascota_nombre": row[5],
                        "mascota_especie": row[6],
                        "mascota_raza": row[7] if row[7] else "No especificada"
                    })
                return {"status": "success", "found": True, "data": owners}
    except Exception as e:
        return {"status": "error", "message": str(e)}


