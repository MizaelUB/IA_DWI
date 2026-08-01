import os
import secrets
import time
import datetime
import jwt
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address

security_scheme = HTTPBearer(auto_error=False)

SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or secrets.token_urlsafe(64)
ALGORITHM = "HS256"

BLACKLISTED_TOKENS = set()

# ── IP Blocklist para penalización de 10 minutos ──
blocked_ips: dict[str, float] = {}  # {ip: timestamp_when_unblocked}

def is_ip_blocked(ip: str) -> bool:
    """Retorna True si la IP está bloqueada por exceso de requests."""
    if ip in blocked_ips:
        if time.time() < blocked_ips[ip]:
            return True
        del blocked_ips[ip]
    return False

def block_ip(ip: str, seconds: int = 600):
    """Bloquea una IP por N segundos (default 10 minutos)."""
    blocked_ips[ip] = time.time() + seconds

def get_real_ip(request: Request) -> str:
    """
    Obtiene la IP real del cliente de forma segura.
    Trata de evitar IP spoofing tomando el último valor de X-Forwarded-For,
    y recae en get_remote_address de slowapi.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ips = [i.strip() for i in forwarded.split(",") if i.strip()]
        if ips:
            return ips[-1]
    return get_remote_address(request)

# Instancia global del limitador
limiter = Limiter(key_func=get_real_ip)


def create_access_token(veterinary_id: int, user_id: int, username: str) -> str:
    """
    Crea un token JWT para un usuario normal (expira en 24h).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": username,
        "veterinary_id": veterinary_id,
        "user_id": user_id,
        "role": "admin",
        "permissions": ["read", "write", "delete"],
        "type": "auth_token",
        "iat": now,
        "exp": now + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> dict:
    """
    Dependencia de FastAPI para proteger rutas del dashboard.
    Extrae y verifica el JWT del header Authorization, permitiendo solo usuarios normales.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token de autenticación no proporcionado")
        
    if credentials.credentials in BLACKLISTED_TOKENS:
        raise HTTPException(status_code=401, detail="Token revocado")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != "auth_token":
            raise HTTPException(status_code=401, detail="Tipo de token inválido")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

