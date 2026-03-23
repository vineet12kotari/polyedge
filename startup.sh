#!/bin/bash
# Generate historical data if not present, then start server
python generate_history.py
uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8000}