import pytest

from rag_query_planner import plan_rag_subqueries


def test_plan_rag_subqueries_returns_original_query_for_simple_unknown_query():
    plan = plan_rag_subqueries(
        query="unknown topic",
    )

    assert plan.original_query == "unknown topic"
    assert plan.subqueries == [
        "unknown topic",
    ]


def test_plan_rag_subqueries_plans_single_token_query():
    plan = plan_rag_subqueries(
        query="token expiration",
    )

    assert plan.subqueries == [
        "token expiration",
    ]


def test_plan_rag_subqueries_plans_multi_part_security_query():
    plan = plan_rag_subqueries(
        query="How should credentials and debug mode be handled in production?",
    )

    assert plan.subqueries == [
        "credentials production",
        "debug mode production",
    ]


def test_plan_rag_subqueries_respects_max_subqueries():
    plan = plan_rag_subqueries(
        query="credentials debug token small function",
        max_subqueries=2,
    )

    assert plan.subqueries == [
        "credentials",
        "debug mode",
    ]


def test_plan_rag_subqueries_rejects_empty_query():
    with pytest.raises(ValueError):
        plan_rag_subqueries(
            query="",
        )