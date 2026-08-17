import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CONFIG_FILE_NAME = "agentloop.toml"
CONFIG_PATH_ENV_NAME = "AGENTLOOP_CONFIG_PATH"


@dataclass(frozen=True)
class OpenAISettings:
    model: str
    max_output_tokens: int
    request_timeout_seconds: float
    review_max_content_chars: int


@dataclass(frozen=True)
class CliSettings:
    openai_max_steps: int
    openai_max_output_tokens: int
    openai_request_timeout_seconds: float


@dataclass(frozen=True)
class RuntimeSettings:
    agent_mode_max_steps: int
    command_timeout_seconds: float


@dataclass(frozen=True)
class AgentSettings:
    max_steps: int
    max_rejected_final_answers: int
    max_rejected_tool_calls: int
    max_invalid_llm_outputs: int


@dataclass(frozen=True)
class ReviewSettings:
    default_reviewer: str
    max_findings: int
    max_files: int
    max_file_size_bytes: int


@dataclass(frozen=True)
class RagSettings:
    top_k: int
    chunk_max_chars: int
    chunk_overlap_chars: int
    agent_max_steps: int
    retrieval_strategy: str


@dataclass(frozen=True)
class ArtifactSettings:
    default_report_path: str
    reviews_dir_name: str
    comparisons_dir_name: str


@dataclass(frozen=True)
class WorkspacePresetSettings:
    name: str
    profile: str
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    max_files: int
    max_file_size_bytes: int


@dataclass(frozen=True)
class AppSettings:
    openai: OpenAISettings
    cli: CliSettings
    runtime: RuntimeSettings
    agent: AgentSettings
    review: ReviewSettings
    rag: RagSettings
    artifacts: ArtifactSettings
    presets: dict[str, WorkspacePresetSettings]
    config_path: str


def default_config_path() -> Path:
    return Path(
        __file__,
    ).resolve().with_name(
        DEFAULT_CONFIG_FILE_NAME,
    )


def resolve_config_path(
    *,
    config_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    environment = environ or os.environ

    if config_path:
        return Path(
            config_path,
        ).expanduser().resolve()

    environment_path = environment.get(
        CONFIG_PATH_ENV_NAME,
        "",
    ).strip()

    if environment_path:
        return Path(
            environment_path,
        ).expanduser().resolve()

    return default_config_path()


def read_toml_config(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {}

    if not path.is_file():
        raise ValueError(
            f"AgentLoop config path must be a file: {path}"
        )

    with path.open(
        "rb",
    ) as file:
        value = tomllib.load(
            file,
        )

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            "AgentLoop configuration must contain a TOML table."
        )

    return value


def get_section(
    data: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    value = data.get(
        name,
        {},
    )

    if value is None:
        return {}

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"Configuration section [{name}] must be a table."
        )

    return value


def env_string(
    *,
    environ: Mapping[str, str],
    name: str,
    default: str,
) -> str:
    value = environ.get(
        name,
    )

    if value is None:
        return default

    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{name} must not be empty."
        )

    return normalized


