#!/usr/bin/env python3

import json
import sys
import unittest


class ChatMessageExtractor:

    @staticmethod
    def extract_second_message(json_content, message_criteria=lambda x: True):
        second_messages = []
        for chat in json_content.get('chats', []):
            # Get the list of messages in the chat
            messages = chat.get('messages', [])
            # Check if there are at least two messages in the list
            if len(messages) > 1:
                # Get the content of the second message, apply criteria, and slice to 300 chars if it passes
                second_message = messages[1]
                if message_criteria(second_message):
                    second_messages.append(second_message.get('content', 'No content')[:300])
                else:
                    # If message doesn't meet criteria, append None or a custom value
                    second_messages.append(None)
            else:
                # If there isn't a second message, append None
                second_messages.append(None)
        return second_messages

def main(json_path, message_criteria):
    try:
        with open(json_path, 'r') as file:
            chats_data = json.load(file)

        second_messages = ChatMessageExtractor.extract_second_message(chats_data, message_criteria)

        unique_messages = {}
        for message in second_messages:
            if message is not None:
                # Standardizing to lowercase for case-insensitive comparison
                unique_messages[message] = message

        # Filter out None entries and sort the valid second messages
        valid_messages = sorted([m for m in unique_messages if m is not None])

        for message in valid_messages:
            print(message)
            print('----------------------------------')

    except Exception as e:
        print(f'An error occurred: {e}')

# Define your message criteria here
def custom_criteria(message):
    """Return True if the message meets the criteria, else False."""
    # Example criteria: Message must be from the user and contain the word 'urgent'
    content = message.get('content', '')
    return (message.get('role') == 'user' and  'Act as' in message.get('content')
    and '```' not in message.get('content')
    )





if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # If 'test' is the second argument, remove all arguments except the first
        sys.argv = sys.argv[:1]
        unittest.main()
    elif len(sys.argv) == 2:
        # Otherwise, the second argument is assumed to be the JSON file path
        json_file_path = sys.argv[1]
        main(json_file_path, custom_criteria)
    else:
        print("Prompt Extracting Tool\n"
		"----------------------------\n"
		"Usage: python script.py <path_to_json_file> | test")
        sys.exit(1)
