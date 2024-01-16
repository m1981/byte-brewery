import unittest
from unittest.mock import patch, mock_open, MagicMock
import json

from src.dce import ConfigLoader, EnvironmentFileParser, UserInteractions, InfoDisplayer, CommandRunner

class TestConfigLoader(unittest.TestCase):
    def test_load_valid_config(self):
        # Assume this is the valid content of your config file
        config_content = json.dumps({
            "services": {
                "backend": {
                    "path": "docker/backend",
                    "env_file": "docker/backend/env.local",
                    "commands": {
                        "console": "compose_ci.yml run --service-ports console"
                    }
                }
            }
        })
        with patch("builtins.open", mock_open(read_data=config_content)):
            config = ConfigLoader.load('./.dce.json')
            self.assertIn("backend", config["services"])
            self.assertIn("console", config["services"]["backend"]["commands"])

    def test_load_invalid_json(self):
        # Malformed JSON content
        config_content = '{"services": {"backend": { "path": "docker/backend", "env_file"'
        with patch("builtins.open", mock_open(read_data=config_content)):
            with self.assertRaises(json.JSONDecodeError):
                ConfigLoader.load('./.dce.json')

    def test_load_missing_key(self):
        # Missing 'commands' key
        config_content = json.dumps({
            "services": {
                "backend": {
                    "path": "docker/backend",
                    "env_file": "docker/backend/env.local"
                }
            }
        })
        with patch("builtins.open", mock_open(read_data=config_content)):
            config = ConfigLoader.load('./.dce.json')
            self.assertIsNone(config["services"]["backend"].get("commands"))

class TestEnvironmentFileParser(unittest.TestCase):
    def test_parse_valid_env(self):
        env_content = "VAR1=value1\n# Comment line\nVAR2=value2"
        with patch("builtins.open", mock_open(read_data=env_content)):
            env_dict = EnvironmentFileParser.parse('fake_env_file')
            self.assertEqual(env_dict, {"VAR1": "value1", "VAR2": "value2"})

    def test_parse_empty_file(self):
        with patch("builtins.open", mock_open(read_data="")):
            env_dict = EnvironmentFileParser.parse('fake_env_file')
            self.assertEqual(env_dict, {})


class TestConfigLoaderWithNestedCommand(unittest.TestCase):
    def setUp(self):
        # This should match the structure of your reference configuration, with nested build commands
        self.test_json_content = json.dumps({
            "services": {
                "backend": {
                    "path": "docker/backend",
                    "env_file": "docker/backend/env.local",
                    "commands": {
                        "build": {
                            "development": {
                                "env": {
                                    "BUILD_TARGET": "development"
                                },
                                "command": "compose_ci_build.yml build --progress plain"
                            },
                            "testing": {
                                "env": {
                                    "BUILD_TARGET": "testing"
                                },
                                "command": "compose_ci_build.yml build --progress plain"
                            },
                            "production": {
                                "env": {
                                    "BUILD_TARGET": "production"
                                },
                                "command": "compose_ci_build.yml build --progress plain"
                            }
                        }
                    }
                }
            }
        })

    def test_load_config_with_nested_build_command(self):
        with patch("builtins.open", mock_open(read_data=self.test_json_content)):
            config = ConfigLoader.load('./.dce.json')
            backend_commands = config["services"]["backend"]["commands"]
            self.assertIn("build", backend_commands)

            # Check development build configuration
            build_dev_command = backend_commands["build"]["development"]["command"]
            build_dev_env = backend_commands["build"]["development"]["env"]
            self.assertEqual(build_dev_command, "compose_ci_build.yml build --progress plain")
            self.assertEqual(build_dev_env, {"BUILD_TARGET": "development"})

            # Check testing build configuration
            build_testing_command = backend_commands["build"]["testing"]["command"]
            build_testing_env = backend_commands["build"]["testing"]["env"]
            self.assertEqual(build_testing_command, "compose_ci_build.yml build --progress plain")
            self.assertEqual(build_testing_env, {"BUILD_TARGET": "testing"})

            # Check production build configuration
            build_prod_command = backend_commands["build"]["production"]["command"]
            build_prod_env = backend_commands["build"]["production"]["env"]
            self.assertEqual(build_prod_command, "compose_ci_build.yml build --progress plain")
            self.assertEqual(build_prod_env, {"BUILD_TARGET": "production"})


class TestUserInteractions(unittest.TestCase):
    @patch("builtins.input")
    def test_get_user_choice_valid(self, mock_input):
        mock_input.side_effect = ["1"]
        options = ["option1", "option2"]
        user_choice = UserInteractions.get_user_choice(options, "Select an option:")
        self.assertEqual(user_choice, "option1")

    @patch("builtins.input")
    def test_get_user_choice_invalid(self, mock_input):
        mock_input.side_effect = ["0", "3", "2"]
        options = ["option1", "option2"]
        user_choice = UserInteractions.get_user_choice(options, "Select an option:")
        self.assertEqual(user_choice, "option2")

    @patch('builtins.input')
    def test_get_user_choice_for_nested_command(self, mock_input):
        # Specifying each user input as a separate item in the list.
        # The number of items should match the number of times input() is called.
        mock_input.side_effect = ["1", "1", "1"]  # Select 'backend', then 'build', then 'precommit'

        service_choices = ["backend", "frontend"]
        command_choices = ["console", "down", "precommit", "tests-ut", "tests-int", "build"]
        nested_build_choices = ["precommit", "testing"]

        # Simulate selecting the 'backend' service
        service_choice = UserInteractions.get_user_choice(service_choices, "Select a service:")
        self.assertEqual(service_choice, "backend")

        # Simulate selecting the 'build' command
        command_choice = UserInteractions.get_user_choice(command_choices, "Select a command:")
        self.assertEqual(command_choice, "build")

        # Simulate selecting the 'precommit' from the nested 'build' commands
        nested_command_choice = UserInteractions.get_user_choice(nested_build_choices, "Select a build command:")
        self.assertEqual(nested_command_choice, nested_build_choices[0])


if __name__ == "__main__":
    unittest.main()
