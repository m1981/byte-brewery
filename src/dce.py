#!/usr/bin/env python3

import json
import subprocess
import os
import sys
import re

# Path to the JSON configuration file
CONFIG_FILE = './.dce.json'


class ConfigLoader:
    @staticmethod
    def load(config_path):
        with open(config_path, 'r') as json_file:
            return json.load(json_file)


class EnvironmentFileParser:
    @staticmethod
    def parse(env_file_path):
        env_dict = {}
        with open(env_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_dict[key] = value
        return env_dict


class UserInteractions:
    @staticmethod
    def get_user_choice(options, prompt):
        print(prompt)
        for index, option in enumerate(sorted(options), start=1):
            print(f"{index}. {option}")
        while True:
            choice_input = input("Enter your choice (number): ").strip()
            try:
                choice_index = int(choice_input) - 1
                if choice_index >= 0 and choice_index < len(options):
                    return sorted(options)[choice_index]
                else:
                    print("Choice out of range. Please try again.")
            except ValueError:
                print("Invalid choice. Please enter a number. Try again.")

class InfoDisplayer:
    @staticmethod
    def extract_docker_compose_action(full_command):
        # Use regex to find the action in the full command string
        match = re.search(r'\b(up|run|build|down)\b', full_command)
        return match.group(1) if match else 'Executing'

    @staticmethod
    def show_info(service_choice, command, env_file, env_vars):
        # Existing functionality to handle the env file
        if env_file:
            env_from_file = EnvironmentFileParser.parse(env_file)
            overwritten_vars = set(env_from_file) & set(env_vars)
            env_from_file.update(env_vars)
            for key, value in sorted(env_from_file.items()):
                overwritten = " (Overwritten)" if key in overwritten_vars else ""
                print(f"{key}={value}{overwritten}")

        # Printing the original command
        print(f"\nExecuting:\n{command}\n")

        # Searching and expanding the command with actual environment variables from the OS
        command_str = ' '.join(command)
        matches = re.findall(r'\$\{(.*?)\}', command_str)

        # Check each variable in the command if it is set in the environment
        undefined_vars = [var for var in matches if os.getenv(var) is None]
        for var in undefined_vars:
            print(f"Warning: The environment variable {var} is not defined.")

        expanded_command = os.path.expandvars(command_str)
        if undefined_vars:
            print(f"Real path (with undefined vars kept as placeholders):\n{expanded_command}")
        else:
            print(f"Real path:\n{expanded_command}")




class CommandRunner:
    def run(self, command_or_commands, env_vars=None):
        if env_vars:
            for key, value in env_vars.items():
                os.environ[key] = value
        if isinstance(command_or_commands, list):
            for cmd in command_or_commands:
                self._execute_command(cmd)
        else:
            self._execute_command(command_or_commands)

    @staticmethod
    def _execute_command(command):
        subprocess.run(command, shell=True)



def determine_service_choice(config, args, user_interactions):
    if len(args) < 2 or args[1] not in config['services']:
        service_choice = user_interactions.get_user_choice(config['services'], "Select a service:")
        if not service_choice:
            print("No valid service provided.")
            sys.exit(1)
    else:
        service_choice = args[1]
    return service_choice


def get_command_from_args_or_prompt(commands, args, arg_index, prompt_message, user_interactions):
    if len(args) > arg_index and args[arg_index] in commands:
        return args[arg_index]
    return user_interactions.get_user_choice(list(commands.keys()), prompt_message)

def determine_command_choice(service, args, user_interactions):
    commands = service['commands']
    command_choice = get_command_from_args_or_prompt(commands, args, 2, "Select a command:", user_interactions)

    command_data = commands[command_choice]

    # Check if selected command is a command group with sub-commands
    if isinstance(command_data, dict) and all(isinstance(value, dict) for value in command_data.values()):
        sub_commands = command_data
        sub_command_choice = get_command_from_args_or_prompt(sub_commands, args, 3, "Select a sub-command:", user_interactions)
        command_data = sub_commands[sub_command_choice]

    return command_choice, command_data



def extract_command_data(command_config):
    if isinstance(command_config, dict):
        if 'command' in command_config:
            return command_config.get('env', {}), command_config['command']
        elif 'commands' in command_config:
            return command_config.get('env', {}), command_config['commands']
        else:
            raise ValueError("Invalid command configuration found.")
    elif isinstance(command_config, str):
        # Direct command string means no additional env vars
        return {}, command_config
    else:
        raise ValueError("Command configuration must be a string or a dict.")

def build_full_command(service, command_data):
    if 'path' not in service or 'env_file' not in service:
        return command_data  # This handles non Docker-compose commands directly

    # Get service settings for Docker Compose
    path_prefix = service['path']
    env_file_argument = f"--env-file {service['env_file']} -f"

    # Helper function to prepend Docker Compose parts if necessary
    def prepend_docker_compose(cmd):
        return f"docker-compose {env_file_argument} {path_prefix}/{cmd}" if 'docker-compose' not in cmd else cmd

    # Apply Docker Compose parts to the command or commands
    if isinstance(command_data, list):
        return [prepend_docker_compose(cmd) for cmd in command_data]
    else:
        return prepend_docker_compose(command_data)



def main(command_runner, config_loader, user_interactions, info_displayer):
    config = config_loader.load(CONFIG_FILE)
    service_choice = determine_service_choice(config, sys.argv, user_interactions)
    service = config['services'][service_choice]

    command_choice, command_data = determine_command_choice(service, sys.argv, user_interactions)

    env_vars, command = extract_command_data(command_data)

    full_command_or_commands = build_full_command(service, command)

    info_displayer.show_info(service_choice, full_command_or_commands, service.get('env_file', ''), env_vars)
    command_runner.run(full_command_or_commands, env_vars)


if __name__ == "__main__":
    command_runner = CommandRunner()
    config_loader = ConfigLoader()
    print("DEBUG: sys.argv:", sys.argv)

    user_interactions = UserInteractions()
    info_displayer = InfoDisplayer()
    main(command_runner, config_loader, user_interactions, info_displayer)
