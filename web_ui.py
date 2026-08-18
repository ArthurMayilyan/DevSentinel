import argparse
import json
import webbrowser
from http import HTTPStatus
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path
from typing import Any
from urllib.parse import (
    parse_qs,
    quote,
    unquote,
    urlparse,
)

from app_settings import get_app_settings
from mcp_review_git_diff import (
    mcp_review_git_diff,
)
from mcp_review_workspace import (
    mcp_review_workspace,
)
from mcp_server_context import (
    build_agent_loop_mcp_context,
)
from reviewer_config import (
    DEFAULT_OPENAI_REVIEW_MODEL,
    DEFAULT_REVIEWER,
)
from workspace_review_presets import (
    SUPPORTED_WORKSPACE_PRESETS,
    WORKSPACE_PRESET_PYTHON_SECURITY,
)


DEFAULT_WEB_HOST = "127.0.0.1"
DEFAULT_WEB_PORT = 8765

STATIC_DIR = (
    Path(__file__).resolve().parent
    / "web_ui_static"
)

INDEX_PATH = (
    STATIC_DIR
    / "index.html"
)


def build_web_ui_config() -> dict[str, Any]:
    return {
        "presets": sorted(
            SUPPORTED_WORKSPACE_PRESETS,
        ),
        "reviewers": [
            "deterministic",
            "openai",
        ],
        "defaults": {
            "preset": (
                WORKSPACE_PRESET_PYTHON_SECURITY
            ),
            "reviewer": DEFAULT_REVIEWER,
            "model": (
                DEFAULT_OPENAI_REVIEW_MODEL
            ),
            "base_ref": "main",
            "target_ref": "HEAD",
        },
    }


def require_non_empty_string(
    payload: dict[str, Any],
    key: str,
) -> str:
    value = payload.get(
        key,
        "",
    )

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{key} must be a string."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"{key} is required."
        )

    return value


def optional_string(
    payload: dict[str, Any],
    key: str,
    default: str = "",
) -> str:
    value = payload.get(
        key,
        default,
    )

    if value is None:
        return default

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(
            f"{key} must be a string."
        )

    return value.strip()


def run_review_request(
    *,
    context,
    payload: dict[str, Any],
) -> dict[str, Any]:
    mode = require_non_empty_string(
        payload,
        "mode",
    )

    if mode not in {
        "workspace",
        "git",
        "staged",
    }:
        raise ValueError(
            "mode must be one of: "
            "workspace, git, staged."
        )

    project_path = (
        require_non_empty_string(
            payload,
            "project_path",
        )
    )

    preset = optional_string(
        payload,
        "preset",
        WORKSPACE_PRESET_PYTHON_SECURITY,
    )

    reviewer = optional_string(
        payload,
        "reviewer",
        DEFAULT_REVIEWER,
    )

    model = optional_string(
        payload,
        "model",
        DEFAULT_OPENAI_REVIEW_MODEL,
    )

    reviews_dir = optional_string(
        payload,
        "reviews_dir",
    )

    if mode == "workspace":
        return mcp_review_workspace(
            context=context,
            workspace_path=project_path,
            preset=preset,
            reviewer=reviewer,
            model=model,
            reviews_dir=reviews_dir,
        )

    base_ref = optional_string(
        payload,
        "base_ref",
        "main",
    )

    target_ref = optional_string(
        payload,
        "target_ref",
        "HEAD",
    )

    return mcp_review_git_diff(
        context=context,
        repository_path=project_path,
        base_ref=base_ref,
        target_ref=target_ref,
        staged_only=(
            mode == "staged"
        ),
        preset=preset,
        reviewer=reviewer,
        model=model,
        reviews_dir=reviews_dir,
    )


def safe_load_json(
    path: Path,
) -> dict[str, Any]:
    if not path.is_file():
        return {}

    try:
        value = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(
        value,
        dict,
    ):
        return {}

    return value


def resolve_reviews_dir(
    *,
    project_path: str,
    reviews_dir: str = "",
) -> Path:
    if reviews_dir:
        return Path(
            reviews_dir,
        ).expanduser().resolve(
            strict=False,
        )

    settings = get_app_settings()

    return (
        Path(
            project_path,
        )
        .expanduser()
        .resolve(
            strict=False,
        )
        / settings.artifacts.reviews_dir_name
    )


