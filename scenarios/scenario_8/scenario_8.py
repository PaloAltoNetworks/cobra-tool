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


class ScenarioExecution:
    def __init__(self):
        pass

    def run_subprocess(self, cmd):
        return_code = subprocess.call(cmd, shell=True)
        if return_code != 0:
            print("Subprocess returned error, aborting...")
            exit(1)

    def scenario_8_execute(self):
        print("-"*30)
        print(colored("Executing Scenraio 8 : AWS Persistence Privileges Escalation", color="red"))
        loading_animation()
        print("-"*30)

        print(colored("Rolling out Infra", color="red"))
        loading_animation()
        print("-"*30)
        
        file_path = "./core/cobra-scenario-8-output.json"
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File '{}' found and deleted.".format(file_path))
        else:
            print("File '{}' not found.".format(file_path))

        generate_ssh_key()

        self.run_subprocess("cd ./scenarios/scenario_8/infra/ && pulumi up -s cobra-scenario-8 -y")
        self.run_subprocess("cd ./scenarios/scenario_8/infra/ && pulumi stack -s cobra-scenario-8 output --json >> ../../../core/cobra-scenario-8-output.json")

        with open("./core/cobra-scenario-8-output.json", "r") as file:
            data = json.load(file)
        
        REGION = data["Region"] 

        
