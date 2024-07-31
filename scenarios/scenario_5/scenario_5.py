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

def scenario_5_execute():
    print("-"*30)
    print(colored("Executing Scenraio 5 : Compromise instance, takover, use s3 access, perform ransomware with external kms key", color="red"))
    loading_animation()
    print("-"*30)

    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)
    
    file_path = "./core/aws-scenario-5-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))

    generate_ssh_key()

    subprocess.call("cd ./scenarios/scenario_5/infra/ && pulumi up -s aws-scenario-5 -y", shell=True)
    subprocess.call("cd ./scenarios/scenario_5/infra/ && pulumi stack -s aws-scenario-5 output --json >> ../../../core/aws-scenario-5-output.json", shell=True)

    with open("./core/aws-scenario-5-output.json", "r") as file:
        data = json.load(file)

    ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"] 
    BUCKET_NAME = data["Bucket Name"]   
    KMS_KEY = data["KMS Key"]

    sleep_duration = 80
    with tqdm(total=sleep_duration, desc="Infra coming up") as pbar:
        while sleep_duration > 0:
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval    

    #Add Webapp attack here later
    print(colored("Initiate Instance Takeover", color="red"))
    loading_animation()
    print("-"*30)

    print(colored("Access bucket & encrypt the objects using external kms key", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'echo BUCKET_NAME={BUCKET_NAME} | sudo tee -a /etc/environment && echo KMS_KEY={KMS_KEY} | sudo tee -a /etc/environment'", shell=True)
    #subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'echo $BUCKET_NAME'", shell=True)

    subprocess.call(f"ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} 'python3 attack.py'", shell=True)






