import os
import pyfiglet
import time
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
from .report import gen_report
from .report import gen_report_2
from scenarios.scenario_1.scenario_1 import scenario_1_execute
from scenarios.scenario_2.scenario_2 import scenario_2_execute
from scenarios.scenario_2.scenario_2 import scenario_2_destroy
from scenarios.scenario_3.scenario_3 import scenario_3_execute

def loading_animation():
    chars = "/—\\|"
    for _ in range(10):
        for char in chars:
            print(f"\rLoading {char}", end="", flush=True)
            time.sleep(0.1)


def print_ascii_art(text):
    ascii_art = pyfiglet.figlet_format(text)
    print(colored(ascii_art, color="cyan"))

def select_cloud_provider():
    print(colored("Select Cloud Provider:", color="yellow"))
    print(colored("1. AWS", color="green")) 
    print(colored("2. Azure", color="green"))
    print(colored("3. GCP", color="green"))
    while True:
        try:
            choice = int(input(colored("Enter your choice (1/2/3): ", color="yellow")))
            if choice not in [1, 2, 3]:
                raise ValueError(colored("Invalid choice. Please enter 1, 2, or 3.", color="red"))
            return choice
        except ValueError as e:
            print(e)

def select_attack_scenario(cloud_provider):
    print(colored("Select Attack Scenario of %s:", color="yellow") % cloud_provider)
    print(colored("1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning", color="green"))
    print(colored("2. Rest API exploit - command injection, credential exfiltration from backend lambda and privilige escalation, rogue identity creation & persistence", color="green"))
    print(colored("3. Compromising a web app living inside a GKE Pod, access pod secret, escalate privilege, take over the cluster", color="green"))
    while True:
        try:
            choice = int(input(colored("Enter your choice: ", color="yellow")))
            if choice not in [1, 2, 3]:
                raise ValueError(colored("Invalid choice. Please enter 1 or 2.", color="red"))
            return choice
        except ValueError as e:
            print(e)

def get_credentials():
    while True:
        try:
            access_key = input(colored("Enter Access Key: ", color="yellow"))
            if not access_key:
                raise ValueError(colored("Access Key cannot be empty.", color="red"))
            secret_key = input(colored("Enter Secret Key: ", color="yellow"))
            if not secret_key:
                raise ValueError(colored("Secret Key cannot be empty.", color="red"))
            return access_key, secret_key
        except ValueError as e:
            print(e)

def execute_scenario(x):
    try:
        # Call the scenario function from the imported module
        if x == 1:
            scenario_1_execute()
        elif x == 2:
            scenario_2_execute()
        elif x == 3:
            scenario_3_execute()
        else: 
            print("Invalid Scenario Selected")
        print(colored("Scenario executed successfully!", color="green"))
    except Exception as e:
        print(colored("Error executing scenario:", color="red"), str(e))

def main(cloud_provider, action, simulation, scenario):
    tool_name = "C N B A S"
    print(scenario)
    print_ascii_art(tool_name)
    if cloud_provider == 'aws':
        if action == 'launch':
            if simulation is True:
                scenario_choice = select_attack_scenario(cloud_provider)
                if scenario_choice == 1:
                    # Pass the selected scenario module to execute
                    execute_scenario(1)
                elif scenario_choice == 2:
                    execute_scenario(2)
                elif scenario_choice == 3:
                    execute_scenario(3)
                    #print(colored("Scenario coming soon!", color="yellow"))
        elif action == 'status' and scenario == "scenario-1":
            subprocess.call("cd ./scenarios/scenario_1/infra/ && pulumi stack ls", shell=True)
        elif action == 'status' and scenario == "scenario-2":
            subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi stack ls", shell=True)
        elif action == 'destroy' and scenario == "scenario-1":
            subprocess.call("cd ./scenarios/scenario_1/infra && pulumi destroy", shell=True)
        elif action == 'destroy' and scenario == "scenario-2":
            scenario_2_destroy()    
        else:
            print('No options provided. --help to know more')

if __name__ == "__main__":
    main()
