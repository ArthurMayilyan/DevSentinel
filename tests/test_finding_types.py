from finding_types import (
    FINDING_TYPE_SECURITY_DEBUG_MODE,
    FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS,
    FINDING_TYPE_SECURITY_HARDCODED_SECRET,
    FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE,
    FINDING_TYPE_SECURITY_OTHER,
    FINDING_TYPE_SECURITY_TOKEN_EXPIRATION,
    FINDING_TYPE_SECURITY_TOKEN_VALIDATION,
    infer_finding_type,
    normalize_finding_type,
)


def test_infer_hardcoded_secret():
    assert infer_finding_type(
        issue="Hardcoded SECRET_KEY.",
    ) == FINDING_TYPE_SECURITY_HARDCODED_SECRET


def test_infer_hardcoded_admin_credentials():
    assert infer_finding_type(
        issue="Hardcoded admin credentials.",
    ) == FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS


def test_infer_debug_mode():
    assert infer_finding_type(
        issue="Debug mode enabled.",
    ) == FINDING_TYPE_SECURITY_DEBUG_MODE


def test_infer_token_validation():
    assert infer_finding_type(
        issue="Token validation is incomplete.",
    ) == FINDING_TYPE_SECURITY_TOKEN_VALIDATION


def test_infer_token_expiration():
    assert infer_finding_type(
        issue="Tokens may be unsigned or non-expiring.",
    ) == FINDING_TYPE_SECURITY_TOKEN_EXPIRATION


def test_infer_information_disclosure():
    assert infer_finding_type(
        issue="Debug information may be exposed in API responses.",
    ) == FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE


def test_infer_unknown_returns_other():
    assert infer_finding_type(
        issue="Something completely unknown.",
    ) == FINDING_TYPE_SECURITY_OTHER


def test_normalize_accepts_known_type():
    assert normalize_finding_type(
        "security.debug_mode",
    ) == FINDING_TYPE_SECURITY_DEBUG_MODE


def test_normalize_falls_back_to_issue_inference():
    assert normalize_finding_type(
        "",
        issue="Debug mode enabled.",
    ) == FINDING_TYPE_SECURITY_DEBUG_MODE