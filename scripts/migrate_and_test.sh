#!/bin/bash
docker run --name test-gr-postgres -e POSTGRES_PASSWORD=adminpw -e POSTGRES_USER=admin -e POSTGRES_DB=gamginrealmdb --network=host --rm -d postgres:latest
poetry run prisma db push
poetry run pytest
docker stop test-gr-postgres
