import pytest

from review_profiles import (
    REVIEW_PROFILE_FULL,
    REVIEW_PROFILE_SECURITY,
    get_review_profile,
)


def test_get_review_profile_returns_security_profile_by_default():
    profile = get_review_profile(
        "",
    )

    assert profile.name == REVIEW_PROFILE_SECURITY
    assert "credentials" in " ".join(
        profile.knowledge_queries,
    )


def test_get_review_profile_returns_full_profile():
    profile = get_review_profile(
        REVIEW_PROFILE_FULL,
    )

    assert profile.name == REVIEW_PROFILE_FULL
    assert len(
        profile.knowledge_queries,
    ) >= 3


def test_get_review_profile_rejects_unknown_profile():
    with pytest.raises(ValueError):
        get_review_profile(
            "unknown",
        )