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
    def expand_command(command_str):
        # Simulating command expansion, replacing placeholders with test paths
        command_str = command_str.replace('$(pwd)', '/test_path')
        command_str = command_str.replace('${INSTALL_DIR}', '/test_install_dir')
        return command_str

    @staticmethod
    def handle_command_substitutions(command_str, env_vars):
        # Regex to match command substitution patterns like $(...)
        all_vars = re.findall(r'\$\{?(\w+)\}?', command_str)
        undefined_vars = []
        for var in all_vars:
            if var not in env_vars and os.getenv(var) is None:
                undefined_vars.append(var)
        if undefined_vars:
            print("Following environment variables are not defined:")
            for var in undefined_vars:
                print(f" - {var}")
            raise EnvironmentError("Undefined environment variables")
        return os.path.expandvars(command_str)

    @staticmethod
    def handle_env_vars(command_str, env_vars):
        # Update the environment with the provided env_vars
        os.environ.update(env_vars)

        # Expand the environmental variables in the command string
        return os.path.expandvars(command_str)

    @staticmethod
    def show_info(service_choice, command, env_file, env_vars):
        if env_file:
            env_from_file = EnvironmentFileParser.parse(env_file)
            os.environ.update(env_from_file)
        print("-"*60)
        print(f"\nExecuting:")
        if isinstance(command, list):
            for cmd in command:
                print(f"  {cmd}")
        else:
            print(f"  {command}")
        print()

        if isinstance(command, list):
            command_str = '\n'.join(command)
        else:
            command_str = command

        substituted_command_str = InfoDisplayer.handle_command_substitutions(command_str, env_vars)

        # Check if any custom variables are used in the command
        if re.search(r'\$\{?\w+\}?', command_str):
            expanded_command_str = InfoDisplayer.handle_env_vars(substituted_command_str, env_vars)
            print(f"Real path:")
            print(expanded_command_str)
        print("-"*60)


class CommandRunner:
    def run(self, command_or_commands, env_vars=None):
        if env_vars:
            for key, value in env_vars.items():
                os.environ[key] = value

        if isinstance(command_or_commands, list):
            for cmd in command_or_commands:
                if not self._execute_command(cmd):
                    sys.exit(1)  # Exit the script if a command fails
        else:
            if not self._execute_command(command_or_commands):
                sys.exit(1)  # Exit the script if the command fails

    @staticmethod
    def _execute_command(command):
        result = subprocess.run(command, shell=True)
        if result.returncode != 0:
            print(f"Command '{command}' failed with exit code {result.returncode}")
            return False
        return True


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
        # return f"docker-compose {env_file_argument} {path_prefix}/{cmd}" if 'docker-compose' not in cmd else cmd
        return cmd

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

