#!/usr/bin/env python3
import argparse
import sys
import os
from pathlib import Path

# Fix imports to use relative paths within the package
from .aug_extract_json import extract_json_from_xml
from .aug_extract_chats import extract_human_prompts
from .aug_common import extract_conversation_exchanges  # Update import
from .aug_process_prompts import group_prompts_by_conversation, extract_meaningful_content
from .aug_gen_schema import generate_schema
from .aug_common import save_json_output

def validate_input_file(file_path: str) -> bool:
    """Validate input XML file."""
    if not file_path:
        print("Error: Input file path is required", file=sys.stderr)
        return False
    
    path = Path(file_path)
    if not path.exists():
        print(f"Error: File '{file_path}' does not exist", file=sys.stderr)
        return False
    
    if not path.is_file():
        print(f"Error: '{file_path}' is not a file", file=sys.stderr)
        return False
    
    if path.suffix.lower() != '.xml':
        print(f"Error: File '{file_path}' is not an XML file", file=sys.stderr)
        return False
    
    return True

def validate_output_dir(dir_path: str) -> bool:
    """Validate and create output directory if needed."""
    path = Path(dir_path)
    
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        return False

def process_chat_pipeline(input_xml: str, output_dir: str) -> bool:
    """Process chat data through the pipeline with error handling."""
    try:
        # Step 1: Extract JSON from XML
        print(f"Processing '{input_xml}'...")
        print("Step 1: Extracting JSON from XML...")
        chat_data = extract_json_from_xml(input_xml)
        save_json_output(chat_data, f"{output_dir}/chat_state.json")

        # Step 2: Extract prompts
        print("Step 2: Extracting prompts...")
        prompts = extract_human_prompts(chat_data)
        if not prompts:
            print("Warning: No prompts found in chat data", file=sys.stderr)
        save_json_output(prompts, f"{output_dir}/prompts.json")

        # Step 3: Process prompts
        print("Step 3: Processing prompts...")
        grouped_prompts = group_prompts_by_conversation(prompts)
        processed_data = []  # Initialize as empty list instead of dict when no prompts
        if grouped_prompts:  # Only process if there are prompts
            processed_data = {}
            for conv_id, conv_prompts in grouped_prompts.items():
                processed_data[conv_id] = [
                    {
                        "meaningful_content": extract_meaningful_content(p["prompt"]),
                        "original_length": len(p["prompt"]),
                        "processed_length": len(extract_meaningful_content(p["prompt"]))
                    }
                    for p in conv_prompts
                ]
        save_json_output(processed_data, f"{output_dir}/analyzed_prompts.json")

        # Step 4: Generate schema
        print("Step 4: Generating schema...")
        schema = generate_schema(processed_data, "Chat Analysis Schema")
        save_json_output(schema, f"{output_dir}/schema.json")

        print("\nProcessing complete! Output files:")
        for file in Path(output_dir).glob("*.json"):
            print(f"- {file}")
        
        return True

    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        return False

def create_parser():
    """Create argument parser with all options."""
    parser = argparse.ArgumentParser(
        description="Process chat data through extraction, analysis, and schema generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aug input.xml                     # Process with default output directory
  aug input.xml -o /path/to/output  # Process with custom output directory
  aug input.xml --extract-responses <conversation_id>  # Extract responses from specific conversation
        """
    )
    parser.add_argument("input_xml", 
                       nargs="?", 
                       help="Input XML file path")
    parser.add_argument("--output-dir", "-o", 
                       default="output",
                       help="Output directory for all generated files (default: output)")
    parser.add_argument("--extract-responses",
                       help="Extract responses from specific conversation ID")
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    # Show help if no arguments provided
    if not args.input_xml:
        parser.print_help()
        sys.exit(1)

    # Validate input and output
    if not validate_input_file(args.input_xml):
        sys.exit(1)
    
    if not validate_output_dir(args.output_dir):
        sys.exit(1)

    # Extract JSON from XML
    chat_data = extract_json_from_xml(args.input_xml)
    
    # If conversation ID provided, extract exchanges
    if args.extract_responses:
        exchanges = extract_conversation_exchanges(chat_data, args.extract_responses)
        exchange_file = f"{args.output_dir}/conversation_{args.extract_responses}.md"
        with open(exchange_file, 'w', encoding='utf-8') as f:
            f.write(exchanges)
        print(f"Conversation exchanges extracted to {exchange_file}")
        sys.exit(0)

    # Run regular pipeline
    success = process_chat_pipeline(args.input_xml, args.output_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()