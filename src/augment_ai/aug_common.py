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
        # Use only the essential fields - avoid duplication
        request = message.get('request_message', '')
        response = message.get('response_text', '')  # Primary source
        
        if request or response:
            exchange = []
            if request:
                exchange.append(f"### User Request\n\n{request}\n")
            if response:
                exchange.append(f"### Assistant Response\n\n{clean_markdown_response(response)}\n")
            exchanges.append("\n".join(exchange))

    return "\n\n---\n\n".join(exchanges)

def clean_message_data(message_data: dict) -> dict:
    """Clean message data by removing workspace_file_chunks and other noise."""
    cleaned = message_data.copy()
    
    # Remove workspace file chunks and other verbose fields
    cleaned.pop('workspace_file_chunks', None)
    cleaned.pop('structured_output_nodes', None)  # Duplicate of response_text
    cleaned.pop('structured_request_nodes', None)  # Duplicate of request_message
    cleaned.pop('rich_text_json_repr', None)       # Another duplicate format
    
    return cleaned

def extract_human_prompts(json_data):
    """Extract all human prompts from the chat JSON data."""
    prompts = []

    for conv_id, conversation in json_data.get("conversations", {}).items():
        for message in conversation.get("chatHistory", []):
            if "request_message" in message and message["request_message"].strip():
                # Clean the message data
                cleaned_message = clean_message_data(message)
                
                prompt_data = {
                    "prompt": cleaned_message["request_message"],
                    "request_id": cleaned_message.get("request_id", ""),
                    "conversation_id": conv_id,
                    "timestamp": cleaned_message.get("timestamp", "")
                }
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

                json_data = json.loads(json_str)
                return json_data

        raise ValueError("No CHAT_STATE entry found")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise


def extract_user_prompts_markdown(json_data: dict) -> str:
    """Extract only user prompts in markdown format."""
    all_prompts = []
    
    for conv_id, conversation in json_data.get('conversations', {}).items():
        title = f"# Conversation: {conv_id}\n"
        created = conversation.get('createdAtIso', 'Unknown')
        title += f"**Created:** {created}\n\n"
        
        prompts = []
        for i, message in enumerate(conversation.get('chatHistory', []), 1):
            request = message.get('request_message', '')
            if request:
                prompts.append(f"## Prompt {i}\n\n{request}\n")
        
        if prompts:
            all_prompts.append(title + "\n".join(prompts))
    
    return "\n\n" + "="*80 + "\n\n".join(all_prompts)

def clean_chat_data(json_data: dict) -> dict:
    """Clean entire chat data structure by removing workspace_file_chunks."""
    cleaned_data = json_data.copy()
    
    total_chunks_removed = 0
    total_rich_text_removed = 0
    total_feedback_removed = 0
    
    for conv_id, conversation in cleaned_data.get('conversations', {}).items():
        # Remove feedbackStates at conversation level
        if 'feedbackStates' in conversation:
            total_feedback_removed += len(conversation['feedbackStates'])
            del conversation['feedbackStates']
        
        for message in conversation.get('chatHistory', []):
            if 'workspace_file_chunks' in message:
                chunk_count = len(message['workspace_file_chunks'])
                total_chunks_removed += chunk_count
                del message['workspace_file_chunks']
            
            if 'rich_text_json_repr' in message:
                total_rich_text_removed += 1
                del message['rich_text_json_repr']
            
            # Also clean other redundant fields
            message.pop('structured_output_nodes', None)
            message.pop('structured_request_nodes', None)
    
    if total_chunks_removed > 0 or total_rich_text_removed > 0 or total_feedback_removed > 0:
        print(f"✅ Cleaned {total_chunks_removed} workspace_file_chunks, {total_rich_text_removed} rich_text_json_repr, and {total_feedback_removed} feedbackStates from dataset")
    
    return cleaned_data
