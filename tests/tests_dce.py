import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
import os

import src.dce as dce

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
            config = dce.ConfigLoader.load('./.dce.json')
            self.assertIn("backend", config["services"])
            self.assertIn("console", config["services"]["backend"]["commands"])

    def test_load_invalid_json(self):
        # Malformed JSON content
        config_content = '{"services": {"backend": { "path": "docker/backend", "env_file"'
        with patch("builtins.open", mock_open(read_data=config_content)):
            with self.assertRaises(json.JSONDecodeError):
                dce.ConfigLoader.load('./.dce.json')

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
            config = dce.ConfigLoader.load('./.dce.json')
            self.assertIsNone(config["services"]["backend"].get("commands"))

class TestEnvironmentFileParser(unittest.TestCase):
    def test_parse_valid_env(self):
        env_content = "VAR1=value1\n# Comment line\nVAR2=value2"
        with patch("builtins.open", mock_open(read_data=env_content)):
            env_dict = dce.EnvironmentFileParser.parse('fake_env_file')
            self.assertEqual(env_dict, {"VAR1": "value1", "VAR2": "value2"})

    def test_parse_empty_file(self):
        with patch("builtins.open", mock_open(read_data="")):
            env_dict = dce.EnvironmentFileParser.parse('fake_env_file')
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
            config = dce.ConfigLoader.load('./.dce.json')
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
        user_choice = dce.UserInteractions.get_user_choice(options, "Select an option:")
        self.assertEqual(user_choice, "option1")

    @patch("builtins.input")
    def test_get_user_choice_invalid(self, mock_input):
        mock_input.side_effect = ["0", "3", "2"]
        options = ["option1", "option2"]
        user_choice = dce.UserInteractions.get_user_choice(options, "Select an option:")
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
        service_choice = dce.UserInteractions.get_user_choice(service_choices, "Select a service:")
        self.assertEqual(service_choice, "backend")

        # Simulate selecting the 'build' command
        command_choice = dce.UserInteractions.get_user_choice(command_choices, "Select a command:")
        self.assertEqual(command_choice, "build")

        # Simulate selecting the 'precommit' from the nested 'build' commands
        nested_command_choice = dce.UserInteractions.get_user_choice(nested_build_choices, "Select a build command:")
        self.assertEqual(nested_command_choice, nested_build_choices[0])


class TestCommandParsing(unittest.TestCase):
    def test_single_docker_compose_command(self):
        command_config = "compose_ci.yml up --remove-orphans dev-server"
        env_vars, command = dce.extract_command_data(command_config)
        self.assertEqual(env_vars, {})
        self.assertEqual(command, "compose_ci.yml up --remove-orphans dev-server")

    def test_multiple_docker_compose_commands(self):
        command_config = {
            "commands": [
                "compose_ci.yml up --build",
                "compose_ci.yml down"
            ]
        }
        env_vars, commands = dce.extract_command_data(command_config)
        self.assertEqual(env_vars, {})
        self.assertEqual(commands, [
            "compose_ci.yml up --build",
            "compose_ci.yml down"
        ])

    def test_arbitrary_shell_command(self):
        command_config = {
            "command": "docker exec container_name echo 'Hello World'"
        }
        env_vars, command = dce.extract_command_data(command_config)
        self.assertEqual(env_vars, {})
        self.assertEqual(command, "docker exec container_name echo 'Hello World'")

    def test_command_with_environment_variables(self):
        command_config = {
            "env": {
                "MY_VARIABLE": "VALUE"
            },
            "command": "docker-compose up"
        }
        env_vars, command = dce.extract_command_data(command_config)
        self.assertEqual(env_vars, {"MY_VARIABLE": "VALUE"})
        self.assertEqual(command, "docker-compose up")

    def test_invalid_command_config(self):
        with self.assertRaises(ValueError):
            dce.extract_command_data(None)

        with self.assertRaises(ValueError):
            dce.extract_command_data(123)


class TestUtilityFunctions(unittest.TestCase):

    def test_determine_service_choice_with_arg(self):
        '''Test if the function correctly determines the service from the provided command line argument.'''
        config = {
            "services": {
                "backend": {},
                "frontend": {}
            }
        }
        args = ["utility.py", "backend"]
        service_choice = dce.determine_service_choice(config, args, dce.UserInteractions())
        self.assertEqual(service_choice, "backend")

    def test_determine_service_choice_without_arg(self):
        '''Test if the function correctly prompts the user for a choice when no argument is given.'''
        config = {
            "services": {
                "backend": {},
                "frontend": {}
            }
        }
        args = ["utility.py"]

        # Mock the user input to automatically provide a choice
        with patch('builtins.input', return_value='1'):
            service_choice = dce.determine_service_choice(config, args, dce.UserInteractions())
            self.assertEqual(service_choice, "backend")

    def test_determine_command_choice_with_arg(self):
        '''Test if the function correctly determines the command from the provided command line argument.'''
        service = {
            "commands": {
                "console": "some command",
                "down": "another command"
            }
        }
        args = ["utility.py", "backend", "console"]
        user_interactions = dce.UserInteractions()
        command_choice, command_data = dce.determine_command_choice(service, args, user_interactions)
        self.assertEqual(command_choice, "console")
        self.assertEqual(command_data, "some command")

    def test_determine_command_choice_without_arg(self):
        '''Test if the function correctly prompts the user for a choice when no command argument is given.'''
        service = {
            "commands": {
                "console": "some command",
                "down": "another command"
            }
        }
        args = ["utility.py", "backend"]

        # Mock the user input to automatically provide a choice
        with patch('builtins.input', return_value='1'):
            user_interactions = dce.UserInteractions()
            command_choice, command_data = dce.determine_command_choice(service, args, user_interactions)
            self.assertEqual(command_choice, "console")
            self.assertEqual(command_data, "some command")


