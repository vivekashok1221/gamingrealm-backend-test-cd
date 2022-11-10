FROM python:3.10-slim

ENV POETRY_VERSION=1.2.0 \
    PIP_NO_CACHE_DIR=1 \
    http_proxy="http://edcguest:edcguest@172.31.102.29:3128/" \
    ftp_proxy="ftp://edcguest:edcguest@172.31.102.29:3128/" \
    rsync_proxy="rsync://edcguest:edcguest@172.31.102.29:3128/" \
    no_proxy="localhost,127.0.0.1,192.168.1.1,::1,*.local" \
    HTTP_PROXY="http://edcguest:edcguest@172.31.102.29:3128/" \
    FTP_PROXY="ftp://edcguest:edcguest@172.31.102.29:3128/" \
    RSYNC_PROXY="rsync://edcguest:edcguest@172.31.102.29:3128/" \
    NO_PROXY="localhost,127.0.0.1,192.168.1.1,::1,*.local" \
    https_proxy="http://edcguest:edcguest@172.31.102.29:3128/" \
    HTTPS_PROXY="http://edcguest:edcguest@172.31.102.29:3128/"


WORKDIR /GR-backend/

RUN pip install -U poetry

COPY ./pyproject.toml ./poetry.lock* ./

RUN poetry install --no-root --without dev

RUN mkdir ./prisma/

COPY prisma/schema.prisma  ./

COPY prisma/prisma_partial_types.py ./prisma/

RUN poetry run prisma generate

COPY . .

ENTRYPOINT ["./scripts/entrypoint.sh"]
