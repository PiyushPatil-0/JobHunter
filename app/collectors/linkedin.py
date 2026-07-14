"""
LinkedIn Collector.

Uses LinkedIn's public "guest" job search endpoint - the same one
LinkedIn's own unauthenticated job search pages call. No login, no
session, no anti-bot bypass. This is unofficial and undocumented,
so it can change or start rejecting requests without notice; treat
it as best-effort, not a stable integration.

Search keywords/locations are built fresh on every scan from the
union of onboarded users who enabled "linkedin" as a source.

Review LinkedIn's Terms of Service before relying on this at scale.
"""

from __future__ import annotations

import time
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.collectors.search_scope import build_search_scope
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger

SOURCE_KEY = "linkedin"

RESULTS_PER_PAGE = 25

REQUEST_DELAY_SECONDS = 1.0


class LinkedInCollector(BaseCollector):

    BASE_URL = (
        "https://www.linkedin.com/jobs-guest/jobs/api/"
        "seeMoreJobPostings/search"
    )

    def __init__(
        self,
        max_pages: int = 2,
    ) -> None:

        self.client = HttpClient()
        self.max_pages = max_pages

    @property
    def name(self) -> str:
        return "LinkedIn"

    def collect(self) -> list[Job]:

        keywords, locations = build_search_scope(SOURCE_KEY)

        if not keywords:

            logger.warning(
                "LinkedIn: no search keywords available "
                "(no onboarded users with linkedin enabled). Skipping."
            )

            return []

        locations = locations or [""]

        jobs: list[Job] = []

        for keyword in keywords:

            for location in locations:

                jobs.extend(self._search(keyword, location))

        logger.success(
            f"Collected {len(jobs)} jobs from LinkedIn."
        )

        return jobs

    def _search(self, keyword: str, location: str) -> list[Job]:

        results: list[Job] = []

        for page in range(self.max_pages):

            start = page * RESULTS_PER_PAGE

            params = {
                "keywords": keyword,
                "location": location,
                "start": start,
            }

            url = f"{self.BASE_URL}?{urlencode(params)}"

            logger.info(
                f"Searching LinkedIn: '{keyword}' in '{location}' "
                f"(page {page + 1})"
            )

            try:
                html = self.client.get(url)

            except Exception:

                logger.exception(
                    f"LinkedIn search failed: '{keyword}' in '{location}'"
                )

                break

            page_jobs = self._parse(html)

            if not page_jobs:
                # No more results, or LinkedIn changed its markup -
                # either way there's nothing further to paginate.
                break

            results.extend(page_jobs)

            time.sleep(REQUEST_DELAY_SECONDS)

        return results

    def _parse(self, html: str) -> list[Job]:

        soup = BeautifulSoup(html, "html.parser")

        jobs: list[Job] = []

        for card in soup.select("li"):

            title_el = card.select_one(".base-search-card__title")
            company_el = card.select_one(".base-search-card__subtitle")
            location_el = card.select_one(".job-search-card__location")
            link_el = card.select_one("a.base-card__full-link")

            if not (title_el and company_el and link_el):
                continue

            title = title_el.get_text(strip=True)

            # No title-based relevance filtering here - relevance
            # is decided per user by PreferenceMatcher, not by a
            # shared allowlist at collection time.

            try:

                jobs.append(

                    Job(

                        title=title,

                        company=company_el.get_text(strip=True),

                        location=(
                            location_el.get_text(strip=True)
                            if location_el
                            else ""
                        ),

                        experience="Unknown",

                        source=JobSource.LINKEDIN,

                        url=link_el.get("href", "").split("?")[0],

                        employment_type=EmploymentType.UNKNOWN,
                    )
                )

            except Exception:

                logger.warning(
                    f"Skipped malformed LinkedIn card: {title!r}"
                )

        return jobs
