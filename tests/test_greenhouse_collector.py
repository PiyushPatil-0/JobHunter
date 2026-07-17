"""
Tests for the Greenhouse collector's dual-host support.

Confirms both boards-api.greenhouse.io (global) and
boards-api.eu.greenhouse.io (EU) are queried, with the right
companies routed to each, and that a job from either host ends up in
the combined result - discovered because currenciesdirect's genuine
India (Mumbai/Hyderabad) roles are only reachable via the EU host,
which the collector didn't support before this fix.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

from app.collectors.greenhouse import GreenhouseCollector


def _fake_job(title: str, location: str) -> dict:
    return {
        "title": title,
        "location": {"name": location},
        "absolute_url": "https://example.com/job",
        "content": "Job description",
    }


class TestGreenhouseDualHost:
    def test_queries_global_host_for_companies(self) -> None:
        collector = GreenhouseCollector(companies=["acme"])

        with patch.object(collector.client, "get_json") as mock_get:
            mock_get.return_value = {"jobs": [_fake_job("Engineer", "Remote")]}
            collector.collect()

        mock_get.assert_called_once_with(
            "https://boards-api.greenhouse.io/v1/boards/acme/jobs"
        )

    def test_queries_eu_host_for_eu_companies(self) -> None:
        collector = GreenhouseCollector(
            companies=[], eu_companies=["currenciesdirect"]
        )

        with patch.object(collector.client, "get_json") as mock_get:
            mock_get.return_value = {
                "jobs": [_fake_job("Accounts Payable Executive", "India - Mumbai")]
            }
            jobs = collector.collect()

        mock_get.assert_called_once_with(
            "https://boards-api.eu.greenhouse.io/v1/boards/currenciesdirect/jobs"
        )
        assert len(jobs) == 1
        assert jobs[0].location == "India - Mumbai"

    def test_combines_global_and_eu_results(self) -> None:
        collector = GreenhouseCollector(
            companies=["acme"], eu_companies=["currenciesdirect"]
        )

        def fake_get_json(url: str):
            if "eu.greenhouse" in url:
                return {"jobs": [_fake_job("Engineering Manager", "India - Hyderabad")]}
            return {"jobs": [_fake_job("Sales Rep", "London")]}

        with patch.object(collector.client, "get_json", side_effect=fake_get_json):
            jobs = collector.collect()

        assert len(jobs) == 2
        locations = {job.location for job in jobs}
        assert locations == {"India - Hyderabad", "London"}

    def test_no_eu_companies_means_eu_host_never_called(self) -> None:
        collector = GreenhouseCollector(companies=["acme"])

        with patch.object(collector.client, "get_json") as mock_get:
            mock_get.return_value = {"jobs": []}
            collector.collect()

        called_urls = [call.args[0] for call in mock_get.call_args_list]
        assert all("eu.greenhouse" not in url for url in called_urls)

    def test_one_company_failing_does_not_abort_the_other(self) -> None:
        collector = GreenhouseCollector(
            companies=["broken"], eu_companies=["currenciesdirect"]
        )

        def fake_get_json(url: str):
            if "eu.greenhouse" in url:
                return {"jobs": [_fake_job("Backend Engineer", "India - Mumbai")]}
            raise RuntimeError("simulated network failure")

        with patch.object(collector.client, "get_json", side_effect=fake_get_json):
            jobs = collector.collect()

        assert len(jobs) == 1
        assert jobs[0].location == "India - Mumbai"
