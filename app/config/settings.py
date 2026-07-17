"""
Application configuration loader.
"""

from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import Field

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[2]


class AppConfig(BaseModel):
    name: str
    version: str
    environment: str


class SchedulerConfig(BaseModel):
    ats_interval_minutes: int
    job_board_interval_minutes: int


class DatabaseConfig(BaseModel):
    path: str
    job_retention_days: int = Field(default=14, ge=1)


class TelegramConfig(BaseModel):
    enabled: bool


class CompanyConfig(BaseModel):
    include: list[str]
    exclude: list[str]


# ---------- SOURCES: ATS (company-slug based) ----------

class GreenhouseConfig(BaseModel):
    enabled: bool = True
    companies: list[str]
    # Some companies' Greenhouse boards are hosted on the EU-specific
    # domain (job-boards.eu.greenhouse.io) rather than the global one
    # - a different API host entirely. Discovered via
    # currenciesdirect, which has genuine India (Mumbai/Hyderabad)
    # roles but is unreachable through the global host.
    eu_companies: list[str] = Field(default_factory=list)


class LeverConfig(BaseModel):
    enabled: bool = False
    companies: list[str] = Field(default_factory=list)


class AshbyConfig(BaseModel):
    enabled: bool = False
    companies: list[str] = Field(default_factory=list)


class SmartRecruitersConfig(BaseModel):
    enabled: bool = False
    companies: list[str] = Field(default_factory=list)


# ---------- SOURCES: Workday (tenant-based, no simple slug) ----------

class WorkdayTenantConfig(BaseModel):
    host: str
    tenant: str
    site: str


class WorkdayConfig(BaseModel):
    enabled: bool = False
    tenants: list[WorkdayTenantConfig] = Field(default_factory=list)


# ---------- SOURCES: consumer job boards ----------

class LinkedInConfig(BaseModel):
    enabled: bool = False
    max_pages: int = 2


class NaukriConfig(BaseModel):
    enabled: bool = False
    max_pages: int = 2


class AggregatorConfig(BaseModel):
    """
    Config for the generic job-aggregator collector
    (app.collectors.job_aggregator). Unlike LinkedIn/Naukri (whose
    own terms prohibit this kind of use entirely), this plugs into
    third-party job-search APIs that are explicitly built and
    documented for third parties to integrate - Adzuna, Careerjet,
    or Jooble.

    Credentials are intentionally NOT here - they're secrets, same
    category as TELEGRAM_BOT_TOKEN, and belong in .env
    (AGGREGATOR_API_KEY / AGGREGATOR_API_SECRET), not in settings.yaml.
    See .env.example.
    """
    enabled: bool = False
    provider: str = ""  # "adzuna" | "careerjet" | "jooble"
    country: str = "in"


class SourcesConfig(BaseModel):
    greenhouse: GreenhouseConfig
    lever: LeverConfig = LeverConfig()
    ashby: AshbyConfig = AshbyConfig()
    smartrecruiters: SmartRecruitersConfig = SmartRecruitersConfig()
    workday: WorkdayConfig = WorkdayConfig()
    linkedin: LinkedInConfig = LinkedInConfig()
    naukri: NaukriConfig = NaukriConfig()
    aggregator: AggregatorConfig = AggregatorConfig()


# ---------- SETTINGS ----------

class Settings(BaseModel):
    app: AppConfig
    scheduler: SchedulerConfig
    database: DatabaseConfig
    telegram: TelegramConfig
    companies: CompanyConfig
    sources: SourcesConfig


def load_settings() -> Settings:
    config_file = ROOT_DIR / "config" / "settings.yaml"

    with open(config_file, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return Settings(**config)


settings = load_settings()
