FROM python:3.10-slim

ENV POETRY_VERSION=1.2.0 \
    PIP_NO_CACHE_DIR=1

WORKDIR /GR-backend/

RUN pip install -U poetry

COPY ./pyproject.toml ./poetry.lock* ./

RUN poetry install --no-root --without dev

COPY ./schema.prisma .

RUN poetry run prisma generate

COPY . .

ENTRYPOINT ["poetry", "run", "uvicorn", "src.backend.app:app", "--host", "0.0.0.0"]
CMD ["--reload", "--reload-dir", "/GR-backend/src"]
