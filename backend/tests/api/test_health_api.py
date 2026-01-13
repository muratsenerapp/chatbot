"""API endpoint tests for health check route."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestHealthCheck:
    """Tests for the /api/health endpoint."""

    def test_health_returns_ok_when_ollama_available(self):
        """Test health endpoint returns 'ok' status when Ollama is reachable."""
        with patch(
            "app.api.health.check_ollama_connection", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = True
            client = TestClient(app)
            response = client.get("/api/health")

            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "ok"
            assert body["service"] == "chatbot-backend"
            assert body["dependencies"]["ollama"] == "ok"

    def test_health_returns_degraded_when_ollama_unavailable(self):
        """Test health endpoint returns 'degraded' status when Ollama is down."""
        with patch(
            "app.api.health.check_ollama_connection", new_callable=AsyncMock
        ) as mock_check:
            mock_check.return_value = False
            client = TestClient(app)
            response = client.get("/api/health")

            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "degraded"
            assert body["service"] == "chatbot-backend"
            assert body["dependencies"]["ollama"] == "unavailable"


class TestCheckOllamaConnection:
    """Tests for the check_ollama_connection helper function."""

    @pytest.mark.asyncio
    async def test_returns_true_when_ollama_responds_200(self):
        """Test returns True when Ollama API responds with 200."""
        from app.api.health import check_ollama_connection

        with patch("app.api.health.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await check_ollama_connection("http://localhost:11434")

            assert result is True
            mock_client.get.assert_called_once_with("http://localhost:11434")

    @pytest.mark.asyncio
    async def test_returns_false_when_ollama_responds_non_200(self):
        """Test returns False when Ollama API responds with non-200 status."""
        from app.api.health import check_ollama_connection

        with patch("app.api.health.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await check_ollama_connection("http://localhost:11434")

            assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_connection_error(self):
        """Test returns False when connection to Ollama fails."""
        from app.api.health import check_ollama_connection

        with patch("app.api.health.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await check_ollama_connection("http://localhost:11434")

            assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_timeout(self):
        """Test returns False when Ollama request times out."""
        from app.api.health import check_ollama_connection

        with patch("app.api.health.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await check_ollama_connection("http://localhost:11434")

            assert result is False
