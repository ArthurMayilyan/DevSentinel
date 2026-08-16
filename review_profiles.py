from dataclasses import dataclass


REVIEW_PROFILE_SECURITY = "security"
REVIEW_PROFILE_RELIABILITY = "reliability"
REVIEW_PROFILE_MAINTAINABILITY = "maintainability"
REVIEW_PROFILE_FULL = "full"

SUPPORTED_REVIEW_PROFILES = {
    REVIEW_PROFILE_SECURITY,
    REVIEW_PROFILE_RELIABILITY,
    REVIEW_PROFILE_MAINTAINABILITY,
    REVIEW_PROFILE_FULL,
}


@dataclass(frozen=True)
class ReviewProfile:
    name: str
    description: str
    knowledge_queries: list[str]


def get_review_profile(
    profile: str,
) -> ReviewProfile:
    if not profile:
        profile = REVIEW_PROFILE_SECURITY

    if profile not in SUPPORTED_REVIEW_PROFILES:
        supported = ", ".join(
            sorted(
                SUPPORTED_REVIEW_PROFILES,
            )
        )

        raise ValueError(
            f"unsupported review profile: {profile}. Supported profiles: {supported}"
        )

    if profile == REVIEW_PROFILE_SECURITY:
        return ReviewProfile(
            name=REVIEW_PROFILE_SECURITY,
            description="Security-focused review for credentials, tokens, debug mode, and unsafe production behavior.",
            knowledge_queries=[
                "credentials production security",
                "debug mode production",
                "token expiration validation",
            ],
        )

    if profile == REVIEW_PROFILE_RELIABILITY:
        return ReviewProfile(
            name=REVIEW_PROFILE_RELIABILITY,
            description="Reliability-focused review for fragile behavior, missing validation, and unsafe runtime assumptions.",
            knowledge_queries=[
                "production reliability validation",
            ],
        )

    if profile == REVIEW_PROFILE_MAINTAINABILITY:
        return ReviewProfile(
            name=REVIEW_PROFILE_MAINTAINABILITY,
            description="Maintainability-focused review for readability, complexity, and code organization.",
            knowledge_queries=[
                "maintainable code review",
            ],
        )

    return ReviewProfile(
        name=REVIEW_PROFILE_FULL,
        description="Full review profile combining security, reliability, and maintainability checks.",
        knowledge_queries=[
            "credentials production security",
            "debug mode production",
            "token expiration validation",
            "production reliability validation",
            "maintainable code review",
        ],
    )