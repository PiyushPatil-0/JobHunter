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


class TelegramConfig(BaseModel):
    enabled: bool


class FilterConfig(BaseModel):
    minimum_match_score: int


class JobPreferenceConfig(BaseModel):
    keywords: list[str]
    locations: list[str]
    experience: list[str]
    employment_types: list[str]


class CompanyConfig(BaseModel):
    include: list[str]
    exclude: list[str]


# ---------- SOURCES: ATS (company-slug based) ----------

class GreenhouseConfig(BaseModel):
    enabled: bool = True
    companies: list[str]


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
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    max_pages: int = 2


class NaukriConfig(BaseModel):
    enabled: bool = False
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    max_pages: int = 2


class SourcesConfig(BaseModel):
    greenhouse: GreenhouseConfig
    lever: LeverConfig = LeverConfig()
    ashby: AshbyConfig = AshbyConfig()
    smartrecruiters: SmartRecruitersConfig = SmartRecruitersConfig()
    workday: WorkdayConfig = WorkdayConfig()
    linkedin: LinkedInConfig = LinkedInConfig()
    naukri: NaukriConfig = NaukriConfig()


# ---------- SETTINGS ----------

class Settings(BaseModel):
    app: AppConfig
    scheduler: SchedulerConfig
    database: DatabaseConfig
    telegram: TelegramConfig
    filters: FilterConfig
    job_preferences: JobPreferenceConfig
    companies: CompanyConfig
    sources: SourcesConfig


def load_settings() -> Settings:
    config_file = ROOT_DIR / "config" / "settings.yaml"

    with open(config_file, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return Settings(**config)


settings = load_settings()
