"""The ONLY place in the codebase allowed to import a concrete CaseLawProvider.
Every other module - the reliability agent, the Celery monitor job, the admin recheck
route - must call get_case_law_provider() and depend only on the CaseLawProvider ABC.
If switching CASE_LAW_PROVIDER ever requires touching code outside this package, the
abstraction has been done wrong.
"""
from functools import lru_cache

from app.config import get_settings
from app.reliability.provider import CaseLawProvider


@lru_cache
def get_case_law_provider() -> CaseLawProvider:
    settings = get_settings()
    if settings.case_law_provider == "indiankanoon":
        from app.reliability.indiankanoon_provider import IndianKanoonProvider
        return IndianKanoonProvider(api_token=settings.indiankanoon_api_token)

    from app.reliability.mock_provider import MockCaseLawProvider
    return MockCaseLawProvider()
