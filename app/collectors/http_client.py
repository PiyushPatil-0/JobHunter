"""
Shared HTTP client for all collectors.
"""

from __future__ import annotations

import time

import httpx

from app.utils.logger import logger

# Retried automatically - transient, likely to succeed on a second
# attempt: DNS hiccups, connection resets, timeouts, and the
# httpx.ConnectError family in general (this is what covers the
# "getaddrinfo failed" case - a momentary DNS resolution failure).
RETRYABLE_EXCEPTIONS = (httpx.TransportError,)

# Retried automatically - transient server-side conditions.
# Deliberately excludes other 4xx codes (404, 401, 403, ...): those
# mean the request itself is wrong (bad company slug, bad
# credentials) and will fail identically no matter how many times
# it's retried.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

MAX_RETRIES = 2

RETRY_DELAY_SECONDS = 2.0


class HttpClient:

    def __init__(self) -> None:

        self.client = httpx.Client(

            timeout=30,

            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/138.0 Safari/537.36"
                )
            },
        )

    def _send_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """
        Sends one request, retrying up to MAX_RETRIES times on
        transient failures (network-level errors, or a 429/5xx
        response) with a short delay between attempts. Non-transient
        errors (404, 401, malformed JSON, etc.) are raised
        immediately - retrying those would just fail the same way
        every time.
        """

        last_exception: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 2):  # e.g. 1 try + 2 retries = 3 attempts

            try:

                response = self.client.request(method, url, **kwargs)

                response.raise_for_status()

                return response

            except httpx.HTTPStatusError as exc:

                if exc.response.status_code not in RETRYABLE_STATUS_CODES:
                    raise

                last_exception = exc

            except RETRYABLE_EXCEPTIONS as exc:

                last_exception = exc

            if attempt <= MAX_RETRIES:
                logger.warning(
                    f"{method} {url} failed "
                    f"(attempt {attempt}/{MAX_RETRIES + 1}): "
                    f"{last_exception!r}. Retrying in "
                    f"{RETRY_DELAY_SECONDS}s..."
                )
                time.sleep(RETRY_DELAY_SECONDS)

        # All attempts exhausted - surface the last failure so the
        # caller's existing try/except (e.g. GreenhouseCollector
        # logging "Failed: {company}" and moving on to the next one)
        # behaves exactly as it did before this retry logic existed.
        raise last_exception

    def get(
        self,
        url: str,
        headers: dict | None = None,
    ) -> str:

        logger.info(f"GET {url}")

        response = self._send_with_retry("GET", url, headers=headers)

        return response.text

    def get_json(
        self,
        url: str,
        headers: dict | None = None,
    ):

        logger.info(f"GET {url}")

        response = self._send_with_retry("GET", url, headers=headers)

        return response.json()

    def post_json(
        self,
        url: str,
        json: dict,
        headers: dict | None = None,
    ):

        logger.info(f"POST {url}")

        response = self._send_with_retry("POST", url, json=json, headers=headers)

        return response.json()

    def close(self):

        self.client.close()
