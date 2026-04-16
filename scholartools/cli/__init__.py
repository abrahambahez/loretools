import argparse
import importlib.metadata
import os
import sys

from scholartools.cli import extract as _extract
from scholartools.cli import files as _files
from scholartools.cli import refs as _refs
from scholartools.cli import staging as _staging

_GROUPS = ["refs", "extract", "files", "staging"]

_DESCRIPTIONS = {
    "refs": "manage references in the library",
    "extract": "extract metadata from a local file",
    "files": "manage files linked to references",
    "staging": "manage staged references before merging",
}


def _not_implemented(args: argparse.Namespace) -> None:
    print("not yet implemented", file=sys.stderr)
    sys.exit(1)


def _build_parser() -> argparse.ArgumentParser:
    try:
        version = importlib.metadata.version("scholartools")
    except importlib.metadata.PackageNotFoundError:
        version = os.environ.get("SCHT_VERSION", "unknown")

    parser = argparse.ArgumentParser(
        prog="scht",
        description="scholartools CLI",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {version}")
    parser.add_argument(
        "--plain",
        action="store_true",
        default=False,
        help="human-readable output instead of JSON",
    )

    subparsers = parser.add_subparsers(dest="group", metavar="group")

    _group_registers = {
        "refs": _refs.register,
        "extract": _extract.register,
        "files": _files.register,
        "staging": _staging.register,
    }

    for group in _GROUPS:
        sub = subparsers.add_parser(group, help=_DESCRIPTIONS[group])
        if group in _group_registers:
            _group_registers[group](sub)
        else:
            sub.set_defaults(func=_not_implemented)

    return parser


def main() -> None:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--plain", action="store_true", default=False)
    pre_args, remaining = pre.parse_known_args()

    parser = _build_parser()
    args = parser.parse_args(remaining)
    args.plain = pre_args.plain

    if args.group is None:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, "func"):
        args.func(args)
    else:
        _not_implemented(args)


if __name__ == "__main__":
    main()
