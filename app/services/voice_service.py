import os
import tempfile
import logging
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Modelo de Whisper a usar
# - tiny/base/small/medium/large-v3
# - tiny es suficiente para comandos de voz (~500 MB RAM)
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "medium")

# Dispositivo:
# - auto: deja que CTranslate2 detecte (en Windows+AMD caerá a CPU)
# - cpu: fuerza CPU (funciona en cualquier hardware)
# - cuda: solo NVIDIA
# Para usar GPU AMD en Windows se requiere whisper.cpp + Vulkan (ver docs/VOICE_BENCHMARKS.md)
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "auto")

# Tipo de cómputo:
# - auto: deja que CTranslate2 elija según el dispositivo
# - float16: para GPU (menor precisión, más rápido)mm
# - int8: para CPU (cuantizado, menor RAM)
# - int8_float16: híbrido
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "auto")

# Instancia global del modelo (lazy loading)
_whisper_model = None
_whisper_available = None
_whisper_actual_device = None


def _get_whisper_model():
    """Carga el modelo de faster-whisper de forma lazy (solo cuando se necesita)."""
    global _whisper_model, _whisper_available, _whisper_actual_device
    
    if _whisper_available is False:
        return None
    
    if _whisper_model is not None:
        return _whisper_model
    
    try:
        from faster_whisper import WhisperModel
        device = WHISPER_DEVICE
        compute = WHISPER_COMPUTE_TYPE
        logger.info(f"Cargando modelo Whisper '{WHISPER_MODEL}' -> device={device}, compute_type={compute}...")
        _whisper_model = WhisperModel(
            WHISPER_MODEL,
            device=device,
            compute_type=compute
        )
        _whisper_available = True
        
        # Detectar en qué dispositivo real terminó corriendo
        _whisper_actual_device = _detectar_dispositivo_real(_whisper_model)
        logger.info(f"✔ Modelo Whisper '{WHISPER_MODEL}' cargado. Dispositivo real: {_whisper_actual_device}")
        return _whisper_model
    except ImportError:
        logger.warning("faster-whisper no está instalado. El endpoint de transcripción no estará disponible.")
        _whisper_available = False
        return None
    except Exception as e:
        logger.error(f"Error al cargar modelo Whisper: {e}")
        _whisper_available = False
        return None


def _detectar_dispositivo_real(model) -> str:
    """Detecta si el modelo se ejecuta en CPU o GPU consultando las propiedades internas de CTranslate2."""
    try:
        # faster-whisper expone el modelo interno de CTranslate2 en model.model
        ct2_model = getattr(model, 'model', None)
        if ct2_model is not None:
            device_str = str(ct2_model.device).lower()
            if 'cuda' in device_str:
                return f"cuda ({ct2_model.device})"
            elif 'cpu' in device_str:
                return f"cpu ({ct2_model.device})"
        # Si no podemos detectarlo, intentar inferir de la propiedad device_index
        device_index = getattr(model, 'device_index', None)
        return 'auto' if device_index is None else str(device_index)
    except Exception:
        return 'desconocido'


async def transcribir_audio(audio_file: UploadFile) -> JSONResponse:
    """
    Recibe un archivo de audio y lo transcribe usando faster-whisper local.
    
    Acepta formatos: wav, webm, mp3, ogg, m4a, flac.
    Retorna: {"text": "...", "language": "es", "confidence": 0.95}
    """
    model = _get_whisper_model()
    
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="El servicio de transcripción de voz no está disponible. faster-whisper no está instalado o falló al cargar."
        )
    
    # Validar tipo de archivo
    allowed_types = {
        "audio/wav", "audio/wave", "audio/x-wav",
        "audio/webm", "audio/ogg", "audio/mpeg", "audio/mp3",
        "audio/mp4", "audio/m4a", "audio/flac", "audio/x-m4a",
        "application/octet-stream"
    }
    
    content_type = (audio_file.content_type or "application/octet-stream").split(";")[0].strip()
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de audio no soportado: {content_type}. Use WAV, WebM, MP3, OGG, M4A o FLAC."
        )
    
    # Guardar archivo temporalmente
    suffix = _get_audio_suffix(content_type)
    tmp_path = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribir
        logger.info(f"Transcribiendo audio ({len(content)} bytes, {content_type})...")
        segments, info = model.transcribe(
            tmp_path,
            language=None,  # Auto-detectar idioma
            beam_size=5,
            vad_filter=True,  # Filtrar silencios
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=200
            )
        )
        
        # Concatenar segmentos
        texto_completo = " ".join(segment.text.strip() for segment in segments)
        texto_completo = texto_completo.strip()
        
        if not texto_completo:
            return JSONResponse(content={
                "text": "",
                "language": info.language,
                "engine": "whisper_local",
                "model": WHISPER_MODEL,
                "confidence": round(info.language_probability, 2),
                "warning": "No se detectó voz en el audio."
            })
        
        logger.info(f"Transcripción completada: '{texto_completo[:80]}...' ({info.language}, {info.language_probability:.2f})")
        
        return JSONResponse(content={
            "text": texto_completo,
            "language": info.language,
            "engine": "whisper_local",
            "model": WHISPER_MODEL,
            "confidence": round(info.language_probability, 2)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error durante la transcripción: {e}")
        raise HTTPException(status_code=500, detail=f"Error al transcribir el audio: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _get_audio_suffix(content_type: str) -> str:
    """Retorna la extensión de archivo apropiada según el content type."""
    mapping = {
        "audio/wav": ".wav",
        "audio/wave": ".wav",
        "audio/x-wav": ".wav",
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".m4a",
        "audio/m4a": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/flac": ".flac",
    }
    return mapping.get(content_type, ".wav")


def voice_status() -> dict:
    """
    Endpoint de diagnóstico para saber si Whisper está disponible, 
    qué motor se está usando y en qué dispositivo/cuantización real.
    """
    model = _get_whisper_model()
    return {
        "available": model is not None,
        "engine": "whisper_local" if model is not None else "web_speech_api",
        "model": WHISPER_MODEL if model is not None else None,
        "device_requested": WHISPER_DEVICE,
        "device_actual": _whisper_actual_device if model is not None else None,
        "compute_type_requested": WHISPER_COMPUTE_TYPE,
        "fallback_active": model is None,
        "gpu_note": "AMD RX 6600 no soportado por CTranslate2 en Windows. Usa whisper.cpp + Vulkan para GPU AMD en Windows. Ver docs/VOICE_BENCHMARKS.md."
    }
