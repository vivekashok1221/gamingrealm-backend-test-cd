#!/bin/bash

poetry run uvicorn src.backend.app:app --reload --reload-dir ./src
