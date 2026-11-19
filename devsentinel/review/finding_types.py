FINDING_TYPE_SECURITY_HARDCODED_SECRET = (
    "security.hardcoded_secret"
)

FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS = (
    "security.hardcoded_admin_credentials"
)

FINDING_TYPE_SECURITY_DEBUG_MODE = (
    "security.debug_mode"
)

FINDING_TYPE_SECURITY_TOKEN_VALIDATION = (
    "security.token_validation"
)

FINDING_TYPE_SECURITY_TOKEN_EXPIRATION = (
    "security.token_expiration"
)

FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE = (
    "security.information_disclosure"
)

FINDING_TYPE_SECURITY_OTHER = (
    "security.other"
)


SUPPORTED_FINDING_TYPES = {
    FINDING_TYPE_SECURITY_HARDCODED_SECRET,
    FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS,
    FINDING_TYPE_SECURITY_DEBUG_MODE,
    FINDING_TYPE_SECURITY_TOKEN_VALIDATION,
    FINDING_TYPE_SECURITY_TOKEN_EXPIRATION,
    FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE,
    FINDING_TYPE_SECURITY_OTHER,
}


def infer_finding_type(
    *,
    issue: str,
    evidence: str = "",
) -> str:
    text = (
        f"{issue} {evidence}"
    ).lower()

    if (
        "admin" in text
        and (
            "credential" in text
            or "password" in text
            or "username" in text
        )
    ):
        return FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS

    if (
        "debug information" in text
        or "information disclosure" in text
        or (
            "debug" in text
            and "expos" in text
        )
    ):
        return FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE

    if (
        "token validation" in text
        or "cryptographic validation" in text
        or (
            "token" in text
            and "signature" in text
            and "valid" in text
        )
    ):
        return FINDING_TYPE_SECURITY_TOKEN_VALIDATION

    if (
        "non-expiring" in text
        or "unsigned" in text
        or (
            "token" in text
            and "expiration" in text
        )
        or (
            "token" in text
            and "expiry" in text
        )
    ):
        return FINDING_TYPE_SECURITY_TOKEN_EXPIRATION

    if (
        "secret_key" in text
        or "hardcoded secret" in text
        or "hardcoded secret key" in text
    ):
        return FINDING_TYPE_SECURITY_HARDCODED_SECRET

    if (
        "debug mode" in text
        or "debug=true" in text
        or "debug = true" in text
    ):
        return FINDING_TYPE_SECURITY_DEBUG_MODE

    return FINDING_TYPE_SECURITY_OTHER


def normalize_finding_type(
    value: str,
    *,
    issue: str = "",
    evidence: str = "",
) -> str:
    if isinstance(
        value,
        str,
    ):
        normalized = value.strip().lower()

        if normalized in SUPPORTED_FINDING_TYPES:
            return normalized

    return infer_finding_type(
        issue=issue,
        evidence=evidence,
    )