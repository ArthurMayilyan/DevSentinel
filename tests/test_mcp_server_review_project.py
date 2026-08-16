import asyncio
import json

from mcp import Client

from agent_loop_mcp_server import create_agent_loop_mcp_server
from mcp_server_context import build_agent_loop_mcp_context


def run_async(coro):
    return asyncio.run(
        coro,
    )


def extract_mcp_tool_payload(
    tool_result,
):
    if getattr(
        tool_result,
        "structured_content",
        None,
    ) is not None:
        return tool_result.structured_content

    content = getattr(
        tool_result,
        "content",
        None,
    )

    if not content:
        return None

    first_item = content[0]

    text = getattr(
        first_item,
        "text",
        None,
    )

    if text is None:
        return content

    try:
        return json.loads(
            text,
        )
    except json.JSONDecodeError:
        return text


def create_security_project(tmp_path):
    project_path = tmp_path / "project"
    project_path.mkdir()

    config_path = project_path / "config.py"
    config_path.write_text(
        'SECRET_KEY = "dev-secret"\nDEBUG = True\n',
        encoding="utf-8",
    )

    auth_path = project_path / "auth.py"
    auth_path.write_text(
        '''
def verify_token(token):
    return bool(token)

def login(username, password):
    if username == "admin" and password == "admin":
        return "token"
    return None
''',
        encoding="utf-8",
    )

    return project_path


async def call_review_project(
    project_path,
    report_path,
):
    context = build_agent_loop_mcp_context(
        report_path=str(
            report_path,
        )
    )

    mcp = create_agent_loop_mcp_server(
        context=context,
    )

    async with Client(
        mcp,
    ) as client:
        result = await client.call_tool(
            "review_project",
            {
                "project_path": str(
                    project_path,
                ),
                "profile": "security",
            },
        )

        return extract_mcp_tool_payload(
            result,
        )


def test_mcp_server_review_project_tool_runs_workflow(tmp_path):
    project_path = create_security_project(
        tmp_path,
    )

    report_path = tmp_path / "report.md"

    payload = run_async(
        call_review_project(
            project_path,
            report_path,
        )
    )

    serialized = json.dumps(
        payload,
    )

    assert "completed" in serialized
    assert "security" in serialized
    assert report_path.exists()

    report = report_path.read_text(
        encoding="utf-8",
    )

    assert "Hardcoded SECRET_KEY." in report
    assert "Hardcoded admin credentials." in report