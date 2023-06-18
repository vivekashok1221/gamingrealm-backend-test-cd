#!/bin/bash
docker run --name test-gr-postgres -e POSTGRES_PASSWORD=adminpw -e POSTGRES_USER=admin -e POSTGRES_DB=gamingrealmdb --network=host --rm -d postgres:15 && \
poetry run prisma db push && \
poetry run pytest
docker stop test-gr-postgres