def load_recent_reviews(
    *,
    project_path: str,
    reviews_dir: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    if limit <= 0:
        raise ValueError(
            "limit must be greater than zero."
        )

    root = resolve_reviews_dir(
        project_path=project_path,
        reviews_dir=reviews_dir,
    )

    if not root.is_dir():
        return []

    runs: list[
        dict[str, Any]
    ] = []

    directories = sorted(
        (
            path
            for path in root.iterdir()
            if path.is_dir()
            and path.name
            != "comparisons"
        ),
        key=lambda path: path.name,
        reverse=True,
    )

    for run_dir in directories:
        summary_data = safe_load_json(
            run_dir
            / "summary.json",
        )

        run_config = safe_load_json(
            run_dir
            / "run_config.json",
        )

        findings_path = (
            run_dir
            / "findings.json"
        )

        findings_count = (
            summary_data.get(
                "findings_count",
            )
        )

        if not isinstance(
            findings_count,
            int,
        ):
            findings_count = 0

            if findings_path.is_file():
                try:
                    findings = json.loads(
                        findings_path.read_text(
                            encoding="utf-8",
                        )
                    )

                    if isinstance(
                        findings,
                        list,
                    ):
                        findings_count = len(
                            findings,
                        )

                except (
                    OSError,
                    json.JSONDecodeError,
                ):
                    pass

        summary = summary_data.get(
            "summary",
            "",
        )

        if not isinstance(
            summary,
            str,
        ):
            summary = ""

        workflow = run_config.get(
            "workflow",
            "workspace",
        )

        if not isinstance(
            workflow,
            str,
        ):
            workflow = "workspace"

        reviewer = run_config.get(
            "reviewer",
            "",
        )

        if not isinstance(
            reviewer,
            str,
        ):
            reviewer = ""

        html_path = (
            run_dir
            / "report.html"
        )

        runs.append(
            {
                "run_id": (
                    run_dir.name
                ),
                "workflow": workflow,
                "reviewer": reviewer,
                "findings_count": (
                    findings_count
                ),
                "summary": summary,
                "_report_html_path": (
                    str(
                        html_path,
                    )
                    if html_path.is_file()
                    else ""
                ),
            }
        )

        if len(
            runs,
        ) >= limit:
            break

    return runs


def extract_report_html_path(
    result: dict[str, Any],
) -> str:
    artifacts = result.get(
        "artifacts",
    )

    if isinstance(
        artifacts,
        dict,
    ):
        value = artifacts.get(
            "report_html_path",
        )

        if isinstance(
            value,
            str,
        ) and value:
            return value

    value = result.get(
        "report_html_path",
    )

    if isinstance(
        value,
        str,
    ):
        return value

    return ""


class AgentLoopWebServer(
    ThreadingHTTPServer,
):
    def __init__(
        self,
        server_address,
        handler_class,
        *,
        knowledge_path: str = "",
    ):
        super().__init__(
            server_address,
            handler_class,
        )

        self.context = (
            build_agent_loop_mcp_context(
                knowledge_path=knowledge_path,
            )
        )

        self.report_paths: dict[
            str,
            Path,
        ] = {}

    def register_report(
        self,
        *,
        run_id: str,
        report_path: str,
    ) -> str:
        if (
            not run_id
            or not report_path
        ):
            return ""

        path = Path(
            report_path,
        ).expanduser().resolve(
            strict=False,
        )

        if not path.is_file():
            return ""

        self.report_paths[
            run_id
        ] = path

        return (
            "/reports/"
            + quote(
                run_id,
                safe="",
            )
        )


class AgentLoopWebHandler(
    BaseHTTPRequestHandler,
):
    server: AgentLoopWebServer

    def send_json(
        self,
        payload: Any,
        *,
        status: HTTPStatus = (
            HTTPStatus.OK
        ),
    ) -> None:
        content = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ).encode(
            "utf-8",
        )

        self.send_response(
            status,
        )

        self.send_header(
            "Content-Type",
            (
                "application/json; "
                "charset=utf-8"
            ),
        )

        self.send_header(
            "Content-Length",
            str(
                len(
                    content,
                )
            ),
        )

        self.end_headers()

        self.wfile.write(
            content,
        )

    def send_text_file(
        self,
        path: Path,
        *,
        content_type: str,
    ) -> None:
        if not path.is_file():
            self.send_error(
                HTTPStatus.NOT_FOUND,
            )
            return

        content = path.read_bytes()

        self.send_response(
            HTTPStatus.OK,
        )

        self.send_header(
            "Content-Type",
            content_type,
        )

        self.send_header(
            "Content-Length",
            str(
                len(
                    content,
                )
            ),
        )

        self.end_headers()

        self.wfile.write(
            content,
        )

    def register_result_report(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        output = dict(
            result,
        )

        run_id = output.get(
            "run_id",
            "",
        )

        if not isinstance(
            run_id,
            str,
        ):
            run_id = ""

        report_html_path = (
            extract_report_html_path(
                output,
            )
        )

        output[
            "report_url"
        ] = self.server.register_report(
            run_id=run_id,
            report_path=report_html_path,
        )

        return output

    def do_GET(
        self,
    ) -> None:
        parsed = urlparse(
            self.path,
        )

        if parsed.path in {
            "/",
            "/index.html",
        }:
            self.send_text_file(
                INDEX_PATH,
                content_type=(
                    "text/html; charset=utf-8"
                ),
            )
            return

        if parsed.path == "/api/config":
            self.send_json(
                build_web_ui_config(),
            )
            return

        if parsed.path == "/api/history":
            query = parse_qs(
                parsed.query,
            )

            project_path = (
                query.get(
                    "project_path",
                    [""],
                )[0]
            )

            reviews_dir = (
                query.get(
                    "reviews_dir",
                    [""],
                )[0]
            )

            if not project_path:
                self.send_json(
                    {
                        "error": (
                            "project_path "
                            "is required."
                        )
                    },
                    status=(
                        HTTPStatus.BAD_REQUEST
                    ),
                )
                return

            try:
                history = (
                    load_recent_reviews(
                        project_path=(
                            project_path
                        ),
                        reviews_dir=(
                            reviews_dir
                        ),
                    )
                )

            except Exception as exc:
                self.send_json(
                    {
                        "error": str(
                            exc,
                        )
                    },
                    status=(
                        HTTPStatus.BAD_REQUEST
                    ),
                )
                return

            output = []

            for item in history:
                value = dict(
                    item,
                )

                report_path = (
                    value.pop(
                        "_report_html_path",
                        "",
                    )
                )

                value[
                    "report_url"
                ] = (
                    self.server.register_report(
                        run_id=value[
                            "run_id"
                        ],
                        report_path=(
                            report_path
                        ),
                    )
                )

                output.append(
                    value,
                )

            self.send_json(
                {
                    "runs": output,
                }
            )
            return

        if parsed.path.startswith(
            "/reports/",
        ):
            run_id = unquote(
                parsed.path[
                    len(
                        "/reports/"
                    ):
                ]
            )

            report_path = (
                self.server.report_paths.get(
                    run_id,
                )
            )

            if report_path is None:
                self.send_error(
                    HTTPStatus.NOT_FOUND,
                )
                return

            self.send_text_file(
                report_path,
                content_type=(
                    "text/html; charset=utf-8"
                ),
            )
            return

        self.send_error(
            HTTPStatus.NOT_FOUND,
        )

    def do_POST(
        self,
    ) -> None:
        parsed = urlparse(
            self.path,
        )

        if parsed.path != "/api/review":
            self.send_error(
                HTTPStatus.NOT_FOUND,
            )
            return

        raw_length = self.headers.get(
            "Content-Length",
            "0",
        )

        try:
            content_length = int(
                raw_length,
            )

        except ValueError:
            self.send_json(
                {
                    "error": (
                        "Invalid Content-Length."
                    )
                },
                status=(
                    HTTPStatus.BAD_REQUEST
                ),
            )
            return

        if (
            content_length <= 0
            or content_length
            > 1_000_000
        ):
            self.send_json(
                {
                    "error": (
                        "Invalid request body size."
                    )
                },
                status=(
                    HTTPStatus.BAD_REQUEST
                ),
            )
            return

        raw_body = self.rfile.read(
            content_length,
        )

        try:
            payload = json.loads(
                raw_body.decode(
                    "utf-8",
                )
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            self.send_json(
                {
                    "error": (
                        "Request body must be "
                        "valid UTF-8 JSON."
                    )
                },
                status=(
                    HTTPStatus.BAD_REQUEST
                ),
            )
            return

        if not isinstance(
            payload,
            dict,
        ):
            self.send_json(
                {
                    "error": (
                        "Request body must "
                        "be a JSON object."
                    )
                },
                status=(
                    HTTPStatus.BAD_REQUEST
                ),
            )
            return

        try:
            result = run_review_request(
                context=(
                    self.server.context
                ),
                payload=payload,
            )

            result = (
                self.register_result_report(
                    result,
                )
            )

        except Exception as exc:
            self.send_json(
                {
                    "error": str(
                        exc,
                    )
                },
                status=(
                    HTTPStatus.BAD_REQUEST
                ),
            )
            return

        self.send_json(
            result,
        )

    def log_message(
        self,
        format,
        *args,
    ) -> None:
        print(
            "[web]",
            format % args,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local AgentLoop Web UI."
        ),
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_WEB_HOST,
        help=(
            "HTTP host. "
            "Default: 127.0.0.1"
        ),
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_WEB_PORT,
        help=(
            "HTTP port. Default: 8765"
        ),
    )

    parser.add_argument(
        "--no-browser",
        action="store_true",
        help=(
            "Do not automatically open "
            "the browser."
        ),
    )

    parser.add_argument(
        "--knowledge-path",
        default="",
        help=(
            "Optional knowledge-base directory "
            "used by security reviews."
        ),
    )    

    return parser


def run_from_args(
    argv: list[str] | None = None,
) -> None:
    args = build_parser().parse_args(
        argv,
    )

    if not (
        0 < args.port < 65536
    ):
        raise ValueError(
            "port must be between "
            "1 and 65535."
        )

    if not INDEX_PATH.is_file():
        raise FileNotFoundError(
            f"Web UI file not found: "
            f"{INDEX_PATH}"
        )

    server = AgentLoopWebServer(
        (
            args.host,
            args.port,
        ),
        AgentLoopWebHandler,
        knowledge_path=args.knowledge_path,
    )

    url = (
        f"http://{args.host}:"
        f"{args.port}/"
    )

    print(
        "AgentLoop Web UI"
    )

    print(
        f"Listening on {url}"
    )

    print(
        "Press Ctrl+C to stop."
    )

    if not args.no_browser:
        webbrowser.open(
            url,
        )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print(
            "\nStopping AgentLoop Web UI."
        )

    finally:
        server.server_close()


def main() -> None:
    run_from_args()


if __name__ == "__main__":
    main()