from fastapi.testclient import TestClient


def test_init_conversation(client: TestClient) -> None:
    response = client.post("/api/chat/", json={"message": "Eres una IA bien chida"})
    assert response.status_code == 200
