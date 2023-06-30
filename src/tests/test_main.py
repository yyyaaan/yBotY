# Yan Pan
# python -m pytest -sv
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_base():
    response = client.get("/")
    assert response.status_code == 200
