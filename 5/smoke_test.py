"""Lightweight local smoke test; requires project dependencies installed."""
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
print("GET /", client.get("/").status_code)
print("GET /health", client.get("/health").json())
print("OpenAPI", client.get("/openapi.json").status_code)
