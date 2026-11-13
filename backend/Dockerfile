# Dois alvos (specs/011-modo-de-uso/research.md, R-02):
# - dev: modo de desenvolvimento (compose.yaml), com as dependências de teste e o código montado;
# - uso: modo de uso (compose.uso.yaml), só as dependências de execução, código na imagem,
#   Gunicorn e usuário sem privilégios.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

EXPOSE 8000


FROM base AS dev

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

CMD ["sh", "scripts/start-dev.sh"]


FROM base AS uso

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --no-create-home --shell /usr/sbin/nologin grana

COPY . .

USER grana

CMD ["sh", "scripts/start-uso.sh"]
