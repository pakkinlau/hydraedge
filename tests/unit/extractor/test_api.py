from fastapi.testclient import TestClient
from src.serve.app import app

client = TestClient(app)

def test_ping():
    assert client.get("/ping").json() == {"pong": True}
