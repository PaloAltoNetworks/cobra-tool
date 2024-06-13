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

def loading_animation():
    chars = "/—\\|"
    for _ in range(10):
        for char in chars:
            print(f"\rLoading {char}", end="", flush=True)
            time.sleep(0.1)



    

    print("-"*30)
    print(colored("Executing Scenraio 1 : Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning ", color="red"))
    generate_ssh_key()
    loading_animation()
    print("-"*30)
    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call("pwd", shell=True)
    file_path = "./core/aws-scenario-1-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))
    subprocess.call("cd ./infra/scenario-1/ && pulumi up -s aws-scenario-1 -y", shell=True)
    subprocess.call("cd ./infra/scenario-1/ && pulumi stack -s aws-scenario-1 output --json >> ../../core/aws-scenario-1-output.json", shell=True)
    
    print("-"*30)
    print(colored("Bringing up the Vulnerable Application", color="red"))
    loading_animation()

    # Use tqdm as a context manager to create the progress bar
    sleep_duration = 300
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        # Loop until sleep_duration is reached
        while sleep_duration > 0:
            # Sleep for a shorter interval to update the progress bar
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
            # Update the progress bar with the elapsed time
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval


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
    while True:
        try:
            choice = int(input(colored("Enter your choice: ", color="yellow")))
            if choice not in [1, 2]:
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
                    #print(colored("Scenario coming soon!", color="yellow"))
        elif action == 'status' and scenario == "scenario-1":
            subprocess.call("cd ./scenarios/scenario_1/infra/ && pulumi stack ls", shell=True)
        elif action == 'status' and scenario == "scenario-2":
            subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi stack ls", shell=True)
        elif action == 'destroy' and scenario == "scenario-1":
            subprocess.call("cd ./scenarios/scenario_1/infra && pulumi destroy", shell=True)
        elif action == 'destroy' and scenario == "scenario-2":
            subprocess.call("cd ./scenarios/scenario_2/infra && pulumi destroy", shell=True)    
        else:
            print('No options provided. --help to know more')

if __name__ == "__main__":
    main()
