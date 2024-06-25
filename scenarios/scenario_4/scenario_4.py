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
from core.helpers import generate_ssh_key

def scenario_4_execute():
    print("-"*30)
    print(colored("Executing Scenraio 4 : Exfiltrate EC2 role credentials using IMDSv2 with least privileged access", color="red"))
    loading_animation()
    print("-"*30)

    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)
    
    file_path = "./core/aws-scenario-3-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))

    generate_ssh_key()

    subprocess.call("cd ./scenarios/scenario_4/infra/ && pulumi up -s aws-scenario-3 -y", shell=True)
    subprocess.call("cd ./scenarios/scenario_4/infra/ && pulumi stack -s aws-scenario-3 output --json >> ../../../core/aws-scenario-3-output.json", shell=True)

    with open("./core/aws-scenario-3-output.json", "r") as file:
        data = json.load(file)

    ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"]
    VICTIM_SERVER_PUBLIC_IP = data["Victim Server Public IP"]
    ATTACKER_SERVER_INSTANCE_ID = data["Attacker Server Instance ID"]
    VICTIM_SERVER_INSTANCE_ID = data["Victim Server Instance ID"]
    SUBNET_ID = data["Subnet ID"]
    AMI_ID = data["AMI ID"]
    KEY_PAIR_NAME = data["Key Pair Name"]
    REGION = data["Region"]

    sleep_duration = 30
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        while sleep_duration > 0:
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval

    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'cat /etc/hostname'", shell=True)

    
    
