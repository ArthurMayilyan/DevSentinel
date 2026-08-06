from typing import Any

from task_presets import build_task_from_preset


def build_task_from_args(args: Any) -> str:
    if args.task and args.preset:
        raise ValueError("Use either --task or --preset, not both.")

    if args.task:
        return args.task

    if args.preset:
        if not args.path:
            raise ValueError("--path is required when --preset is used.")

        return build_task_from_preset(
            preset=args.preset,
            path=args.path,
            max_findings=args.max_findings,
        )

    raise ValueError("Either --task or --preset must be provided.")

