"""
Naukri Collector.

Uses the JSON endpoint naukri.com's own web frontend calls for job
search. No login required, but it's unofficial and undocumented -
the header values below (appid/systemid) are static identifiers
the public frontend sends, not credentials, but the endpoint's
shape can still change without notice.

Search keywords/locations are built fresh on every scan from the
union of onboarded users who enabled "naukri" as a source, plus
the config baseline (see app.collectors.search_scope) - so this
collector actually searches for what users asked for, not a frozen
YAML list.

Review Naukri's Terms of Service before relying on this at scale.
"""

from __future__ import annotations

import time
from urllib.parse import urlencode

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.collectors.search_scope import build_search_scope
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger

SOURCE_KEY = "naukri"

RESULTS_PER_PAGE = 20

REQUEST_DELAY_SECONDS = 1.0


class NaukriCollector(BaseCollector):

    BASE_URL = "https://www.naukri.com/jobapi/v3/search"

    HEADERS = {
        "appid": "109",
        "systemid": "Naukri",
        "Accept": "application/json",
    }

    def __init__(
        self,
        keywords: list[str],
        locations: list[str],
        max_pages: int = 2,
    ) -> None:

        self.client = HttpClient()

        self.baseline_keywords = keywords

        self.baseline_locations = locations

        self.max_pages = max_pages

    @property
    def name(self) -> str:
        return "Naukri"

    def collect(self) -> list[Job]:

        keywords, locations = build_search_scope(
            SOURCE_KEY,
            self.baseline_keywords,
            self.baseline_locations,
        )

        if not keywords:

            logger.warning(
                "Naukri: no search keywords available "
                "(empty baseline config and no onboarded users "
                "with naukri enabled). Skipping."
            )

            return []

        location_param = ",".join(locations)

        jobs: list[Job] = []

        for keyword in keywords:

            jobs.extend(self._search(keyword, location_param))

        logger.success(
            f"Collected {len(jobs)} jobs from Naukri."
        )

        return jobs

    def _search(self, keyword: str, location_param: str) -> list[Job]:

        results: list[Job] = []

        for page in range(1, self.max_pages + 1):

            params = {
                "noOfResults": RESULTS_PER_PAGE,
                "urlType": "search_by_keyword",
                "searchType": "adv",
                "keyword": keyword,
                "location": location_param,
                "pageNo": page,
            }

            url = f"{self.BASE_URL}?{urlencode(params)}"

            logger.info(
                f"Searching Naukri: '{keyword}' (page {page})"
            )

            try:
                data = self.client.get_json(url, headers=self.HEADERS)

            except Exception:

                logger.exception(
                    f"Naukri search failed: '{keyword}'"
                )

                break

            job_details = data.get("jobDetails", [])

            if not job_details:
                break

            results.extend(self._parse(job_details))

            time.sleep(REQUEST_DELAY_SECONDS)

        return results

    def _parse(self, job_details: list[dict]) -> list[Job]:

        jobs: list[Job] = []

        for item in job_details:

            title = item.get("title", "")

            # No title-based relevance filtering here - relevance
            # is decided per user by PreferenceMatcher, not by a
            # shared allowlist at collection time.

            url = item.get("jdURL") or item.get("staticUrl") or ""

            if url.startswith("/"):
                url = f"https://www.naukri.com{url}"

            try:

                jobs.append(

                    Job(

                        title=title,

                        company=item.get("companyName", "Unknown"),

                        location=self._placeholder(item, "location"),

                        experience=(
                            self._placeholder(item, "experience")
                            or "Unknown"
                        ),

                        source=JobSource.NAUKRI,

                        url=url,

                        employment_type=EmploymentType.UNKNOWN,
                    )
                )

            except Exception:

                logger.warning(
                    f"Skipped malformed Naukri listing: {title!r}"
                )

        return jobs

    @staticmethod
    def _placeholder(item: dict, key: str) -> str:

        for placeholder in item.get("placeholders", []):

            if placeholder.get("type") == key:
                return placeholder.get("label", "")

        return ""
