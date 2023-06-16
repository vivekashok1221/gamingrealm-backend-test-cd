# GamingRealm Backend
[![API Testing](https://github.com/idkbrowby/gamingrealm-backend/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/idkbrowby/gamingrealm-backend/actions/workflows/integration-tests.yml)
## Architecture
TODO: fill this in

## Developing
This project uses the [Poetry](https://python-poetry.org) package manager.
After installing poetry, run
```bash
poetry install
```
in this directory to install all dependencies. Then, run
```bash
poetry run pre-commit install
```
to install the git pre-commit hooks. To manually trigger linting, run `poetry run task lint`.

The following steps will differ depending on whether you have PostgreSQL installed locally.
### Local PostgreSQL
1) Set the `GR_DATABASE_URL` environment variable (or make a file called `.env` in this directory and make it);
set it to your database connection URL.
2) Run
```bash
poetry run prisma generate
poetry run prisma migrate dev
```

### You don't have PostgreSQL installed
Just use our Docker container for development
```bash
docker compose up
```

## Running the server
Run
```bash
poetry run task runserver
```

## Running tests
Run
```bash
poetry run task test
```

## Database Structure
[ER Diagram](https://dbdiagram.io/embed/635aaaa96848d85eee878aea)
