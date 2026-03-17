import argparse
import json
import sys

import scholartools
from scholartools.cli._fmt import exit_result


def _stage(args: argparse.Namespace) -> None:
    raw = args.json
    if raw is None:
        if not sys.stdin.isatty():
            raw = sys.stdin.read().strip()
        else:
            print(
                json.dumps({"ok": False, "data": None, "error": "argument required"}),
                file=sys.stdout,
            )
            sys.exit(1)
    try:
        ref_dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(
            json.dumps({"ok": False, "data": None, "error": str(exc)}),
            file=sys.stdout,
        )
        sys.exit(1)
    result = scholartools.stage_reference(ref_dict, file_path=args.file)
    exit_result(result, args.plain)


def _list_staged(args: argparse.Namespace) -> None:
    result = scholartools.list_staged(page=args.page)
    if args.plain and hasattr(result, "references"):
        rows = result.references
        header = f"{'citekey':<20} {'title':<40} {'authors':<30} {'year':<6}"
        lines = [header]
        for r in rows:
            title = (r.title or "")[:40]
            authors = (r.authors or "")[:30]
            year = str(r.year) if r.year else ""
            lines.append(f"{r.citekey:<20} {title:<40} {authors:<30} {year:<6}")
        print("\n".join(lines))
        sys.exit(0)
    exit_result(result, args.plain)


def _delete_staged(args: argparse.Namespace) -> None:
    result = scholartools.delete_staged(args.citekey)
    exit_result(result, args.plain)


def _merge(args: argparse.Namespace) -> None:
    omit = [k.strip() for k in args.omit.split(",")] if args.omit else None
    result = scholartools.merge(omit=omit, allow_semantic=args.allow_semantic)
    exit_result(result, args.plain)


def register(sub: argparse.ArgumentParser) -> None:
    cmds = sub.add_subparsers(dest="staging_cmd")

    p_stage = cmds.add_parser("stage")
    p_stage.add_argument("json", nargs="?", default=None)
    p_stage.add_argument("--file", default=None)
    p_stage.set_defaults(func=_stage)

    p_list = cmds.add_parser("list-staged")
    p_list.add_argument("--page", type=int, default=1)
    p_list.set_defaults(func=_list_staged)

    p_delete = cmds.add_parser("delete-staged")
    p_delete.add_argument("citekey")
    p_delete.set_defaults(func=_delete_staged)

    p_merge = cmds.add_parser("merge")
    p_merge.add_argument("--omit", default=None)
    p_merge.add_argument("--allow-semantic", action="store_true", default=False)
    p_merge.set_defaults(func=_merge)
