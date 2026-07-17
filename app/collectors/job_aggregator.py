"""
Generic job-aggregator collector.

Plugs into whichever job-aggregator API you've registered for -
Adzuna, Careerjet, or Jooble - selected via
config.sources.aggregator.provider. Unlike LinkedIn/Naukri (whose own
terms explicitly prohibit this kind of automated redistribution) or
Darwinbox/Wellfound (both behind active bot detection with no public
API meant for this), these three are built and documented specifically
for third parties to pull job data into their own apps.

Credentials come from environment variables, never settings.yaml -
same category as TELEGRAM_BOT_TOKEN:

    AGGREGATOR_API_KEY     - required by all three providers
                              (Adzuna: app_id, Careerjet: affiliate
                              ID, Jooble: API key)
    AGGREGATOR_API_SECRET  - only used by Adzuna (app_key). Leave
                              unset for Careerjet/Jooble.

Search keywords/locations are built fresh every scan from the union
of onboarded users who enabled "aggregator" as a source, the same
pattern LinkedIn/Naukri use (app.collectors.search_scope).

IMPORTANT - verify before enabling in production:
- Field names below (title/company/location/url/description/date per
  provider) are based on each provider's published documentation as
  of when this was written, not a live-tested response - APIs like
  this can add/rename/remove fields without notice. Log a raw
  response once against your real credentials and confirm the shapes
  still match before trusting this at scale.
- Adzuna's terms require a visible "Jobs by Adzuna" credit wherever
  their listings are displayed (min. size, hyperlinked) - handled
  here via Job.attribution_text/attribution_url, rendered by
  app.notifications.message_builder. Careerjet/Jooble's exact
  requirements weren't independently confirmed - re-check whichever
  provider you pick against their current terms before relying on
  this, since I was not able to verify their equivalent obligations
  as thoroughly as Adzuna's.
- The 14-day-trial-for-ongoing-individual-use clause found in
  Adzuna's terms was not resolved here - if you choose Adzuna, get
  written confirmation from them that a personal, non-commercial
  project qualifies for ongoing free-tier use before relying on it
  long-term.
"""

from __future__ import annotations

import time

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.collectors.search_scope import build_search_scope
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger

SOURCE_KEY = "aggregator"

RESULTS_PER_PAGE = 20

MAX_PAGES = 2

REQUEST_DELAY_SECONDS = 1.0

ADZUNA_ATTRIBUTION_TEXT = "Jobs by Adzuna"
ADZUNA_ATTRIBUTION_URL = "https://www.adzuna.in"


