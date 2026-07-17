"""
Tests for HttpClient's automatic retry on transient failures -
covers the exact scenario that prompted this: a momentary DNS
resolution failure (httpx.ConnectError / "getaddrinfo failed") on one
request shouldn't cost a collector its entire result for that scan
cycle if a retry a couple seconds later would have succeeded.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import httpx
import pytest

from app.collectors.http_client import HttpClient
from app.collectors.http_client import MAX_RETRIES


def _response(status_code: int, json_body: dict | None = None) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com")
    return httpx.Response(
        status_code=status_code,
        json=json_body or {},
        request=request,
    )


class TestRetryOnTransientNetworkErrors:
    def test_connect_error_then_success_returns_result(self) -> None:
        """
        Mirrors the reported case exactly: first attempt raises
        httpx.ConnectError (DNS failure), second attempt succeeds.
        """
        client = HttpClient()

        with patch.object(
            client.client,
            "request",
            side_effect=[
                httpx.ConnectError("getaddrinfo failed"),
                _response(200, {"jobs": []}),
            ],
        ), patch("app.collectors.http_client.time.sleep") as mock_sleep:
            result = client.get_json("https://example.com/jobs")

        assert result == {"jobs": []}
        mock_sleep.assert_called_once()

    def test_all_attempts_failing_raises_the_last_exception(self) -> None:
        client = HttpClient()

        with patch.object(
            client.client,
            "request",
            side_effect=httpx.ConnectError("getaddrinfo failed"),
        ) as mock_request, patch("app.collectors.http_client.time.sleep"):
            with pytest.raises(httpx.ConnectError):
                client.get_json("https://example.com/jobs")

        # 1 initial attempt + MAX_RETRIES retries
        assert mock_request.call_count == MAX_RETRIES + 1

    def test_timeout_is_also_retried(self) -> None:
        client = HttpClient()

        with patch.object(
            client.client,
            "request",
            side_effect=[
                httpx.ReadTimeout("timed out"),
                _response(200, {"jobs": []}),
            ],
        ), patch("app.collectors.http_client.time.sleep"):
            result = client.get_json("https://example.com/jobs")

        assert result == {"jobs": []}


class TestRetryOnStatusCodes:
    def test_429_is_retried_then_succeeds(self) -> None:
        client = HttpClient()

        with patch.object(
            client.client,
            "request",
            side_effect=[_response(429), _response(200, {"jobs": []})],
        ), patch("app.collectors.http_client.time.sleep") as mock_sleep:
            result = client.get_json("https://example.com/jobs")

        assert result == {"jobs": []}
        mock_sleep.assert_called_once()

    def test_500_is_retried(self) -> None:
        client = HttpClient()

        with patch.object(
            client.client,
            "request",
            side_effect=[_response(500), _response(200, {"jobs": []})],
        ), patch("app.collectors.http_client.time.sleep"):
            result = client.get_json("https://example.com/jobs")

        assert result == {"jobs": []}

    def test_404_is_not_retried(self) -> None:
        """
        A bad company slug returns 404 every time - retrying wastes
        time and delays the scan for no benefit. Should raise
        immediately, on the first attempt.
        """
        client = HttpClient()

        with patch.object(
            client.client,
            "request",
            return_value=_response(404),
        ) as mock_request, patch("app.collectors.http_client.time.sleep") as mock_sleep:
            with pytest.raises(httpx.HTTPStatusError):
                client.get_json("https://example.com/jobs")

        assert mock_request.call_count == 1
        mock_sleep.assert_not_called()

    def test_401_is_not_retried(self) -> None:
        client = HttpClient()

        with patch.object(
            client.client, "request", return_value=_response(401)
        ) as mock_request, patch("app.collectors.http_client.time.sleep"):
            with pytest.raises(httpx.HTTPStatusError):
                client.get_json("https://example.com/jobs")

        assert mock_request.call_count == 1


class TestNoRetryNeeded:
    def test_success_on_first_attempt_does_not_sleep(self) -> None:
        client = HttpClient()

        with patch.object(
            client.client, "request", return_value=_response(200, {"jobs": [1, 2]})
        ), patch("app.collectors.http_client.time.sleep") as mock_sleep:
            result = client.get_json("https://example.com/jobs")

        assert result == {"jobs": [1, 2]}
        mock_sleep.assert_not_called()

    def test_post_json_also_retries(self) -> None:
        client = HttpClient()

        with patch.object(
            client.client,
            "request",
            side_effect=[
                httpx.ConnectError("getaddrinfo failed"),
                _response(200, {"jobs": []}),
            ],
        ), patch("app.collectors.http_client.time.sleep"):
            result = client.post_json(
                "https://example.com/jobs", json={"keywords": "python"}
            )

        assert result == {"jobs": []}
