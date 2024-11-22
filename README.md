<h2 align="center">🚀 Cloud Offensive Breach and Risk Assessment (COBRA) Tool 👩‍💻</h2>

<!-- <p align="center">
<img width="300" alt="cobra" src="https://raw.githubusercontent.com/PaloAltoNetworks/cobra-tool/main/core/cobra-logo.png">
</p> -->

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Description
Cloud Offensive Breach and Risk Assessment (COBRA) is an open-source tool designed to empower users to simulate attacks within multi-cloud environments, offering a comprehensive evaluation of security controls. By automating the testing of various threat vectors including external and insider threats, lateral movement, and data exfiltration, COBRA enables organizations to gain insights into their security posture vulnerabilities. COBRA is designed to conduct simulated attacks to assess an organization's ability to detect and respond to security threats effectively.

It facilitates Proof of Concept (POC) evaluations, assesses security controls, measures maturity levels, and generates comprehensive reports, enabling organizations to enhance their cloud security resilience through lifelike threat scenarios. 


### COBRA Features

1. **Seamless Integration for POC and Tool Evaluation**: COBRA provides seamless integration for Proof of Concept (POC) and tool evaluation purposes. Whether you're exploring new cloud-native applications or evaluating existing solutions, COBRA offers a user-friendly interface and flexible deployment options to facilitate effortless testing and assessment.

2. **Comprehensive Assessment of Cloud-Native Security Posture**: Gain unparalleled insights into your organization's existing cloud-native security posture with COBRA. Our advanced assessment capabilities enable you to identify vulnerabilities, assess security controls, and pinpoint areas for improvement. By understanding your current security posture, you can proactively address gaps and strengthen your defenses against emerging threats.

3. **Benchmarking Against Industry Standards and Best Practices**: COBRA enables you to benchmark your cloud security controls against industry standards and best practices. With our comprehensive benchmarking framework, you can compare your security posture against established benchmarks, identify areas of strength and weakness, and prioritize remediation efforts accordingly.

4. **Actionable Insights and Recommendations**: COBRA goes beyond providing insights by providing a report delivering actionable recommendations tailored to your organization's specific needs. Whether it's optimizing security configurations, implementing additional controls, or enhancing incident response processes, COBRA equips you with the tools and guidance needed to bolster your cloud security defenses.

5. **Continuous Threat Simulation**:  COBRA offers a modular and templatized approach for users to easily integrate additional modules, allowing for continuous threat simulation and adaptability, by providing a flexible framework for adding modules, COBRA ensures that users can tailor their threat simulation capabilities according to evolving security needs, making it an ideal platform for continuous threat simulation.


### Key Features

- 🤖 Supports Multi-cloud AWS, Azure and GCP environment.
- 🔍 Cloud Native Contextual based analysis.
- 🌐 Seamless multi-cloud attack path simulation.
- 💻 Cloud based tool evaluation based on controls analysis.
- 📊 Generate report and provide check list to mitigate the risk

## Prerequisites

