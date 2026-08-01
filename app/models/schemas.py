from pydantic import BaseModel, field_validator
from typing import List
import re


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
    conversation_id: str | None = None
    user_id: int | None = None
    is_follow_up: bool = False


class RegisterUserRequest(BaseModel):
    model_config = {"extra": "forbid"}
    # Datos personales
    username: str = ""
    password: str
    email: str
    full_name: str
    phone: str

    # Cédula del médico (validada pero NO almacenada)
    doctor_license: str

    # Datos de veterinaria
    vet_name: str
    vet_city: str
    vet_address: str = ""
    vet_phone: str = ""
    vet_email: str = ""

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if v and not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError("El usuario debe tener 3-30 caracteres (letras, números, guión bajo).")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("El correo electrónico no es válido.")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError("El nombre completo debe tener 2-100 caracteres.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not re.match(r"^\d{10}$", cleaned):
            raise ValueError("El teléfono debe tener 10 dígitos.")
        return cleaned

    @field_validator("doctor_license")
    @classmethod
    def validate_doctor_license(cls, v):
        if not re.match(r"^[a-zA-Z0-9]{6,20}$", v):
            raise ValueError("La cédula del médico debe tener 6-20 caracteres alfanuméricos.")
        return v

    @field_validator("vet_name")
    @classmethod
    def validate_vet_name(cls, v):
        if len(v) < 2 or len(v) > 100:
            raise ValueError("El nombre de la veterinaria debe tener 2-100 caracteres.")
        return v

    @field_validator("vet_city")
    @classmethod
    def validate_vet_city(cls, v):
        if len(v) < 2 or len(v) > 50:
            raise ValueError("La ciudad debe tener 2-50 caracteres.")
        return v


class RequestCodeRequest(BaseModel):
    email: str
    purpose: str = "registro"  # 'registro' o 'recuperacion'
    captcha_id: str | None = None
    captcha_answer: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", v):
            raise ValueError("El correo electrónico no es válido.")
        return v


class VerifyCodeRequest(BaseModel):
    email: str
    code: str
    purpose: str = "registro"

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not re.match(r"^\d{6}$", v):
            raise ValueError("El código de verificación debe tener 6 dígitos numéricos.")
        return v


class ResetPasswordWithCodeRequest(BaseModel):
    email: str
    code: str
    new_password: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not re.match(r"^\d{6}$", v):
            raise ValueError("El código de verificación debe tener 6 dígitos numéricos.")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula.")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una minúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        return v

