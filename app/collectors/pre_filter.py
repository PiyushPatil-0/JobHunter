"""
Collector pre-filter.
"""

from app.collectors.title_classifier import TitleClassifier


class PreFilter:

    @classmethod
    def accept(
        cls,
        title: str,
    ) -> bool:

        return TitleClassifier.accept(title)