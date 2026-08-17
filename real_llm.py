import json

from dotenv import load_dotenv
from openai import (
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app_settings import get_app_settings


_SETTINGS = get_app_settings()


class RealLLM:
    def __init__(
        self,
        model: str = _SETTINGS.openai.model,
        temperature: float | None = None,
        request_timeout_seconds: float = (
            _SETTINGS.openai.request_timeout_seconds
        ),
    ):
        load_dotenv()

        self.client = OpenAI()
        self.model = model
        self.temperature = temperature
        self.request_timeout_seconds = (
            request_timeout_seconds
        )

    def complete(
        self,
        messages: list[dict],
        state=None,
    ) -> dict:
        action = None
        content = ""

        try:
            request = {
                "model": self.model,
                "messages": messages,
                "response_format": {
                    "type": "json_object",
                },
            }

            if self.temperature is not None:
                request[
                    "temperature"
                ] = self.temperature

            client = self.client

            if hasattr(
                client,
                "with_options",
            ):
                client = client.with_options(
                    timeout=self.request_timeout_seconds,
                )

            response = (
                client.chat.completions.create(
                    **request
                )
            )

            content = (
                response.choices[0].message.content
            )

            action = json.loads(
                content,
            )

        except RateLimitError as error:
            return {
                "type": "llm_error",
                "error_type": "rate_limit_or_quota",
                "error": str(
                    error,
                ),
            }

        except BadRequestError as error:
            return {
                "type": "llm_error",
                "error_type": "bad_request",
                "error": str(
                    error,
                ),
            }

        except json.JSONDecodeError as error:
            return {
                "type": "invalid_output",
                "error": (
                    f"Invalid JSON from model: {error}"
                ),
                "raw_content": content,
            }

        return action