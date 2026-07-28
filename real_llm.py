from tool_specs import IssueSeverity, IssueCategory
import json
from openai import OpenAI


class RealLLM:
    def __init__(self, model: str = "gpt-5.5"):
        self.client = OpenAI()
        self.model = model

    def complete(self, messages: list[dict], state=None) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        try:
            action = json.loads(content)
        except json.JSONDecodeError as error:
            return {
                "type": "invalid_output",
                "error": f"Invalid JSON from model: {error}",
                "raw_content": content,
            }

        return action