# Benchmarks de Voz: Inviabilidad de Whisper + LLM en GPU Simultáneo

## Contexto del Sistema

| Componente | Especificación |
|---|---|
| **Sistema Operativo** | Windows (win32-x64) |
| **Node.js** | v24.13.0 |
| **Modelo LLM** | llama3.2:3b (Ollama) |
| **Embeddings** | nomic-embed-text (Ollama) |

## Problema: Colisión de VRAM

El modelo `llama3.2:3b` cargado en Ollama ocupa aproximadamente **2-3 GB de VRAM** cuando se ejecuta en GPU. Los modelos de Whisper tienen los siguientes requisitos de memoria:

| Modelo Whisper | VRAM Requerida | RAM (CPU) | Latencia (CPU) |
|---|---|---|---|
| `whisper-tiny` | ~1 GB | ~500 MB | ~2-4s (30s audio) |
| `whisper-base` | ~1.5 GB | ~800 MB | ~4-8s |
| `whisper-small` | ~2.5 GB | ~1.5 GB | ~10-15s |
| `whisper-medium` | ~5 GB | ~3 GB | ~25-40s |

### Resultado de la prueba de coexistencia

Cargar `whisper-medium` junto con `llama3.2:3b` en GPU simultáneamente requiere **~8 GB de VRAM** disponible. En hardware con ≤6 GB de VRAM (GPUs como RTX 3060, RTX 2060, GTX 1660), esto resulta en:

- **OOM (Out of Memory)** al intentar cargar el segundo modelo
- Colapso de Ollama al intentar liberar/reasignar memoria
- Degradación severa si se fuerza a CPU + GPU mixto

## Solución Implementada

### Track primario: Whisper Tiny en CPU (faster-whisper)

Se utiliza `faster-whisper` con el modelo `tiny` ejecutándose **exclusivamente en CPU** con cuantización `int8`:

```
Device: cpu
Compute type: int8
Model: tiny
RAM usage: ~500 MB
Latencia típica: 2-4 segundos para 30 segundos de audio
```

**Ventajas:**
- No compite por VRAM con el LLM
- Carga lazy (solo se inicializa al primer uso de transcripción)
- `int8` reduce uso de RAM a la mitad vs. float32
- VAD filter elimina silencios automáticamente

### Track de contingencia: Web Speech API

Si `faster-whisper` no está disponible (dependencia no instalada) o falla (hardware insuficiente), el frontend recurre automáticamente a la **Web Speech API** del navegador:

- Chrome/Chromium: `webkitSpeechRecognition`
- Edge: `SpeechRecognition`
- Configurado para español mexicano (`es-MX`)
- Latencia: ~1-2 segundos
- Requiere conexión a internet (procesamiento en servidores de Google)

## Variables de entorno configurables

| Variable | Default | Descripción |
|---|---|---|
| `WHISPER_MODEL` | `tiny` | Modelo de Whisper (tiny, base, small, medium, large-v3) |
| `WHISPER_DEVICE` | `auto` | Dispositivo: auto, cpu, cuda |
| `WHISPER_COMPUTE_TYPE` | `auto` | Tipo: auto, float16, int8, int8_float16 |

**IMPORTANTE para AMD en Windows:** `faster-whisper` usa CTranslate2 como backend, que en Windows solo soporta CUDA (NVIDIA). Para GPUs AMD (RX 6600, RX 6700, etc.) en Windows, CTranslate2 **no** puede usar la GPU y cae automáticamente a CPU. ROCm solo está disponible en Linux.

### Opciones para GPU AMD en Windows

| Opción | Velocidad | Complejidad |
|---|---|---|
| 1. `faster-whisper` con `device=cpu` + `compute_type=int8` (default actual) | ~2-4s | Baja — ya funciona |
| 2. `whisper.cpp` con backend Vulkan (usa la RX 6600 nativamente) | ~0.5-1s | Media — requiere compilar whisper.cpp con soporte Vulkan |
| 3. `faster-whisper` en WSL2 con ROCm | ~0.5-1s | Alta — requiere WSL2 + ROCm stack completo |
| 4. Subir modelo (ej. `small`) en CPU con `int8` | ~4-8s | Baja — más RAM pero mejor precisión |

**Para usar opción 2 (whisper.cpp + Vulkan),** se requiere crear un wrapper que reemplace `voice.py` para usar `whisper.cpp` en lugar de `faster-whisper`, invocando el binario compilado con `--gpu vulkan`. Ver la [guía de compilación de whisper.cpp con Vulkan](https://github.com/ggerganov/whisper.cpp?tab=readme-ov-file#vulkan-support).

**Estado actual:** `faster-whisper` no puede usar la RX 6600 en Windows. El sistema funciona correctamente en CPU con `int8` (tiny = ~500 MB RAM, ~2-4s por 30s de audio).

## Recomendaciones

1. **Producción con GPU limitada**: Mantener `tiny` en CPU. Es suficiente para comandos de voz cortos.
2. **Producción con GPU dedicada**: Usar una GPU separada para Whisper o desplegar en otro servidor.
3. **Sin GPU**: `tiny` en CPU con `int8` es viable en cualquier máquina con ≥4 GB de RAM.
4. **Máxima calidad**: Usar `medium` o `large-v3` en GPU dedicada con ≥8 GB VRAM.
