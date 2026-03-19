import argparse
import json
import sys
from pathlib import Path
from prompt_extractor.core import extract_user_prompts, format_to_markdown

def main():
    parser = argparse.ArgumentParser(
        description="Extract user prompts from LLM conversation JSON files."
    )
    parser.add_argument(
        "filepath",
        type=Path,
        help="Path to the JSON file containing the conversation."
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Optional output Markdown file path. If not provided, prints to stdout."
    )

    args = parser.parse_args()

    if not args.filepath.is_file():
        print(f"Error: File '{args.filepath}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file. {e}", file=sys.stderr)
        sys.exit(1)

    prompts = extract_user_prompts(data)
    markdown_output = format_to_markdown(args.filepath.name, prompts)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown_output)
        print(f"Successfully wrote prompts to {args.output}")
    else:
        print(markdown_output)

if __name__ == "__main__":
    main()