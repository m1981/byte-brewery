#!/usr/bin/env python3
import argparse
import sys
from .aug_common import load_json_input, extract_conversation_exchanges

def main():
    parser = argparse.ArgumentParser(
        description="Extract and format conversation exchanges from chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  aug-extract-responses chat_state.json <conversation_id>
  aug-extract-responses chat_state.json <conversation_id> -o conversation.md
        """
    )
    parser.add_argument("input_file", help="Input JSON file path")
    parser.add_argument("conversation_id", help="Conversation ID to extract")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    try:
        json_data = load_json_input(args.input_file)
        formatted_exchanges = extract_conversation_exchanges(json_data, args.conversation_id)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_exchanges)
            print(f"Conversation exchanges saved to {args.output}")
        else:
            print(formatted_exchanges)
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()