- Python 3.8+
- pip3
- Pulumi CLI [Docs](https://www.pulumi.com/docs/install/)
- Pulumi Account [here](https://www.pulumi.com/)
  - Create Pulumi Personal Access Token [Docs](https://www.pulumi.com/docs/pulumi-cloud/access-management/access-tokens/#creating-personal-access-tokens)
  - Use shell to login to Pulumi `$pulumi login` (Paste access token) [Docs](https://www.pulumi.com/docs/cli/commands/pulumi_login/)
- AWS CLI installed
  - Will use the default profile credentials unless defined with the environment variables `AWS_PROFILE` and `AWS_REGION`
  - Must have the region defined. 
- Azure CLI
- Google Cloud SDK
- kubectl [https://kubernetes.io/docs/tasks/tools/](https://kubernetes.io/docs/tasks/tools/)



## Installation

### AWS Credentials

1. Install the AWS CLI by following the
   instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html).

2. Configure your AWS credentials by running:

    ```bash
    aws configure
    ```

   You'll be prompted to enter your Access Key ID, Secret Access Key, and default region name.


### Install COBRA Tool

```
python3 -m venv ./venv
```

```
source ./venv/bin/activate
```

```
pip install -r requirements.txt
```


## Usage

```
python3 cobra.py -h
```

```
 ____ ___  ____  ____      _
 / ___/ _ \| __ )|  _ \    / \
| |  | | | |  _ \| |_) |  / _ \
| |__| |_| | |_) |  _ <  / ___ \
 \____\___/|____/|_| \_\/_/   \_\


usage: cobra.py [-h] [--simulation]
                [--scenario {cobra-scenario-1,cobra-scenario-2,cobra-scenario-3,cobra-scenario-4,cobra-scenario-5,cobra-scenario-7}]
                [--manual]
                {launch,status,destroy,post-launch}

Terminal-based option tool

positional arguments:
  {launch,status,destroy,post-launch}
                        Action to perform (launch, status, destroy)

options:
  -h, --help            show this help message and exit
  --simulation          Enable simulation mode
  --scenario {cobra-scenario-1,cobra-scenario-2,cobra-scenario-3,cobra-scenario-4,cobra-scenario-5,cobra-scenario-7}
                        Scenario selection
  --manual              Perform attack manually through post-launch
```

>>Note* ONLY RUN INTO SANDBOX ENVIRONMENT

#### Automated Simulate Cloud Attacks 

```
python3 cobra.py launch --simulation
```


```
  ____    ___    ____    ____       _
 / ___|  / _ \  | __ )  |  _ \     / \
| |     | | | | |  _ \  | |_) |   / _ \
| |___  | |_| | | |_) | |  _ <   / ___ \
 \____|  \___/  |____/  |_| \_\ /_/   \_\


Select Attack Scenario of:
1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning
2. Rest API exploit - command injection, credential exfiltration from backend lambda and privilege escalation, rogue identity creation & persistence
3. Compromising a web app living inside a GKE Pod, access pod secret, escalate privilege, take over the cluster
4. Exfiltrate EC2 role credentials using IMDSv2 with least privileged access
5. Instance takeover, abuse s3 access & perform ransomware using external KMS key
7. Container Escape & Cluster Takeover in EKS
8. Exit
Enter your choice:

```

#### Manual Attack simulation 

```
python3 cobra.py launch --simulation --manual
```

```
  ____    ___    ____    ____       _
 / ___|  / _ \  | __ )  |  _ \     / \
| |     | | | | |  _ \  | |_) |   / _ \
| |___  | |_| | | |_) | |  _ <   / ___ \
 \____|  \___/  |____/  |_| \_\ /_/   \_\


Select Attack Scenario of:
1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning
2. Rest API exploit - command injection, credential exfiltration from backend lambda and privilege escalation, rogue identity creation & persistence
3. Compromising a web app living inside a GKE Pod, access pod secret, escalate privilege, take over the cluster
4. Exfiltrate EC2 role credentials using IMDSv2 with least privileged access
5. Instance takeover, abuse s3 access & perform ransomware using external KMS key
7. Container Escape & Cluster Takeover in EKS
8. Exit
Enter your choice:

```



#### COBRA Post Launch Simulation 

```
python3 cobra.py post-launch --simulation 

```

```
  ____    ___    ____    ____       _
 / ___|  / _ \  | __ )  |  _ \     / \
| |     | | | | |  _ \  | |_) |   / _ \
| |___  | |_| | | |_) | |  _ <   / ___ \
 \____|  \___/  |____/  |_| \_\ /_/   \_\


Select Attack Scenario of:
1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning
2. Rest API exploit - command injection, credential exfiltration from backend lambda and privilege escalation, rogue identity creation & persistence
3. Compromising a web app living inside a GKE Pod, access pod secret, escalate privilege, take over the cluster
4. Exfiltrate EC2 role credentials using IMDSv2 with least privileged access
5. Instance takeover, abuse s3 access & perform ransomware using external KMS key
6. Exit
Enter your choice: 1
Select Post Simulation Task:
1. Upload file in Victim Webserver
2. Upload file in Attacker Server
3. SSH inside Victim Webserver
4. SSH inside Attacker Server
5. Execute RCE web attack
6. Perform anomalous compute provision
7. Exit
Enter your choice:

```

#### Print Infra Status 

```
python3 cobra.py status
```


```
  ____    ___    ____    ____       _    
 / ___|  / _ \  | __ )  |  _ \     / \   
| |     | | | | |  _ \  | |_) |   / _ \  
| |___  | |_| | | |_) | |  _ <   / ___ \ 
 \____|  \___/  |____/  |_| \_\ /_/   \_\
                                         

NAME            LAST UPDATE    RESOURCE COUNT  URL
cobra-scenario-1  in progress    14              https://app.pulumi.com/xxxxxx/infra/cobra-scenario-1
fdev            2 months ago   0               https://app.pulumi.com/xxxxxxxx/infra/fdev
cobra-scenario-3  5 minutes ago  4               https://app.pulumi.com/xxxxxxxx/infra/cobra-scenario-3
```


#### Destroy Simulation

```
python3 cobra.py destroy --scenario <cobra-scenario-1/cobra-scenario-2> 
```

### Current Scenarios 

1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning
2. Rest API exploit - command injection, credential exfiltration from backend lambda and privilige escalation, rogue identity creation & persistence
3. Compromising a web app living inside a GKE Pod, access pod secret, escalate privilege, take over the cluster
4. Exfiltrate EC2 role credentials using IMDSv2 with least privileged access
5. Instance takeover, abuse s3 access & perform ransomware using external KMS key
7. Container Escape & Cluster Takeover in EKS

### To Do / In Roadmap

- Azure App exploit on a function, data exfiltration from Blob storage & abusing function misconfigs to escalate privileges & leaving a backdoor IAM entity. 
- Exploiting an App on VM, exfiltration of data from Cosmos DB & possible takeover of a resource group. 
- More scenarios loading...

### Tools used
1. Torghost - [https://github.com/SusmithKrishnan/torghost](https://github.com/SusmithKrishnan/torghost)
2. Cloud Enumeration Tool - [https://github.com/NotSoSecure/cloud-service-enum](https://github.com/NotSoSecure/cloud-service-enum)


## License

This project is licensed under the Apache Version 2.0, - see the [LICENSE](./LICENSE) file for details
