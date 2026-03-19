import argparse
import json
import sys
from pathlib import Path

from prompt_extractor.core import build_threads, format_timeline, format_tree, parse_chunks


def _find_files(directory: Path) -> list[Path]:
    """Return all regular files directly inside directory, sorted by name."""
    return sorted(f for f in directory.iterdir() if f.is_file())


def _process_file(filepath: Path, view: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{filepath}'. {e}", file=sys.stderr)
        return ""

    nodes = parse_chunks(data)
    if view == "tree":
        return format_tree(build_threads(nodes))
    return format_timeline(nodes)


def main():
    parser = argparse.ArgumentParser(
        description="Map LLM conversation branches from Google AI Studio JSON exports."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to a JSON file or a directory of JSON files.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output path. For a directory input this must also be a directory.",
    )
    parser.add_argument(
        "--view",
        choices=["timeline", "tree"],
        default="timeline",
        help="Output format: timeline (default) or tree.",
    )

    args = parser.parse_args()

    if args.input_path.is_dir():
        json_files = _find_files(args.input_path)
        if not json_files:
            print(f"Error: No files found in '{args.input_path}'.", file=sys.stderr)
            sys.exit(1)

        if args.output:
            args.output.mkdir(parents=True, exist_ok=True)

        for json_file in json_files:
            result = _process_file(json_file, args.view)
            if not result:
                continue
            if args.output:
                out_path = args.output / json_file.with_suffix(".md").name
                out_path.write_text(result, encoding="utf-8")
                print(f"Written: {out_path}")
            else:
                print(result)

    elif args.input_path.is_file():
        result = _process_file(args.input_path, args.view)
        if args.output:
            args.output.write_text(result, encoding="utf-8")
            print(f"Written: {args.output}")
        else:
            print(result)

    else:
        print(f"Error: '{args.input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
