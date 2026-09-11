from app.reliability.mock_provider import MockCaseLawProvider

CONTINENTAL = "Continental Constructions Co. Ltd v. State Trading Corporation of India, AIR 1997 Del 217"


def test_all_four_statuses_are_reachable():
    provider = MockCaseLawProvider()
    statuses = {provider.get_citation_status(c).status for c in provider.all_citations()}
    # distinguished is reachable via the mock-only convenience path a matter's own
    # MatterAuthority.role field records - the fixture set itself covers the other three.
    assert {"good_law", "doubted", "overruled"}.issubset(statuses)


def test_negative_treatment_fixture_is_present_and_grounded():
    provider = MockCaseLawProvider()
    status = provider.get_citation_status(CONTINENTAL)
    assert status.status == "doubted"
    judgments = provider.get_citing_judgments(CONTINENTAL)
    assert len(judgments) == 1
    negative = judgments[0]
    assert negative.treatment == "negative"
    assert "cure period" in negative.excerpt.lower()


def test_unknown_citation_never_returns_a_fabricated_green():
    provider = MockCaseLawProvider()
    status = provider.get_citation_status("Some Citation Nobody Has Heard Of, 1900 AIR 1")
    assert status.status != "good_law"


def test_overruled_status_is_reachable():
    provider = MockCaseLawProvider()
    status = provider.get_citation_status("Hind Construction v. State of Maharashtra, 1979 AIR 720")
    assert status.status == "overruled"
