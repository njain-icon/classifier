from classifier.entity_classifier.analyzers.base_analyzer import BaseCountryAnalyzer


from classifier.entity_classifier.analyzers.us_analyzer import USAnalyzer

    # type: ignore



COUNTRY_ANALYZERS = {
    **({"US": USAnalyzer} if USAnalyzer else {}),
}

__all__ = ["BaseCountryAnalyzer", "COUNTRY_ANALYZERS"]


