<h2 align="center">🚀 Cloud Offensive Breach and Risk Assessment (COBRA) Tool 👩‍💻</h2>

<p align="center">
<img width="300" alt="cobra" src="https://raw.githubusercontent.com/PaloAltoNetworks/cobra-tool/main/core/cobra-logo.png">
</p>

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


usage: cobra.py [-h] [--simulation] [--scenario {scenario-1,scenario-2}] {aws,azure,gcp} {launch,status,destroy}

Terminal-based option tool

positional arguments:
  {aws,azure,gcp}       Cloud provider (aws, azure, gcp)
  {launch,status,destroy}
                        Action to perform (launch, status, destroy)

options:
  -h, --help            show this help message and exit
  --simulation          Enable simulation mode
  --scenario {scenario-1,scenario-2}
                        Scenario selection
```

#### Simulate AWS Scenario 

```
python3 cobra.py aws launch --simulation
```


```
  ____ ___  ____  ____      _
 / ___/ _ \| __ )|  _ \    / \
| |  | | | |  _ \| |_) |  / _ \
| |__| |_| | |_) |  _ <  / ___ \
 \____\___/|____/|_| \_\/_/   \_\


Select Attack Scenario of aws:
1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning
2. Rest API exploit - command injection, credential exfiltration from backend lambda and privilige escalation, rogue identity creation & persistence
Enter your choice:

```

#### Check Status 

```
python3 cobra.py aws status
```

#### Destroy Simulation

```
python3 cobra.py aws destroy --scenario <scenario-1/scenario-2> 
```

### Current Scenarios 

1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning
2. Rest API exploit - command injection, credential exfiltration from backend lambda and privilige escalation, rogue identity creation & persistence

### To Do / In Roadmap

3. Compromising a GKE Pod and accessing cluster secrets, taking over the cluster & escalating privileges at the Project level, possible project takeover. 
4. Azure App exploit on a function, data exfiltration from Blob storage & abusing function misconfigs to escalate privileges & leaving a backdoor IAM entity. 
5. Exploiting an App on VM, exfiltration of data from Cosmos DB & possible takeover of a resource group. 
6. More scenarios loading...

## License

This project is licensed under the Apache Version 2.0, - see the [LICENSE](./LICENSE) file for details
