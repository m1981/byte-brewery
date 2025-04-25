#!/usr/bin/env python3
import argparse
from .aug_common import load_json_input, extract_conversation_responses

def main():
    parser = argparse.ArgumentParser(
        description="Extract and format response_text from chat conversations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aug-extract-responses chat_state.json <conversation_id>
  aug-extract-responses chat_state.json <conversation_id> -o readme_section.md
        """
    )
    parser.add_argument("input_file", help="Input JSON file path")
    parser.add_argument("conversation_id", help="Conversation ID to extract")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    try:
        json_data = load_json_input(args.input_file)
        formatted_response = extract_conversation_responses(json_data, args.conversation_id)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_response)
            print(f"Responses saved to {args.output}")
        else:
            print(formatted_response)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()