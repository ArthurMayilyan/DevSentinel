from pathlib import Path

from agent_state import AgentState


def list_files(path: str) -> list[str]:
    base_path = Path(path)

    if not base_path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    if not base_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    return [
        str(file)
        for file in base_path.rglob("*")
        if file.is_file()
    ]


def read_file(path: str) -> str:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return file_path.read_text(encoding="utf-8")


def search_in_files(query: str, path: str) -> list[dict]:
    base_path = Path(path)

    if not base_path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    results = []

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            if query in line:
                results.append({
                    "file": str(file_path),
                    "line": line_number,
                    "text": line.strip()
                })

    return results


def write_report(state: AgentState, markdown: str) -> str:
    report_path = Path("report.md")

    report = ""
    for finding in state.findings:
        if "file" not in finding or "evidence" not in finding or "severity" not in finding:
            raise ValueError("Each finding must have file, evidence, and severity.")
        report += "In the file: " + finding["file"] + "\n"
        report += "Found evidence: " + finding["evidence"] + "\n"
        report += "Severity: " + finding["severity"] + "\n"
        report += "\n" 
    report_path.write_text(report, encoding="utf-8")
 #   report_path.write_text(markdown, encoding="utf-8")
    return str(report_path)