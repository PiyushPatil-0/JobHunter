"""
Workday Collector.

Unlike Greenhouse/Lever/Ashby/SmartRecruiters, Workday has no
single public API host or company-slug pattern - every company's
career site runs on its own tenant subdomain (e.g.
"acme.wd5.myworkdayjobs.com") with its own "site" name configured
by that company. There's nothing to guess from a company name
alone, so each tenant needs host/tenant/site configured explicitly
(see config/settings.yaml -> sources.workday.tenants). You can read
these three values straight out of a company's Workday careers URL,
e.g. https://acme.wd5.myworkdayjobs.com/en-US/External
              host = acme.wd5.myworkdayjobs.com
              tenant = acme
              site = External

Uses Workday's CXS job search API (POST, JSON body) - no auth
required for public postings, but unofficial/undocumented like the
LinkedIn/Naukri endpoints.
"""

from __future__ import annotations

import time

from app.collectors.base import BaseCollector
from app.collectors.http_client import HttpClient
from app.models.job import EmploymentType
from app.models.job import Job
from app.models.job import JobSource
from app.utils.logger import logger

PAGE_SIZE = 20

REQUEST_DELAY_SECONDS = 0.5


class WorkdayCollector(BaseCollector):

    def __init__(self, tenants: list[dict]) -> None:

        self.client = HttpClient()

        self.tenants = tenants

    @property
    def name(self) -> str:
        return "Workday"

    def collect(self) -> list[Job]:

        jobs: list[Job] = []

        for tenant_config in self.tenants:

            jobs.extend(self._collect_tenant(tenant_config))

        logger.success(
            f"Collected {len(jobs)} jobs from Workday."
        )

        return jobs

    def _collect_tenant(self, tenant_config: dict) -> list[Job]:

        host = tenant_config.get("host", "")
        tenant = tenant_config.get("tenant", "")
        site = tenant_config.get("site", "")

        if not (host and tenant and site):

            logger.warning(
                f"Skipping malformed Workday tenant config: "
                f"{tenant_config}"
            )

            return []

        url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

        results: list[Job] = []

        offset = 0

        while True:

            body = {
                "appliedFacets": {},
                "limit": PAGE_SIZE,
                "offset": offset,
                "searchText": "",
            }

            logger.info(
                f"Loading Workday tenant: {tenant} (offset={offset})"
            )

            try:
                data = self.client.post_json(url, json=body)

            except Exception:

                logger.exception(
                    f"Failed: Workday tenant {tenant}"
                )

                break

            postings = data.get("jobPostings", [])

            if not postings:
                break

            for item in postings:

                title = item.get("title", "")

                path = item.get("externalPath", "")

                try:

                    results.append(

                        Job(

                            title=title,

                            company=tenant,

                            location=(
                                item.get("locationsText", "")
                                or item.get("location", "")
                            ),

                            experience="Unknown",

                            source=JobSource.WORKDAY,

                            url=(
                                f"https://{host}{path}"
                                if path
                                else f"https://{host}"
                            ),

                            employment_type=EmploymentType.UNKNOWN,
                        )
                    )

                except Exception:

                    logger.warning(
                        f"Skipped malformed job at {tenant}: "
                        f"{title!r}"
                    )

            offset += PAGE_SIZE

            total = data.get("total", 0)

            if offset >= total:
                break

            time.sleep(REQUEST_DELAY_SECONDS)

        return results
