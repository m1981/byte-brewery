#!/usr/bin/env python3
import json
import sys
from collections import defaultdict
import base64
import xml.etree.ElementTree as ET

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
