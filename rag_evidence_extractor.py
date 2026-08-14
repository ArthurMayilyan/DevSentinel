import ast
import json
from typing import Any


def get_evidence_source(
    value: dict[str, Any],
) -> str:
    for key in [
        "source",
        "file",
        "path",
    ]:
        item = value.get(
            key,
        )

        if isinstance(item, str) and item.strip():
            return item

    return ""


def get_evidence_text(
    value: dict[str, Any],
) -> str:
    for key in [
        "text",
        "content",
        "chunk_text",
        "snippet",
    ]:
        item = value.get(
            key,
        )

        if isinstance(item, str) and item.strip():
            return item

    return ""


def is_evidence_item(
    value,
) -> bool:
    return (
        isinstance(value, dict)
        and bool(
            get_evidence_source(
                value,
            )
        )
        and bool(
            get_evidence_text(
                value,
            )
        )
    )


def is_evidence_list(
    value: list,
) -> bool:
    return bool(value) and all(
        is_evidence_item(
            item,
        )
        for item in value
    )


def try_parse_json_or_python_literal(
    value: str,
):
    try:
        return json.loads(
            value,
        )
    except json.JSONDecodeError:
        pass

    try:
        return ast.literal_eval(
            value,
        )
    except (ValueError, SyntaxError):
        return None


def extract_embedded_list_or_dict_strings(
    text: str,
) -> list[str]:
    candidates = []

    list_start = text.find("[")
    list_end = text.rfind("]")

    if list_start != -1 and list_end != -1 and list_end > list_start:
        candidates.append(
            text[list_start:list_end + 1],
        )

    dict_start = text.find("{")
    dict_end = text.rfind("}")

    if dict_start != -1 and dict_end != -1 and dict_end > dict_start:
        candidates.append(
            text[dict_start:dict_end + 1],
        )

    return candidates


def parse_possible_structured_values(
    value: str,
) -> list[Any]:
    text = value.strip()

    if not text:
        return []

    parsed_values = []

    direct_parsed = try_parse_json_or_python_literal(
        text,
    )

    if direct_parsed is not None:
        parsed_values.append(
            direct_parsed,
        )

    for prefix in [
        "Observation:",
        "observation:",
        "Tool result:",
        "tool result:",
        "tool_result:",
        "Result:",
        "result:",
    ]:
        if text.startswith(prefix):
            candidate = text[len(prefix):].strip()

            parsed = try_parse_json_or_python_literal(
                candidate,
            )

            if parsed is not None:
                parsed_values.append(
                    parsed,
                )

    for candidate in extract_embedded_list_or_dict_strings(
        text,
    ):
        parsed = try_parse_json_or_python_literal(
            candidate,
        )

        if parsed is not None:
            parsed_values.append(
                parsed,
            )

    return parsed_values


def extract_evidence_from_value(
    value,
) -> list[dict[str, Any]]:
    if isinstance(value, list):
        if is_evidence_list(
            value,
        ):
            return value

        evidence = []

        for item in value:
            evidence.extend(
                extract_evidence_from_value(
                    item,
                )
            )

        return evidence

    if isinstance(value, dict):
        if is_evidence_item(
            value,
        ):
            return [
                value,
            ]

        evidence = []

        for key in [
            "content",
            "result",
            "tool_result",
            "observation",
            "output",
            "data",
            "message",
        ]:
            if key not in value:
                continue

            evidence.extend(
                extract_evidence_from_value(
                    value[key],
                )
            )

        return evidence

    if isinstance(value, str):
        evidence = []

        for parsed_value in parse_possible_structured_values(
            value,
        ):
            evidence.extend(
                extract_evidence_from_value(
                    parsed_value,
                )
            )

        return evidence

    return []


def deduplicate_evidence(
    evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    deduplicated = []
    seen = set()

    for item in evidence:
        key = (
            get_evidence_source(
                item,
            ),
            item.get(
                "chunk_index",
            ),
            get_evidence_text(
                item,
            ),
        )

        if key in seen:
            continue

        deduplicated.append(
            item,
        )
        seen.add(
            key,
        )

    return deduplicated


def extract_latest_evidence(
    values,
) -> list[dict[str, Any]]:
    for value in reversed(
        values,
    ):
        evidence = extract_evidence_from_value(
            value,
        )

        if evidence:
            return deduplicate_evidence(
                evidence,
            )

    return []


def extract_all_evidence(
    values,
) -> list[dict[str, Any]]:
    evidence = []

    for value in values:
        evidence.extend(
            extract_evidence_from_value(
                value,
            )
        )

    return deduplicate_evidence(
        evidence,
    )