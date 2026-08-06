import pulumi
import pulumi_aws as aws
import os
import sys
import subprocess
import pdb

# Add project root to path for global imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from core.tags import get_global_tags

GLOBAL_TAGS = get_global_tags()

def read_public_key(pub_key_path):
    # Read the public key from the file
    with open(pub_key_path, "r") as f:
        public_key = f.read().strip()

    return public_key

current = aws.get_region()

# --- VPC & Networking ---
vpc = aws.ec2.Vpc("cobra-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={**GLOBAL_TAGS, "Name": "Cobra Scenario 1 VPC"},
)

igw = aws.ec2.InternetGateway("cobra-igw",
    vpc_id=vpc.id,
    tags={**GLOBAL_TAGS, "Name": "Cobra Scenario 1 IGW"},
)

subnet = aws.ec2.Subnet("cobra-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=f"{current.name}a",
    map_public_ip_on_launch=True,
    tags={**GLOBAL_TAGS, "Name": "Cobra Scenario 1 Subnet"},
)

route_table = aws.ec2.RouteTable("cobra-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags={**GLOBAL_TAGS, "Name": "Cobra Scenario 1 RT"},
)

aws.ec2.RouteTableAssociation("cobra-rta",
    route_table_id=route_table.id,
    subnet_id=subnet.id,
)

key_pair = aws.ec2.KeyPair("my-key-pair", public_key=read_public_key("../../../id_rsa.pub"))

ubuntu_ami = aws.ec2.get_ami(
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
    owners=["099720109477"],  
    most_recent=True,

)

# Create an IAM role for EC2 instance
role = aws.iam.Role("ec2-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }"""
)

# Attach a policy to the role allowing necessary permissions
policy = aws.iam.RolePolicy("ec2-role-policy",
    role=role.name,
    policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "s3:*",
                    "cloudwatch:*",
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "iam:PassRole",
                    "iam:ListAttachedUserPolicies",
                    "iam:GetRole",
                    "iam:GetRolePolicy",
                    "ec2:DescribeInstances",
                    "ec2:CreateKeyPair",
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                    "ec2:CreateTags",
                    "iam:ListRoles",
                    "iam:ListInstanceProfiles",
                    "iam:ListAttachedRolePolicies",
                    "iam:GetPolicyVersion",
                    "iam:GetPolicy",
                    "ec2:AssociateIamInstanceProfile"
                ],
                "Resource": "*"
            }
        ]
    }"""
)

sg = aws.ec2.SecurityGroup("web-sg",
    vpc_id=vpc.id,
    ingress=[
        {
            "protocol": "tcp",
            "fromPort": 8080,
            "toPort": 8080,
            "cidrBlocks": ["0.0.0.0/0"]
        },
        {
            "protocol": "tcp",
            "fromPort": 8081,
            "toPort": 8081,
            "cidrBlocks": ["0.0.0.0/0"]
        },
         {
            "protocol": "tcp",
            "fromPort": 9001,
            "toPort": 9001,
            "cidrBlocks": ["0.0.0.0/0"]
        },
        {
            "protocol": "tcp",
            "fromPort": 80,
            "toPort": 80,
            "cidrBlocks": ["0.0.0.0/0"]
        },
        {
            "protocol": "tcp",
            "fromPort": 22,
            "toPort": 22,
            "cidrBlocks": ["0.0.0.0/0"]
        }
    ],
    egress=[{
        "protocol": "-1",
        "fromPort": 0,
        "toPort": 0,
        "cidrBlocks": ["0.0.0.0/0"]
    }]
)

# Victim Web Server user data script (plain text - Pulumi handles base64 encoding)
user_data_script = """#!/bin/bash
sudo apt update -y
sudo apt install docker.io -y
sudo apt install python3-pip -y
sudo pip3 install aws-export-credentials
sudo pip3 install awscli
sudo systemctl start docker
sudo systemctl enable docker
sudo apt install unzip -y
sudo systemctl stop tomcat9.service

# Install Docker Compose v2 plugin
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

wget https://raw.githubusercontent.com/PaloAltoNetworks/cobra-tool/refs/heads/main/scenarios/scenario_1/infra/victim-lab-files/app.zip -P /home/ubuntu/
cd /home/ubuntu/ && unzip /home/ubuntu/app.zip
sudo docker compose -f /home/ubuntu/app/docker-compose.yml up --build -d
sudo docker run -d -p 8081:8080 ananddockerhub/spring4shell:latest
"""

# Attacker Machine user data script (plain text - Pulumi handles base64 encoding)
user_data_script_1 = """#!/bin/bash
sudo apt update -y
sudo apt install python3-pip -y
sudo apt install unzip -y
sudo apt install git -y
sudo apt install jq -y
sudo apt install curl -y

# Install AWS CLI v2 (avoids botocore version conflicts with apt awscli)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
unzip -q /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install
rm -rf /tmp/aws /tmp/awscliv2.zip

# Python dependencies
sudo pip3 install bs4 packaging requests

# Download exploit scripts
wget https://raw.githubusercontent.com/PaloAltoNetworks/cobra-tool/refs/heads/main/scenarios/scenario_1/infra/attacker-lab-files/exploit.py -P /home/ubuntu
chmod +x /home/ubuntu/exploit.py
chown ubuntu:ubuntu /home/ubuntu/exploit.py

wget https://raw.githubusercontent.com/PaloAltoNetworks/cobra-tool/refs/heads/main/scenarios/scenario_1/infra/attacker-lab-files/exploit.sh -P /home/ubuntu
chmod +x /home/ubuntu/exploit.sh
chown ubuntu:ubuntu /home/ubuntu/exploit.sh

# Cloud service enumeration tool
cd /home/ubuntu/
wget https://github.com/NotSoSecure/cloud-service-enum/archive/refs/heads/master.zip
unzip master.zip
pip3 install -r cloud-service-enum-master/aws_service_enum/requirements.txt
chown -R ubuntu:ubuntu /home/ubuntu/cloud-service-enum-master

# Torghost for anonymization
git clone https://github.com/SusmithKrishnan/torghost.git
mkdir -p /home/ubuntu/.aws/
touch /home/ubuntu/.aws/credentials
chown -R ubuntu:ubuntu /home/ubuntu/.aws/

cd /home/ubuntu/torghost/
bash build.sh
sudo python3 torghost.py -s
sleep 30
sudo python3 torghost.py -s
"""

instance_profile = aws.iam.InstanceProfile("my-instance-profile",
    role=role.name
)

# Create an EC2 instance with user data
instance = aws.ec2.Instance("web-server",
    instance_type="t2.medium",
    ami=ubuntu_ami.id,
    iam_instance_profile=instance_profile.name,
    vpc_security_group_ids=[sg.id],
    subnet_id=subnet.id,
    associate_public_ip_address=True,
    user_data=user_data_script,
    key_name=key_pair.key_name,
    tags={**GLOBAL_TAGS, "Name": "Cobra-Webserver"},
)

instance1 = aws.ec2.Instance("attacker-server",
    instance_type="t2.micro",
    ami=ubuntu_ami.id,
    vpc_security_group_ids=[sg.id],
    subnet_id=subnet.id,
    associate_public_ip_address=True,
    user_data=user_data_script_1,
    key_name=key_pair.key_name,
    tags={**GLOBAL_TAGS, "Name": "Cobra-Attacker"},
)
# Export the public IP of the EC2 instance
print("Web Server Public IP")
pulumi.export("Web Server Public IP", instance.public_ip)

print("Attacker Server Public IP")
pulumi.export("Attacker Server Public IP", instance1.public_ip)

pulumi.export("role_name", role.name)

# Export the policy name
pulumi.export("policy_name", policy.name)

# Export the security group name
pulumi.export("security_group_name", sg.name)

# Export the instance profile name
pulumi.export("instance_profile_name", instance_profile.name)

# Export the instance ID
print("Web Server Instance ID")
pulumi.export("Web Server Instance ID", instance.id)

print("Attacker Server Instance ID")
pulumi.export("Attacker Server Instance ID", instance1.id)

pulumi.export("AMI ID", ubuntu_ami.id)

pulumi.export("Subnet ID", instance.subnet_id)

pulumi.export("Key Pair Name", key_pair.key_name)

pulumi.export("Region", current.name)

