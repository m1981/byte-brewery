#!/usr/bin/env python3
import argparse
from collections import defaultdict
from .aug_common import load_json_input, extract_human_prompts, save_json_output

def group_prompts_by_conversation(prompts):
    """Group prompts by conversation ID."""
    grouped = defaultdict(list)
    for prompt in prompts:
        grouped[prompt["conversation_id"]].append(prompt)
    return grouped

def extract_meaningful_content(text):
    """
    Extract meaningful content from a prompt by stopping at technical indicators
    like code blocks, file paths, or system messages.
    Preserves original letter case and ensures non-empty output.
    """
    # Technical characters that indicate start of code/logs/errors
    technical_indicators = {'`', '|', '/', '\\', '$', '#', '>', '<', '{', '}', '[', ']', '(', ')', '.py', '.json', '.xml'}
    
    result = []
    words = text.split()
    
    for word in words:
        # Stop if we hit any technical indicator
        if any(indicator in word for indicator in technical_indicators):
            break
        
        # Only keep words with at least one alphanumeric character
        if any(c.isalnum() for c in word):
            result.append(word)  # Keep original case
    
    meaningful_content = ' '.join(result).strip()
    
    # Return original text if parsed content would be empty
    return meaningful_content if meaningful_content else text.strip()

def main():
    parser = argparse.ArgumentParser(description="Process and analyze chat prompts")
    parser.add_argument("input_file", nargs='?', default='-',
                       help="Input JSON file path (default: stdin)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()

    json_data = load_json_input(args.input_file)
    prompts = extract_human_prompts(json_data) if not isinstance(json_data, list) else json_data
    grouped_prompts = group_prompts_by_conversation(prompts)

    result = {}
    for conv_id, conv_prompts in grouped_prompts.items():
        result[conv_id] = []
        for prompt in conv_prompts:
            meaningful_content = extract_meaningful_content(prompt["prompt"])
            result[conv_id].append({
#                 "original_prompt": prompt["prompt"],
                "meaningful_content": meaningful_content,
#                 "request_id": prompt["request_id"],
#                 "timestamp": prompt.get("timestamp", "")
            })

    save_json_output(result, args.output)

if __name__ == "__main__":
    main()
