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

    def get(self, url: str) -> str:

        logger.info(f"GET {url}")

        response = self.client.get(url)

        response.raise_for_status()

        return response.text

    def get_json(self, url: str):

        logger.info(f"GET {url}")

        response = self.client.get(url)

        response.raise_for_status()

        return response.json()

    def close(self):

        self.client.close()