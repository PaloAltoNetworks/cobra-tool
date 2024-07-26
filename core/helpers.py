#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path, PurePath
import pyfiglet
import re
import subprocess
import re
from time import sleep
import time

from pathlib import Path, PurePath
from termcolor import colored
from time import sleep

import pyfiglet
import requests
import yaml
from tqdm import tqdm
from tqdm import tqdm
import requests
import yaml


def loading_animation():
    chars = "/—\\|"
    for _ in range(10):
        for char in chars:
            print(f"\rLoading {char}", end="", flush=True)
            time.sleep(0.1)


def print_ascii_art(text):
    ascii_art = pyfiglet.figlet_format(text)
    print(colored(ascii_art, color="cyan"))


def pbar_sleep(duration, label='Loading'):
    """"Show a progress bar while sleeping for given duration."""
    with tqdm(total=duration, desc=label) as pbar:
        # Loop until sleep_duration is reached
        while duration > 0:
            # Sleep for a shorter interval to update the progress bar
            sleep_interval = min(1, duration)
            sleep(sleep_interval)
            # Update the progress bar with the elapsed time
            pbar.update(sleep_interval)
            duration -= sleep_interval


def generate_ssh_key():
    # Define the path to save the keys
    key_path = Path(__file__).parent.parent \
        / 'files' / 'var' / 'ssh' / 'id_rsa'
    # Check if SSH key already exists
    if os.path.exists(key_path):
        print("SSH key already exists. Deleting the existing key...")
        os.remove(key_path)

    # Generate the SSH key pair
    with open(os.devnull, 'w') as devnull:
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", key_path], stdout=devnull, stderr=devnull)
    print("SSH Key Pair generated successfully!")
    return key_path, key_path + ".pub"


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


def http_request(url, method='GET', headers={}):
    resp = requests.request(method, url)
    return resp


def get_scenario_list():
    """Get a list of scenarios for selection from command line.
    """
    scenarios_path = Path(__file__).parent.parent / 'scenarios_ng'
    scenarios_list = []
    for path in Path(scenarios_path).glob('*'):
        if os.path.isdir(path):
            scenarios_list.append(PurePath(path).name)
    scenarios_list.sort()
    return scenarios_list


def get_scenarios_config():
    """Create dict containing scenario config data from every entry in
    scenarios directory (title, description, etc.)
    """
    scenarios_path = Path(__file__).parent.parent / 'scenarios_ng'
    scenarios_config = {}
    for path in Path(scenarios_path).glob('*'):
        if os.path.isdir(path):
            scenario_name = PurePath(path).name
            scenario_path = Path(scenarios_path) / scenario_name
            config_path = Path(scenario_path, '_files', 'config.yaml')
            with open(config_path, 'r') as file_:
                config = yaml.load(file_, Loader=yaml.SafeLoader)
            scenarios_config[scenario_name] = config
    return scenarios_config


def print_ascii_art(text):
    ascii_art = pyfiglet.figlet_format(text)
    print(colored(ascii_art, color="cyan"))



def slugify(s):
    """Return a slug of a string, e.g. My Example becomes my-example"""
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


def http_request(url, method='GET', data={}, headers={}):
    """Convenience method for HTTP requests"""
    resp = requests.request(method, url, data=data, headers=headers)
    return resp


def get_scenario_list():
    """Get a list of scenarios for selection from command line."""
    scenarios_path = Path(__file__).parent.parent / 'scenarios_ng'
    scenarios_list = []
    for path in Path(scenarios_path).glob('*'):
        if os.path.isdir(path):
            scenarios_list.append(PurePath(path).name)
    scenarios_list.sort()
    return scenarios_list


def get_scenarios_config():
    """Create dict containing scenario config data from every entry in
    scenarios directory (title, description, etc.)"""
    scenarios_path = Path(__file__).parent.parent / 'scenarios_ng'
    scenarios_config = {}
    for path in Path(scenarios_path).glob('*'):
        if os.path.isdir(path):
            scenario_name = PurePath(path).name
            scenario_path = Path(scenarios_path) / scenario_name
            config_path = Path(scenario_path, '_files', 'config.yaml')
            with open(config_path, 'r') as file_:
                config = yaml.load(file_, Loader=yaml.SafeLoader)
            scenarios_config[scenario_name] = config
    return scenarios_config


def get_project_root():
    return Path(__file__).parent.parent


def notify(msg):
    print("-"*30)
    print(colored(msg, color="red"))
    loading_animation()
