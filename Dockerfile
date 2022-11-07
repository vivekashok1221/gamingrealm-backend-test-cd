FROM python:3.10-slim

ENV POETRY_VERSION=1.2.0 \
    PIP_NO_CACHE_DIR=1

WORKDIR /GR-backend/

RUN pip install -U poetry

COPY ./pyproject.toml ./poetry.lock* ./

RUN poetry install --no-root --without dev

RUN mkdir ./src/

COPY ./schema.prisma  ./

COPY ./src/prisma_partial_types.py ./src/

RUN poetry run prisma generate

COPY . .

ENTRYPOINT ["./scripts/entrypoint.sh"]
