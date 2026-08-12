def normalize_tool_path(
    path: str,
) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string.")

    return path.replace("\\", "/")