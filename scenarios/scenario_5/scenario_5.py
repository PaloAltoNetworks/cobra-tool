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

