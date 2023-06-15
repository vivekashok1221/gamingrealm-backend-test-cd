#!/bin/bash
poetry run prisma db push
poetry run pytest