class TestSubCommandHandling(unittest.TestCase):

    def setUp(self):
        self.user_interactions = dce.UserInteractions()
        self.mock_config = {
            'services': {
                'backend': {
                    'commands': {
                        'build': {
                            'development': {
                                'command': 'dev_build_command'
                            },
                            'production': {
                                'command': 'prod_build_command'
                            }
                        }
                    }
                }
            }
        }



class TestCommandSelection(unittest.TestCase):

    def test_get_command_from_args_when_present(self):
        commands = {'start': {}, 'stop': {}, 'restart': {}}
        args = ['script_name', 'service_name', 'start']
        arg_index = 2
        prompt_message = "Please select a command"

        selected_command = dce.get_command_from_args_or_prompt(commands, args, arg_index, prompt_message, None)
        self.assertEqual(selected_command, 'start')

    @patch('builtins.input', lambda *args: '3')  # '3' because 'stop' would be the third option after sorting ['restart', 'start', 'stop']
    def test_get_command_from_prompt_when_args_absent(self):
        commands = {'start': {}, 'stop': {}, 'restart': {}}
        args = ['script_name', 'service_name']
        arg_index = 2
        prompt_message = "Please select a command"

        user_interactions =  dce.UserInteractions()  # Assuming this is a correctly implemented class available in the context
        selected_command =  dce.get_command_from_args_or_prompt(commands, args, arg_index, prompt_message, user_interactions)
        self.assertEqual(selected_command, 'stop')

# Now we write a test for the determine_command_choice function
class TestDetermineCommandChoice(unittest.TestCase):

    def setUp(self):
        self.service = {
            'commands': {
                'build': {
                    'development': {'command': 'dev build'},
                    'testing': {'command': 'test build'}
                },
                'deploy': {'command': 'deploy'}
            }
        }

    def test_command_choice_directly_from_args(self):
        args = ['script_name', 'service_name', 'deploy']
        user_interactions = dce.UserInteractions()  # We will not be using this in the test

        command_choice, command_data = dce.determine_command_choice(self.service, args, user_interactions)
        self.assertEqual(command_choice, 'deploy')
        self.assertEqual(command_data, {'command': 'deploy'})

    @patch('builtins.input', side_effect=['1', '1']) # Assuming '1' corresponds to 'development' in a sorted list of subcommands ['development', 'testing']
    def test_command_choice_from_args_with_subcommand_prompt(self, mock_inputs):
        args = ['script_name', 'service_name', 'build']
        user_interactions = dce.UserInteractions()

        command_choice, command_data =  dce.determine_command_choice(self.service, args, user_interactions)
        self.assertEqual(command_choice, 'build')  # This should now be 'build' as it's the main choice
        self.assertEqual(command_data, {'command': 'dev build'})


class TestBuildFullCommand(unittest.TestCase):

    def setUp(self):
        self.service_with_docker = {
            'path': 'docker/backend',
            'env_file': 'docker/backend/env.local',
        }

    def test_non_docker_command(self):
        command = "echo Hello World"
        full_command = dce.build_full_command({}, command)
        self.assertEqual(full_command, command)

    def test_docker_compose_command(self):
        command = "compose_ci.yml up"
        expected_command = f"docker-compose --env-file {self.service_with_docker['env_file']} -f {self.service_with_docker['path']}/{command}"
        full_command = dce.build_full_command(self.service_with_docker, command)
        self.assertEqual(full_command, expected_command)

    def test_prepend_docker_compose_command_list(self):
        commands = ["compose_ci.yml up", "compose_ci.yml down"]
        expected_commands = [
            f"docker-compose --env-file {self.service_with_docker['env_file']} -f {self.service_with_docker['path']}/{cmd}"
            for cmd in commands
        ]
        full_commands = dce.build_full_command(self.service_with_docker, commands)
        self.assertEqual(full_commands, expected_commands)

    def test_skip_already_prefixed_command_list(self):
        commands = ["docker-compose --env-file custom.env up", "compose_ci.yml down"]
        expected_commands = [
            commands[0],  # The first command should remain unchanged
            f"docker-compose --env-file {self.service_with_docker['env_file']} -f {self.service_with_docker['path']}/{commands[1]}"
        ]
        full_commands = dce.build_full_command(self.service_with_docker, commands)
        self.assertEqual(full_commands, expected_commands)

class ShowInfoTestCase(unittest.TestCase):

    @patch('builtins.print')
    @patch.dict(os.environ, {'ENV_FILE': '/actual/path/to/.env', 'LARADOCK_DIR': '/var/www/laradock'}, clear=True)
    def test_show_info_with_expanded_variables(self, mock_print):
        command = ['cp -n "${ENV_FILE}" "${LARADOCK_DIR}/.env"']
        dce.InfoDisplayer.show_info(None, command, None, {})
        expanded_command = 'cp -n "/actual/path/to/.env" "/var/www/laradock/.env"'
        mock_print.assert_any_call(f"Real path:\n{expanded_command}")


    @patch('builtins.print')
    @patch.dict(os.environ, {}, clear=True)
    def test_show_info_with_undefined_variables(self, mock_print):
        command = ['cp -n "${ENV_FILE}" "${LARADOCK_DIR}/.env"']

        with self.assertRaises(EnvironmentError) as context:
            dce.InfoDisplayer.show_info(None, command, None, {})

        self.assertEqual(str(context.exception), "Undefined environment variables detected, terminating execution.")

        # Check that warnings were printed for each undefined variable
        mock_print.assert_any_call("Warning: The environment variable ENV_FILE is not defined.")
        mock_print.assert_any_call("Warning: The environment variable LARADOCK_DIR is not defined.")


if __name__ == "__main__":
    unittest.main()
