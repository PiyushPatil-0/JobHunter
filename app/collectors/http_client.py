"""
Shared HTTP client for all collectors.
"""

from __future__ import annotations

import httpx

from app.utils.logger import logger


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

    def get(
        self,
        url: str,
        headers: dict | None = None,
    ) -> str:

        logger.info(f"GET {url}")

        response = self.client.get(url, headers=headers)

        response.raise_for_status()

        return response.text

    def get_json(
        self,
        url: str,
        headers: dict | None = None,
    ):

        logger.info(f"GET {url}")

        response = self.client.get(url, headers=headers)

        response.raise_for_status()

        return response.json()

    def post_json(
        self,
        url: str,
        json: dict,
        headers: dict | None = None,
    ):

        logger.info(f"POST {url}")

        response = self.client.post(url, json=json, headers=headers)

        response.raise_for_status()

        return response.json()

    def close(self):

        self.client.close()
