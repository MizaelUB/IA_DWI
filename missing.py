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

@router.post("/api/auth/guest")