class JobAggregatorCollector(BaseCollector):

    def __init__(
        self,
        provider: str,
        api_key: str,
        api_secret: str = "",
        country: str = "in",
    ) -> None:

        self.client = HttpClient()

        self.provider = provider.strip().lower()

        self.api_key = api_key

        self.api_secret = api_secret

        self.country = country

        if self.provider not in {"adzuna", "careerjet", "jooble"}:
            raise ValueError(
                f"Unknown aggregator provider: {provider!r}. "
                "Expected 'adzuna', 'careerjet', or 'jooble'."
            )

    @property
    def name(self) -> str:
        return f"Aggregator ({self.provider})"

    def collect(self) -> list[Job]:

        if not self.api_key:
            logger.warning(
                f"Aggregator ({self.provider}): no API key configured "
                "(set AGGREGATOR_API_KEY). Skipping."
            )
            return []

        keywords, locations = build_search_scope(SOURCE_KEY)

        if not keywords:
            logger.warning(
                "Aggregator: no search keywords available "
                "(no onboarded users with aggregator enabled). Skipping."
            )
            return []

        locations = locations or [""]

        search_fn = {
            "adzuna": self._search_adzuna,
            "careerjet": self._search_careerjet,
            "jooble": self._search_jooble,
        }[self.provider]

        jobs: list[Job] = []

        for keyword in keywords:
            for location in locations:
                jobs.extend(search_fn(keyword, location))

        logger.success(
            f"Collected {len(jobs)} jobs from Aggregator ({self.provider})."
        )

        return jobs

    # ---------- Adzuna ----------
    #
    # GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
    #     ?app_id=...&app_key=...&what=...&where=...&results_per_page=...
    #
    # Response shape (per developer.adzuna.com):
    # {"results": [{"title", "company": {"display_name"},
    #               "location": {"display_name"}, "redirect_url",
    #               "description", "created"}], "count": N}

    def _search_adzuna(self, keyword: str, location: str) -> list[Job]:

        results: list[Job] = []

        for page in range(1, MAX_PAGES + 1):

            url = (
                f"https://api.adzuna.com/v1/api/jobs/"
                f"{self.country}/search/{page}"
            )

            params = {
                "app_id": self.api_key,
                "app_key": self.api_secret,
                "what": keyword,
                "results_per_page": RESULTS_PER_PAGE,
                "content-type": "application/json",
            }

            if location:
                params["where"] = location

            try:
                data = self.client.get_json(
                    self._with_query(url, params)
                )
            except Exception:
                logger.exception(
                    f"Adzuna search failed: '{keyword}' in '{location}'"
                )
                break

            items = data.get("results", [])

            if not items:
                break

            for item in items:

                title = item.get("title", "")

                try:
                    results.append(
                        Job(
                            title=title,
                            company=(
                                item.get("company", {}).get(
                                    "display_name", "Unknown"
                                )
                            ),
                            location=(
                                item.get("location", {}).get(
                                    "display_name", ""
                                )
                            ),
                            experience="Unknown",
                            source=JobSource.ADZUNA,
                            url=item.get("redirect_url", ""),
                            description=item.get("description", ""),
                            employment_type=EmploymentType.UNKNOWN,
                            attribution_text=ADZUNA_ATTRIBUTION_TEXT,
                            attribution_url=ADZUNA_ATTRIBUTION_URL,
                        )
                    )
                except Exception:
                    logger.warning(
                        f"Skipped malformed Adzuna listing: {title!r}"
                    )

            time.sleep(REQUEST_DELAY_SECONDS)

        return results

    # ---------- Careerjet ----------
    #
    # GET https://search.api.careerjet.net/v4/query
    #     ?keywords=...&location=...&affid=...&page=...&locale_code=en_IN
    #
    # Response shape (per careerjet's official Python client /
    # public docs):
    # {"type": "JOBS", "hits": N, "jobs": [{"title", "company",
    #  "locations", "url", "description", "date"}]}

    def _search_careerjet(self, keyword: str, location: str) -> list[Job]:

        results: list[Job] = []

        locale_code = f"en_{self.country.upper()}"

        for page in range(1, MAX_PAGES + 1):

            params = {
                "keywords": keyword,
                "location": location,
                "affid": self.api_key,
                "page": page,
                "locale_code": locale_code,
                "pagesize": RESULTS_PER_PAGE,
            }

            url = self._with_query(
                "https://search.api.careerjet.net/v4/query", params
            )

            try:
                data = self.client.get_json(url)
            except Exception:
                logger.exception(
                    f"Careerjet search failed: '{keyword}' in '{location}'"
                )
                break

            if data.get("type") != "JOBS":
                # "LOCATIONS" (ambiguous location, no search run) or
                # any other non-JOBS type - nothing to paginate.
                break

            items = data.get("jobs", [])

            if not items:
                break

            for item in items:

                title = item.get("title", "")

                try:
                    results.append(
                        Job(
                            title=title,
                            company=item.get("company", "Unknown"),
                            location=item.get("locations", ""),
                            experience="Unknown",
                            source=JobSource.CAREERJET,
                            url=item.get("url", ""),
                            description=item.get("description", ""),
                            employment_type=EmploymentType.UNKNOWN,
                        )
                    )
                except Exception:
                    logger.warning(
                        f"Skipped malformed Careerjet listing: {title!r}"
                    )

            time.sleep(REQUEST_DELAY_SECONDS)

        return results

    # ---------- Jooble ----------
    #
    # POST https://jooble.org/api/{api_key}
    #     body: {"keywords": ..., "location": ..., "page": ...}
    #
    # Response shape (per Jooble's REST API docs):
    # {"jobs": [{"title", "location", "company", "link", "snippet",
    #            "updated"}], "totalCount": N}

    def _search_jooble(self, keyword: str, location: str) -> list[Job]:

        results: list[Job] = []

        url = f"https://jooble.org/api/{self.api_key}"

        for page in range(1, MAX_PAGES + 1):

            payload = {
                "keywords": keyword,
                "location": location,
                "page": page,
                "ResultOnPage": RESULTS_PER_PAGE,
            }

            try:
                data = self.client.post_json(url, json=payload)
            except Exception:
                logger.exception(
                    f"Jooble search failed: '{keyword}' in '{location}'"
                )
                break

            items = data.get("jobs", [])

            if not items:
                break

            for item in items:

                title = item.get("title", "")

                try:
                    results.append(
                        Job(
                            title=title,
                            company=item.get("company", "Unknown"),
                            location=item.get("location", ""),
                            experience="Unknown",
                            source=JobSource.JOOBLE,
                            url=item.get("link", ""),
                            description=item.get("snippet", ""),
                            employment_type=EmploymentType.UNKNOWN,
                        )
                    )
                except Exception:
                    logger.warning(
                        f"Skipped malformed Jooble listing: {title!r}"
                    )

            time.sleep(REQUEST_DELAY_SECONDS)

        return results

    @staticmethod
    def _with_query(url: str, params: dict) -> str:
        from urllib.parse import urlencode

        query = urlencode({k: v for k, v in params.items() if v not in (None, "")})

        return f"{url}?{query}" if query else url
