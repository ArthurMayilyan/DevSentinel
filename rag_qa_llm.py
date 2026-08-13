import ast
import json
from typing import Any

from rag_answer_composer import compose_rag_answer


class DeterministicRagQaLLM:
    def __init__(self):
        self.call_count = 0

    def complete(
        self,
        messages,
        state=None,
    ):
        self.call_count += 1

        if self.call_count == 1:
            return {
                "type": "tool_call",
                "tool": "search_knowledge",
                "arguments": {
                    "query": self.extract_user_query(
                        messages,
                    ),
                },
            }

        evidence = self.extract_latest_evidence(
            messages,
        )

        if not evidence:
            return {
                "type": "final_answer",
                "answer": "I do not have enough evidence to answer.",
            }

        composed_answer = compose_rag_answer(
            query=self.extract_user_query(
                messages,
            ),
            evidence=evidence,
            max_sentences=1,
        )

        return {
            "type": "final_answer",
            "answer": composed_answer.answer,
        }

    def extract_user_query(
        self,
        messages,
    ) -> str:
        for message in reversed(messages):
            if not isinstance(message, dict):
                continue

            if message.get("role") == "user":
                content = message.get(
                    "content",
                    "",
                )

                if isinstance(content, str):
                    return content

        return ""

    def extract_latest_evidence(
        self,
        messages,
    ) -> list[dict[str, Any]]:
        for message in reversed(messages):
            evidence = self.extract_evidence_from_value(
                message,
            )

            if evidence:
                return evidence

        return []

    def extract_evidence_from_value(
        self,
        value,
    ) -> list[dict[str, Any]]:
        if isinstance(value, list):
            if self.is_evidence_list(
                value,
            ):
                return value

            for item in reversed(value):
                evidence = self.extract_evidence_from_value(
                    item,
                )

                if evidence:
                    return evidence

            return []

        if isinstance(value, dict):
            if self.is_evidence_item(
                value,
            ):
                return [
                    value,
                ]

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

                evidence = self.extract_evidence_from_value(
                    value[key],
                )

                if evidence:
                    return evidence

            return []

        if isinstance(value, str):
            parsed_values = self.parse_possible_structured_values(
                value,
            )

            for parsed_value in parsed_values:
                evidence = self.extract_evidence_from_value(
                    parsed_value,
                )

                if evidence:
                    return evidence

            return []

        return []

    def parse_possible_structured_values(
        self,
        value: str,
    ) -> list[Any]:
        text = value.strip()

        if not text:
            return []

        parsed_values = []

        direct_parsed = self.try_parse_json_or_python_literal(
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

                parsed = self.try_parse_json_or_python_literal(
                    candidate,
                )

                if parsed is not None:
                    parsed_values.append(
                        parsed,
                    )

        embedded_candidates = self.extract_embedded_list_or_dict_strings(
            text,
        )

        for candidate in embedded_candidates:
            parsed = self.try_parse_json_or_python_literal(
                candidate,
            )

            if parsed is not None:
                parsed_values.append(
                    parsed,
                )

        return parsed_values

    def extract_embedded_list_or_dict_strings(
        self,
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

    def try_parse_json_or_python_literal(
        self,
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

    def is_evidence_list(
        self,
        value: list,
    ) -> bool:
        return bool(value) and all(
            self.is_evidence_item(
                item,
            )
            for item in value
        )

    def is_evidence_item(
        self,
        value,
    ) -> bool:
        if not isinstance(value, dict):
            return False

        source = self.get_evidence_source(
            value,
        )

        text = self.get_evidence_text(
            value,
        )

        return bool(source) and bool(text)

    def get_evidence_source(
        self,
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
        self,
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