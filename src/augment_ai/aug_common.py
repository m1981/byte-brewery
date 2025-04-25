#!/usr/bin/env python3
import json
import sys
from collections import defaultdict
import base64
import xml.etree.ElementTree as ET
import re

def load_json_input(input_file):
    """Load JSON data from file or stdin."""
    try:
        if input_file == '-':
            return json.load(sys.stdin)
        else:
            with open(input_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON input", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def save_json_output(data, output_file=None):
    """Save JSON data to file or stdout."""
    output_json = json.dumps(data, indent=2)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"Data saved to {output_file}")
    else:
        print(output_json)

def clean_markdown_response(response_text: str) -> str:
    """Clean up markdown formatting in response text."""
    if not response_text:
        return ""
        
    # Replace ````mermaid path=xxx mode=xxx with ```mermaid
    response_text = re.sub(r'````mermaid.*?(\n)', '```mermaid\n', response_text)
    # Replace any remaining ```` with ```
    response_text = response_text.replace('````', '```')
    # Remove any <augment_code_snippet> tags
    response_text = re.sub(r'<augment_code_snippet.*?>', '', response_text)
    response_text = response_text.replace('</augment_code_snippet>', '')
    return response_text

def extract_conversation_responses(json_data: dict, conversation_id: str) -> str:
    """Extract and format response_text from specific conversation."""
    conversation = None
    for conv in json_data.get('conversations', {}).values():
        if conv.get('id') == conversation_id:
            conversation = conv
            break

    if not conversation:
        print(f"Error: Conversation {conversation_id} not found", file=sys.stderr)
        return ""

    responses = []
    for message in conversation.get('chatHistory', []):
        response_text = message.get('response_text', '')
        if response_text:
            responses.append(clean_markdown_response(response_text))

    return "\n\n".join(responses)

def extract_conversation_exchanges(json_data: dict, conversation_id: str) -> str:
    """Extract and format request/response pairs from specific conversation."""
    conversation = None
    for conv in json_data.get('conversations', {}).values():
        if conv.get('id') == conversation_id:
            conversation = conv
            break

    if not conversation:
        print(f"Error: Conversation {conversation_id} not found", file=sys.stderr)
        return ""

    exchanges = []
    for message in conversation.get('chatHistory', []):
        request = message.get('request_message', '')
        response = message.get('response_text', '')
        
        if request or response:
            exchange = []
            if request:
                exchange.append(f"### User Request\n\n{request}\n")
            if response:
                exchange.append(f"### Assistant Response\n\n{clean_markdown_response(response)}\n")
            exchanges.append("\n".join(exchange))

    return "\n\n---\n\n".join(exchanges)

def extract_human_prompts(json_data):
    """Extract all human prompts from the chat JSON data."""
    prompts = []

    for conv_id, conversation in json_data.get("conversations", {}).items():
        for message in conversation.get("chatHistory", []):
            if "request_message" in message and message["request_message"].strip():
                prompt_data = {
                    "prompt": message["request_message"],
                    "request_id": message.get("request_id", ""),
                    "conversation_id": conv_id,
                    "timestamp": message.get("timestamp", "")
                }

                # Try to extract timestamp from conversation if not in message
                if not prompt_data["timestamp"] and "lastInteractedAtIso" in conversation:
                    prompt_data["timestamp"] = conversation["lastInteractedAtIso"]

                prompts.append(prompt_data)

    return prompts

def extract_json_from_xml(xml_file):
    """Extract base64-encoded JSON from XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for entry in root.findall(".//entry[@key='CHAT_STATE']"):
            if 'value' in entry.attrib:
                value = entry.attrib['value']
                try:
                    decoded_bytes = base64.b64decode(value)
                    json_str = decoded_bytes.decode('utf-8')
                except:
                    json_str = value

                return json.loads(json_str)

        raise ValueError("No CHAT_STATE entry found")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise
