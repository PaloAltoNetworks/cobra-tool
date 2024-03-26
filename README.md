<h2 align="center">🚀 Cloud Native Breach and Attack Simulation (CNBAS) Tool 👩‍💻</h2>

<p align="center">
<img width="396" alt="cnbas" src="https://github.com/PaloAltoNetworks/cnbas-tool/assets/4271325/f618c9c8-4f3f-48ca-848b-c51b53e4e366">
</p>

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![support](https://img.shields.io/badge/Support%20Level-Community-yellowgreen)](./SUPPORT.md)

## Description
Cloud Native Breach and Attack Simulation (CNBAS) is an open-source tool designed to empower users to simulate attacks within multi-cloud environments, offering a comprehensive evaluation of security controls. By automating the testing of various threat vectors including external and insider threats, lateral movement, and data exfiltration, CNBAS enables organizations to gain insights into their security posture vulnerabilities. CNBAS is designed to conduct simulated attacks to assess an organization's ability to detect and respond to security threats effectively.

It facilitates Proof of Concept (POC) evaluations, assesses security controls, measures maturity levels, and generates comprehensive reports, enabling organizations to enhance their cloud security resilience through lifelike threat scenarios. 


### CNBAS Features

1. **Seamless Integration for POC and Tool Evaluation**: CNBAS provides seamless integration for Proof of Concept (POC) and tool evaluation purposes. Whether you're exploring new cloud-native applications or evaluating existing solutions, CNBAS offers a user-friendly interface and flexible deployment options to facilitate effortless testing and assessment.

2. **Comprehensive Assessment of Cloud-Native Security Posture**: Gain unparalleled insights into your organization's existing cloud-native security posture with CNBAS. Our advanced assessment capabilities enable you to identify vulnerabilities, assess security controls, and pinpoint areas for improvement. By understanding your current security posture, you can proactively address gaps and strengthen your defenses against emerging threats.

3. **Benchmarking Against Industry Standards and Best Practices**: CNBAS enables you to benchmark your cloud security controls against industry standards and best practices. With our comprehensive benchmarking framework, you can compare your security posture against established benchmarks, identify areas of strength and weakness, and prioritize remediation efforts accordingly.

4. **Actionable Insights and Recommendations**: CNBAS goes beyond providing insights by providing a report delivering actionable recommendations tailored to your organization's specific needs. Whether it's optimizing security configurations, implementing additional controls, or enhancing incident response processes, CNBAS equips you with the tools and guidance needed to bolster your cloud security defenses.

5. **Continuous Threat Simulation**:  CNBAS offers a modular and templatized approach for users to easily integrate additional modules, allowing for continuous threat simulation and adaptability, by providing a flexible framework for adding modules, CNBAS ensures that users can tailor their threat simulation capabilities according to evolving security needs, making it an ideal platform for continuous threat simulation.


### Key Features

- 🤖 Supports Multi-cloud AWS, Azure and GCP environment.
- 🔍 Cloud Native Contextual based analysis.
- 🌐 Seamless multi-cloud attack path simulation.
- 💻 Cloud based tool evaluation based on controls analysis.
- 📊 Generate report and provide check list to mitigate the risk

## Prerequisites

- Python 3.8+
- pip3
- Pulumi Account
- AWS CLI
- Azure CLI
- Google Cloud SDK


## Installation

```
python3 -m venv ./infra/venv
```

```
source ./infra/venv/bin/activate
```

```
pip install -r requirements.txt
```


## Usage

```
python3 cnbas.py -h
```

```
usage: cnbas.py [-h] [--simulation] [--scenario {scenario-1,scenario-2}] {aws,azure,gcp} {launch,status,destroy}

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
python3 cnbas.py aws launch --simulation
```


```
  ____   _   _   ____       _      ____
 / ___| | \ | | | __ )     / \    / ___|
| |     |  \| | |  _ \    / _ \   \___ \
| |___  | |\  | | |_) |  / ___ \   ___) |
 \____| |_| \_| |____/  /_/   \_\ |____/


Select Attack Scenario of aws:
1. Exploit Vulnerable Application, EC2 takeover, Credential Exfiltration & Anomalous Compute Provisioning
2. Coming Soon
Enter your choice:
```

#### Check Status 

```
python3 cnbas.py aws status
```

#### Destroy Simulation

```
python3 cnbas.py aws destroy
```

## License

This project is licensed under the Apache Version 2.0, - see the [LICENSE](./LICENSE) file for details
