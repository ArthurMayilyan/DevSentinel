from tool_specs import IssueSeverity, IssueCategory
import json
from openai import BadRequestError, OpenAI, RateLimitError
from dotenv import load_dotenv

class RealLLM:
    def __init__(self, model: str = "gpt-5.6-luna", temperature: float | None = None):
        load_dotenv()
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature

    def complete(self, messages: list[dict], state=None) -> dict:
        action = None

        try:
            request = {
                "model": self.model,
                "messages": messages,
                "response_format": {"type": "json_object"},
            }

            if self.temperature is not None:
                request["temperature"] = self.temperature

            response = self.client.chat.completions.create(**request)

            content = response.choices[0].message.content

            action = json.loads(content)

        except RateLimitError as error:
            return {
                "type": "llm_error",
                "error_type": "rate_limit_or_quota",
                "error": str(error),
            }

        except BadRequestError as error:
            return {
                "type": "llm_error",
                "error_type": "bad_request",
                "error": str(error),
            }

           
        except json.JSONDecodeError as error:
            return {
                "type": "invalid_output",
                "error": f"Invalid JSON from model: {error}",
                "raw_content": content,
            }

        return action