from collections import Counter

from app.collectors.greenhouse import GreenhouseCollector
from app.config.settings import settings

collector = GreenhouseCollector(
    settings.sources.greenhouse.companies
)

jobs = collector.collect()

print(f"\nTotal Jobs: {len(jobs)}\n")

titles = Counter()

locations = Counter()

companies = Counter()

for job in jobs:

    titles[job.title] += 1

    locations[job.location] += 1

    companies[job.company] += 1

print("=" * 80)

print("TOP TITLES")

print("=" * 80)

for title, count in titles.most_common(50):

    print(count, title)

print("\n")

print("=" * 80)

print("TOP LOCATIONS")

print("=" * 80)

for location, count in locations.most_common(50):

    print(count, location)

print("\n")

print("=" * 80)

print("TOP COMPANIES")

print("=" * 80)

for company, count in companies.most_common():

    print(count, company)