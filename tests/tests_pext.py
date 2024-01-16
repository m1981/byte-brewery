import unittest
from src.pext import ChatMessageExtractor

# Unit tests
class TestChatMessageExtractor(unittest.TestCase):

    def test_extract_second_message(self):
        # Test JSON data with two chats
        test_json_data = {
            "chats": [
            {
              "id": "42687d49-6aa7-4105-bbe5-cf10173a2af3",
              "title": "Bash: Add Directory to PATH",
              "messages": [
                {
                  "role": "system",
                  "content": "Be my helpful female advisor."
                },
                {
                  "role": "user",
                  "content": "act as bash expert"
                }
              ],
              "titleSet": "true",
              "folder": "f67b3b25-e436-4423-b160-212fe81f5e2e"
            },
            {
              "id": "b5fae9a3-c397-47a7-a88c-c9329c01bb3f",
              "title": "Tailwind CSS Contradiction Checks",
              "messages": [
                {
                  "role": "system",
                  "content": "Be my helpful female advisor."
                },
                {
                  "role": "user",
                  "content": "Act as an expert of Tailwind and CSS. "
                },
                {
                  "role": "user",
                  "content": "which tool can detect this?\n\n```\n<div class=\"min-h-screen flex flex-col flex-row\">\n    <slot />\n</div>\n```"
                },
                {
                  "role": "user",
                  "content": "what is difference between \nprettier \nand \neslint"
                }
              ],
              "titleSet": "true",
              "folder": "f67b3b25-e436-4423-b160-212fe81f5e2e"
            }
          ]
        }

        expected_output = ["act as bash expert", "Act as an expert of Tailwind and CSS. "]
        second_messages = ChatMessageExtractor.extract_second_message(test_json_data)
        self.assertEqual(second_messages, expected_output)

        # Test JSON data with one chat having only one message
        test_json_data_single_message_chat = {
            "chats": [
                {
                    "id": "chat1",
                    "messages": [
                        {"role": "user", "content": "Is anyone there?"}
                    ]
                }
            ]
        }

        expected_output_single_message = [None]  # No second message
        second_messages = ChatMessageExtractor.extract_second_message(test_json_data_single_message_chat)
        self.assertEqual(second_messages, expected_output_single_message)
