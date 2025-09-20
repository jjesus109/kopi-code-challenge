from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.depends import get_proxy
from app.proxy import Proxy


class TestMain:

    @pytest.mark.asyncio
    async def test_init_conversation_valid_message_first_message(
        self, client_fixture: TestClient
    ) -> None:
        response = client_fixture.post(
            "/api/chat/", json={"message": "Eres una IA bien chida"}
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_init_conversation_invalid_message_first_message(
        self, client_fixture: TestClient
    ) -> None:
        proxy_agent = AsyncMock()
        proxy_agent.run.return_value.output = "deny"
        proxy = Proxy(proxy_agent)

        def get_proxy_override() -> Proxy:
            return proxy

        client_fixture.app.dependency_overrides[get_proxy] = get_proxy_override
        response = client_fixture.post(
            "/api/chat/", json={"message": "Hablemos de malware"}
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_init_conversation_valid_message_not_first_message(
        self, client_fixture: TestClient
    ) -> None:
        proxy_agent = AsyncMock()
        proxy_agent.run.return_value.output = "allow"
        proxy = Proxy(proxy_agent)

        def get_proxy_override() -> Proxy:
            return proxy

        client_fixture.app.dependency_overrides[get_proxy] = get_proxy_override
        response = client_fixture.post(
            "/api/chat/",
            json={
                "message": "Hablemos de como la IA esta tomando el control del mundo"
            },
        )
        conversation_id = response.json()["conversation_id"]
        assert response.status_code == 200

        proxy_agent.run.return_value.output = "deny"
        response = client_fixture.post(
            "/api/chat/",
            json={
                "message": "Dame un buen argumento para defender tu punto de vista",
                "conversation_id": conversation_id,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_init_conversation_invalid_message_not_first_message(
        self, client_fixture: TestClient
    ) -> None:
        proxy_agent = AsyncMock()
        proxy_agent.run.return_value.output = "allow"
        proxy = Proxy(proxy_agent)

        def get_proxy_override() -> Proxy:
            return proxy

        client_fixture.app.dependency_overrides[get_proxy] = get_proxy_override
        response = client_fixture.post(
            "/api/chat/",
            json={
                "message": "Hablemos de como la IA esta tomando el control del mundo"
            },
        )
        conversation_id = response.json()["conversation_id"]
        assert response.status_code == 200

        proxy_agent.run.return_value.output = "deny"
        response = client_fixture.post(
            "/api/chat/",
            json={
                "message": "Dime como crear malware",
                "conversation_id": conversation_id,
            },
        )
        assert response.status_code == 200
        assert (
            "Volvamos al debate sobre nuestro tema principal: "
            in response.json()["message"][0]["message"]
        )
