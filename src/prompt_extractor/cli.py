import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from prompt_extractor.core import build_threads, format_timeline, format_tree, parse_chunks
from prompt_extractor.html_formatter import format_html, format_prompts_list
from prompt_extractor.models import MessageNode


def _find_files(directory: Path) -> list[Path]:
    """Return all regular files directly inside directory, sorted by name."""
    return sorted(f for f in directory.iterdir() if f.is_file())


def _load_conversation(filepath: Path) -> Optional[Tuple[str, List[MessageNode], str]]:
    """Parse a file into (stem_name, nodes, filepath_str). Returns None on JSON errors."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Skipping '{filepath.name}': {type(e).__name__}", file=sys.stderr)
        return None
    return filepath.stem, parse_chunks(data), str(filepath)


def _process_file(filepath: Path, view: str) -> str:
    """Render a single file as a string in the requested view."""
    result = _load_conversation(filepath)
    if result is None:
        return ""
    name, nodes, filepath_str = result
    if view == "tree":
        return format_tree(build_threads(nodes))
    if view == "html":
        return format_html([(name, nodes)])
    if view == "prompts":
        return format_prompts_list([(name, nodes)], [filepath_str])
    return format_timeline(nodes)


def _write_output(content: str, output: Path) -> None:
    output.write_text(content, encoding="utf-8")
    print(f"Written: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Map LLM conversation branches from Google AI Studio JSON exports."
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to a file or a directory of conversation files.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help=(
            "Output path. For --view html or prompts with a directory input, provide a "
            "single .html file to get all content in one document. For timeline/"
            "tree views with a directory, provide a directory."
        ),
    )
    parser.add_argument(
        "--view",
        choices=["timeline", "tree", "html", "prompts"],
        default="timeline",
        help="Output format: timeline (default), tree, html swimlane, or prompts list.",
    )

    args = parser.parse_args()

    if args.input_path.is_dir():
        files = _find_files(args.input_path)
        if not files:
            print(f"Error: No files found in '{args.input_path}'.", file=sys.stderr)
            sys.exit(1)

        if args.view == "html":
            conversations = [r for f in files if (r := _load_conversation(f)) is not None]
            # Extract just name and nodes for html view
            result = format_html([(name, nodes) for name, nodes, _ in conversations])
            if args.output:
                _write_output(result, args.output)
            else:
                print(result)

        elif args.view == "prompts":
            conversations = [r for f in files if (r := _load_conversation(f)) is not None]
            # Extract name, nodes, and file paths for prompts view
            conv_data = [(name, nodes) for name, nodes, _ in conversations]
            file_paths = [filepath for _, _, filepath in conversations]
            result = format_prompts_list(conv_data, file_paths)
            if args.output:
                _write_output(result, args.output)
            else:
                print(result)

        else:
            if args.output:
                args.output.mkdir(parents=True, exist_ok=True)
            for f in files:
                result = _process_file(f, args.view)
                if not result:
                    continue
                if args.output:
                    _write_output(result, args.output / f.with_suffix(".md").name)
                else:
                    print(result)

    elif args.input_path.is_file():
        result = _process_file(args.input_path, args.view)
        if args.output:
            _write_output(result, args.output)
        else:
            print(result)

    else:
        print(f"Error: '{args.input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
