import argparse

import loretools
from loretools.cli._fmt import exit_result
from loretools.models import Result


def _extract(args: argparse.Namespace) -> None:
    try:
        result = loretools.extract_from_file(args.file_path)
    except Exception as e:
        exit_result(Result(ok=False, error=str(e)), plain=False)
    if result.agent_extraction_needed:
        print(
            f"pdfplumber could not extract metadata from {result.file_path}. "
            "Pass the file to your AI assistant for vision-based extraction."
        )
    exit_result(result, plain=False)


def register(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("file_path")
    sub.set_defaults(func=_extract)