def env_int(
    *,
    environ: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    value = environ.get(
        name,
    )

    if value is None:
        return default

    try:
        return int(
            value,
        )
    except ValueError as exc:
        raise ValueError(
            f"{name} must be an integer."
        ) from exc


def env_float(
    *,
    environ: Mapping[str, str],
    name: str,
    default: float,
) -> float:
    value = environ.get(
        name,
    )

    if value is None:
        return default

    try:
        return float(
            value,
        )
    except ValueError as exc:
        raise ValueError(
            f"{name} must be a number."
        ) from exc


def positive_int(
    name: str,
    value: Any,
) -> int:
    if type(
        value,
    ) is not int:
        raise ValueError(
            f"{name} must be an integer."
        )

    if value <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return value


def positive_float(
    name: str,
    value: Any,
) -> float:
    if type(
        value,
    ) not in {
        int,
        float,
    }:
        raise ValueError(
            f"{name} must be a number."
        )

    numeric_value = float(
        value,
    )

    if numeric_value <= 0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return numeric_value


def non_empty_string(
    name: str,
    value: Any,
) -> str:
    if not isinstance(
        value,
        str,
    ) or not value.strip():
        raise ValueError(
            f"{name} must be a non-empty string."
        )

    return value.strip()


def string_list(
    name: str,
    value: Any,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if not isinstance(
        value,
        list,
    ):
        raise ValueError(
            f"{name} must be an array of strings."
        )

    result = []

    for item in value:
        if not isinstance(
            item,
            str,
        ) or not item.strip():
            raise ValueError(
                f"{name} must contain only non-empty strings."
            )

        result.append(
            item.strip(),
        )

    return tuple(
        result,
    )


def build_workspace_presets(
    *,
    data: dict[str, Any],
    review_max_files: int,
    review_max_file_size_bytes: int,
) -> dict[str, WorkspacePresetSettings]:
    presets_section = get_section(
        data,
        "presets",
    )

    presets = {}

    for preset_name, preset_value in presets_section.items():
        if not isinstance(
            preset_value,
            dict,
        ):
            raise ValueError(
                f"Preset {preset_name} must be a TOML table."
            )

        presets[preset_name] = WorkspacePresetSettings(
            name=preset_name,
            profile=non_empty_string(
                f"presets.{preset_name}.profile",
                preset_value.get(
                    "profile",
                    "security",
                ),
            ),
            include_globs=string_list(
                f"presets.{preset_name}.include_globs",
                preset_value.get(
                    "include_globs",
                    [],
                ),
            ),
            exclude_globs=string_list(
                f"presets.{preset_name}.exclude_globs",
                preset_value.get(
                    "exclude_globs",
                    [],
                ),
            ),
            max_files=positive_int(
                f"presets.{preset_name}.max_files",
                preset_value.get(
                    "max_files",
                    review_max_files,
                ),
            ),
            max_file_size_bytes=positive_int(
                f"presets.{preset_name}.max_file_size_bytes",
                preset_value.get(
                    "max_file_size_bytes",
                    review_max_file_size_bytes,
                ),
            ),
        )

    return presets


def load_app_settings(
    *,
    config_path: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> AppSettings:
    environment = environ or os.environ

    resolved_config_path = resolve_config_path(
        config_path=config_path,
        environ=environment,
    )

    data = read_toml_config(
        resolved_config_path,
    )

    openai_section = get_section(
        data,
        "openai",
    )

    cli_section = get_section(
        data,
        "cli",
    )

    runtime_section = get_section(
        data,
        "runtime",
    )

    agent_section = get_section(
        data,
        "agent",
    )

    review_section = get_section(
        data,
        "review",
    )

    rag_section = get_section(
        data,
        "rag",
    )

    artifacts_section = get_section(
        data,
        "artifacts",
    )

    openai_model = env_string(
        environ=environment,
        name="AGENTLOOP_OPENAI_MODEL",
        default=non_empty_string(
            "openai.model",
            openai_section.get(
                "model",
                "gpt-5.6-luna",
            ),
        ),
    )

    openai_max_output_tokens = env_int(
        environ=environment,
        name="AGENTLOOP_OPENAI_MAX_OUTPUT_TOKENS",
        default=positive_int(
            "openai.max_output_tokens",
            openai_section.get(
                "max_output_tokens",
                500,
            ),
        ),
    )

    openai_request_timeout_seconds = env_float(
        environ=environment,
        name="AGENTLOOP_OPENAI_REQUEST_TIMEOUT_SECONDS",
        default=positive_float(
            "openai.request_timeout_seconds",
            openai_section.get(
                "request_timeout_seconds",
                30.0,
            ),
        ),
    )

    openai_review_max_content_chars = positive_int(
        "openai.review_max_content_chars",
        openai_section.get(
            "review_max_content_chars",
            12_000,
        ),
    )

    cli_openai_max_steps = positive_int(
        "cli.openai_max_steps",
        cli_section.get(
            "openai_max_steps",
            15,
        ),
    )

    cli_openai_max_output_tokens = positive_int(
        "cli.openai_max_output_tokens",
        cli_section.get(
            "openai_max_output_tokens",
            250,
        ),
    )

    cli_openai_request_timeout_seconds = positive_float(
        "cli.openai_request_timeout_seconds",
        cli_section.get(
            "openai_request_timeout_seconds",
            10.0,
        ),
    )

    runtime_agent_mode_max_steps = positive_int(
        "runtime.agent_mode_max_steps",
        runtime_section.get(
            "agent_mode_max_steps",
            4,
        ),
    )

    runtime_command_timeout_seconds = env_float(
        environ=environment,
        name="AGENTLOOP_COMMAND_TIMEOUT_SECONDS",
        default=positive_float(
            "runtime.command_timeout_seconds",
            runtime_section.get(
                "command_timeout_seconds",
                120.0,
            ),
        ),
    )

    agent_max_steps = positive_int(
        "agent.max_steps",
        agent_section.get(
            "max_steps",
            8,
        ),
    )

    max_rejected_final_answers = positive_int(
        "agent.max_rejected_final_answers",
        agent_section.get(
            "max_rejected_final_answers",
            3,
        ),
    )

    max_rejected_tool_calls = positive_int(
        "agent.max_rejected_tool_calls",
        agent_section.get(
            "max_rejected_tool_calls",
            5,
        ),
    )

    max_invalid_llm_outputs = positive_int(
        "agent.max_invalid_llm_outputs",
        agent_section.get(
            "max_invalid_llm_outputs",
            3,
        ),
    )

    default_reviewer = env_string(
        environ=environment,
        name="AGENTLOOP_DEFAULT_REVIEWER",
        default=non_empty_string(
            "review.default_reviewer",
            review_section.get(
                "default_reviewer",
                "deterministic",
            ),
        ),
    )

    if default_reviewer not in {
        "deterministic",
        "openai",
    }:
        raise ValueError(
            "review.default_reviewer must be deterministic or openai."
        )

    review_max_findings = positive_int(
        "review.max_findings",
        review_section.get(
            "max_findings",
            5,
        ),
    )

    review_max_files = env_int(
        environ=environment,
        name="AGENTLOOP_REVIEW_MAX_FILES",
        default=positive_int(
            "review.max_files",
            review_section.get(
                "max_files",
                200,
            ),
        ),
    )

    review_max_file_size_bytes = env_int(
        environ=environment,
        name="AGENTLOOP_REVIEW_MAX_FILE_SIZE_BYTES",
        default=positive_int(
            "review.max_file_size_bytes",
            review_section.get(
                "max_file_size_bytes",
                200_000,
            ),
        ),
    )

    rag_top_k = env_int(
        environ=environment,
        name="AGENTLOOP_RAG_TOP_K",
        default=positive_int(
            "rag.top_k",
            rag_section.get(
                "top_k",
                3,
            ),
        ),
    )

    rag_chunk_max_chars = positive_int(
        "rag.chunk_max_chars",
        rag_section.get(
            "chunk_max_chars",
            1000,
        ),
    )

    rag_chunk_overlap_chars = positive_int(
        "rag.chunk_overlap_chars",
        rag_section.get(
            "chunk_overlap_chars",
            100,
        ),
    )

    if rag_chunk_overlap_chars >= rag_chunk_max_chars:
        raise ValueError(
            "rag.chunk_overlap_chars must be smaller than rag.chunk_max_chars."
        )

    rag_agent_max_steps = positive_int(
        "rag.agent_max_steps",
        rag_section.get(
            "agent_max_steps",
            4,
        ),
    )

    rag_retrieval_strategy = non_empty_string(
        "rag.retrieval_strategy",
        rag_section.get(
            "retrieval_strategy",
            "default",
        ),
    )

    default_report_path = non_empty_string(
        "artifacts.default_report_path",
        artifacts_section.get(
            "default_report_path",
            "report.md",
        ),
    )

    reviews_dir_name = non_empty_string(
        "artifacts.reviews_dir_name",
        artifacts_section.get(
            "reviews_dir_name",
            "reviews",
        ),
    )

    comparisons_dir_name = non_empty_string(
        "artifacts.comparisons_dir_name",
        artifacts_section.get(
            "comparisons_dir_name",
            "comparisons",
        ),
    )

    presets = build_workspace_presets(
        data=data,
        review_max_files=review_max_files,
        review_max_file_size_bytes=review_max_file_size_bytes,
    )

    return AppSettings(
        openai=OpenAISettings(
            model=openai_model,
            max_output_tokens=positive_int(
                "openai.max_output_tokens",
                openai_max_output_tokens,
            ),
            request_timeout_seconds=positive_float(
                "openai.request_timeout_seconds",
                openai_request_timeout_seconds,
            ),
            review_max_content_chars=openai_review_max_content_chars,
        ),
        cli=CliSettings(
            openai_max_steps=cli_openai_max_steps,
            openai_max_output_tokens=cli_openai_max_output_tokens,
            openai_request_timeout_seconds=cli_openai_request_timeout_seconds,
        ),
        runtime=RuntimeSettings(
            agent_mode_max_steps=runtime_agent_mode_max_steps,
            command_timeout_seconds=positive_float(
                "runtime.command_timeout_seconds",
                runtime_command_timeout_seconds,
            ),
        ),
        agent=AgentSettings(
            max_steps=agent_max_steps,
            max_rejected_final_answers=max_rejected_final_answers,
            max_rejected_tool_calls=max_rejected_tool_calls,
            max_invalid_llm_outputs=max_invalid_llm_outputs,
        ),
        review=ReviewSettings(
            default_reviewer=default_reviewer,
            max_findings=review_max_findings,
            max_files=positive_int(
                "review.max_files",
                review_max_files,
            ),
            max_file_size_bytes=positive_int(
                "review.max_file_size_bytes",
                review_max_file_size_bytes,
            ),
        ),
        rag=RagSettings(
            top_k=positive_int(
                "rag.top_k",
                rag_top_k,
            ),
            chunk_max_chars=rag_chunk_max_chars,
            chunk_overlap_chars=rag_chunk_overlap_chars,
            agent_max_steps=rag_agent_max_steps,
            retrieval_strategy=rag_retrieval_strategy,
        ),
        artifacts=ArtifactSettings(
            default_report_path=default_report_path,
            reviews_dir_name=reviews_dir_name,
            comparisons_dir_name=comparisons_dir_name,
        ),
        presets=presets,
        config_path=str(
            resolved_config_path,
        ),
    )


def get_app_settings() -> AppSettings:
    return load_app_settings()