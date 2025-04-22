#!/usr/bin/env python3
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessageExtractor:
    @staticmethod
    def extract_second_message(json_content: Optional[Dict[str, Any]], 
                             message_criteria: callable = lambda x: True) -> List[Optional[str]]:
        """
        Extract second message from each chat in the JSON content.
        
        Args:
            json_content (dict): JSON data containing chats
            message_criteria (callable): Optional filter function for messages
            
        Returns:
            list: List of second messages or None for chats with fewer than 2 messages
        """
        if json_content is None:
            return []
            
        second_messages = []
        for chat in json_content.get('chats', []):
            messages = chat.get('messages', [])
            filtered_messages = [
                msg.get('content') 
                for msg in messages 
                if message_criteria(msg)
            ]
            second_messages.append(filtered_messages[1] if len(filtered_messages) > 1 else None)
        return second_messages

def parse_chat_json(file_path: Path) -> Dict[str, Any]:
    """Parse JSON file containing chat data."""
    with open(file_path) as f:
        return json.load(f)

def extract_prompts(chat_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract prompts from chat data with metadata."""
    prompts = []
    for message in chat_data.get('messages', []):
        if message.get('role') == 'human':
            prompt = {
                'content': message['content'],
                'timestamp': chat_data.get('metadata', {}).get('timestamp'),
                'conversation_id': chat_data.get('metadata', {}).get('conversation_id')
            }
            prompts.append(prompt)
    return prompts

def format_prompts(prompts: List[Dict[str, Any]], 
                  format_type: str,
                  include_timestamps: bool = False,
                  include_conversation_id: bool = False) -> str:
    """Format prompts according to specified format."""
    if format_type == "json":
        return json.dumps(prompts, indent=2)
    elif format_type == "csv":
        headers = ['content']
        if include_timestamps:
            headers.append('timestamp')
        if include_conversation_id:
            headers.append('conversation_id')
            
        lines = [','.join(headers)]
        for prompt in prompts:
            values = [prompt['content']]
            if include_timestamps:
                values.append(prompt.get('timestamp', ''))
            if include_conversation_id:
                values.append(prompt.get('conversation_id', ''))
            lines.append(','.join(f'"{v}"' for v in values))
        return '\n'.join(lines)
    else:  # text format
        lines = []
        for prompt in prompts:
            lines.append(prompt['content'])
            if include_timestamps and prompt.get('timestamp'):
                lines.append(f"Timestamp: {prompt['timestamp']}")
            if include_conversation_id and prompt.get('conversation_id'):
                lines.append(f"Conversation ID: {prompt['conversation_id']}")
            lines.append('')  # blank line between prompts
        return '\n'.join(lines)

def save_output(content: str, output_file: Optional[Path]) -> None:
    """Save content to file or print to stdout."""
    if output_file:
        with open(output_file, 'w') as f:
            f.write(content)
    else:
        print(content)

def main() -> None:
    """Main function to process chat files."""
    parser = argparse.ArgumentParser(description='Extract and format chat prompts')
    parser.add_argument('input_file', type=Path, help='Input JSON file')
    parser.add_argument('--output', type=Path, help='Output file (stdout if not specified)')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text',
                      help='Output format (default: text)')
    parser.add_argument('--timestamps', action='store_true',
                      help='Include timestamps in output')
    parser.add_argument('--conversation-id', action='store_true',
                      help='Include conversation IDs in output')
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: Input file {args.input_file} does not exist", file=sys.stderr)
        sys.exit(1)
        
    try:
        chat_data = parse_chat_json(args.input_file)
        prompts = extract_prompts(chat_data)
        formatted = format_prompts(prompts, args.format, 
                                args.timestamps, args.conversation_id)
        save_output(formatted, args.output)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()