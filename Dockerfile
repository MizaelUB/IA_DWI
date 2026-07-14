# Fase 1: Builder para dependencias de Python
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Fase 2: Runner final
FROM python:3.11-slim
WORKDIR /app

# Copiar dependencias instaladas en el builder
COPY --from=builder /root/.local /root/.local
COPY . .

# Asegurar que el PATH incluya los scripts instalados por pip en .local
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
