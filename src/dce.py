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
        if env_file:  # Only parse an env_file if it's provided
            env_from_file = EnvironmentFileParser.parse(env_file)
            overwritten_vars = set(env_from_file) & set(env_vars)
            env_from_file.update(env_vars)
            for key, value in sorted(env_from_file.items()):
                overwritten = " (Overwritten)" if key in overwritten_vars else ""
                print(f"{key}={value}{overwritten}")
        print(f"Executing: {command}")

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


def determine_command_choice(service, args, user_interactions):
    commands = service['commands']
    if len(args) < 3 or args[2] not in commands:
        command_choice = user_interactions.get_user_choice(list(commands.keys()), "Select a command:")
        if not command_choice:
            print("No valid command provided.")
            sys.exit(1)
    else:
        command_choice = args[2]

    # If the command choice is itself a command group (e.g., 'build')
    if isinstance(commands[command_choice], dict) and all(
            isinstance(value, dict) for key, value in commands[command_choice].items()
    ):
        sub_commands = commands[command_choice]
        command_choice = user_interactions.get_user_choice(list(sub_commands.keys()), "Select a command:")
        command_data = sub_commands[command_choice]
    else:
        command_data = commands[command_choice]

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


def main(command_runner, config_loader, user_interactions, info_displayer):
    config = config_loader.load(CONFIG_FILE)
    service_choice = determine_service_choice(config, sys.argv, user_interactions)
    service = config['services'][service_choice]

    command_choice, command_data = determine_command_choice(service, sys.argv, user_interactions)

    env_vars, command = extract_command_data(command_data)

    if 'docker-compose' in command or isinstance(command, list) and any('docker-compose' in cmd for cmd in command):
        # Only prepend the docker-compose specifics if it's a docker-compose command
        assert 'env_file' in service and 'path' in service, "Docker-compose commands require 'env_file' and 'path'."
        full_command_or_commands = f"docker-compose --env-file {service['env_file']} -f {service['path']}/{command}"
    else:
        full_command_or_commands = command  # arbitrary commands, no adjustments needed

    info_displayer.show_info(service_choice, full_command_or_commands, service.get('env_file', ''), env_vars)
    command_runner.run(full_command_or_commands, env_vars)


if __name__ == "__main__":
    command_runner = CommandRunner()
    config_loader = ConfigLoader()
    user_interactions = UserInteractions()
    info_displayer = InfoDisplayer()
    main(command_runner, config_loader, user_interactions, info_displayer)
