import pulumi
import pulumi_aws as aws

import iam
from utils import *


def create_ec2_resources(ec2_role, dev_access_key, lambda_role, agent_bucket,
                         agent_object):
    region = aws.get_region()
    pulumi.export("Region", region.region)

    # --- Use Pulumi Config to get VPC and Subnet IDs ---
    config = pulumi.Config()

    vpc_id = config.require("vpcId")
    subnet_id = config.require("subnetId")
    public_key_path = config.require("publicKeyPath")

    key_pair = aws.ec2.KeyPair("my-key-pair",
                               key_name="cobra-scenario-8-ec2-key",
                               public_key=read_public_key(public_key_path))

    ubuntu_ami = aws.ec2.get_ami(
        most_recent=True,
        # Canonical's AWS Account ID
        owners=["099720109477"],
        filters=[
            aws.ec2.GetAmiFilterArgs(
                name="name",
                values=[
                    "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20251022"
                ]),
            aws.ec2.GetAmiFilterArgs(
                name="virtualization-type",
                values=["hvm"],
            ),
        ],
    )

    sg = aws.ec2.SecurityGroup("ec2-security-group",
                               name="cobra-scenario-8-sg",
                               vpc_id=vpc_id,
                               ingress=[{
                                   "protocol": "tcp",
                                   "fromPort": 22,
                                   "toPort": 22,
                                   "cidrBlocks": ["0.0.0.0/0"]
                               }],
                               egress=[{
                                   "protocol": "-1",
                                   "fromPort": 0,
                                   "toPort": 0,
                                   "cidrBlocks": ["0.0.0.0/0"]
                               }])

    instance_profile = aws.iam.InstanceProfile(
        "ec2-instance-profile",
        name="cobra-scenario-8-instance-profile",
        role=ec2_role.name)

    user_data_script = pulumi.Output.format(
        """#!/bin/bash
# 1. Install Dependencies
sudo snap install aws-cli --classic
sudo apt-get update
sudo apt-get install -y unzip

# 2. Download Agent
# CRITICAL: We do this BEFORE writing the specific user credentials below.
# This command uses the EC2 Instance Profile (which has S3 read access).
echo "Downloading agent from S3..."
aws s3 cp s3://{3}/{4} /home/ubuntu/agent_installer.zip

# 3. Extract & Install Agent 
echo "Extracting agent..."
unzip /home/ubuntu/agent_installer.zip -d /home/ubuntu/agent
chown -R ubuntu:ubuntu /home/ubuntu/agent
sudo mkdir -p /etc/panw
sudo cp  /home/ubuntu/agent/cortex.conf /etc/panw/
chmod +x  /home/ubuntu/agent/cortex-*.sh
sudo /home/ubuntu/agent/cortex-*.sh

# 4. Configure 'Dev User' Credentials
# Now we write the keys for the 'dev-user'. Future AWS commands run by the user
# will use these keys (which have Lambda Admin access but NO S3 access).
mkdir -p /home/ubuntu/.aws

cat <<EOF > /home/ubuntu/.aws/credentials
[default]
aws_access_key_id = {0}
aws_secret_access_key = {1}
EOF

cat <<EOF > /home/ubuntu/.aws/config
[default]
region = {5}

[profile lambda-role]
role_arn = {2}
source_profile = default
EOF

# 5. Fix permissions
chown -R ubuntu:ubuntu /home/ubuntu/.aws
chmod 600 /home/ubuntu/.aws/credentials
chmod 600 /home/ubuntu/.aws/config

echo "Setup complete."
""",
        dev_access_key.id,  # {0}
        dev_access_key.secret,  # {1}
        lambda_role.arn,  # {2}
        agent_bucket.bucket,  # {3} Bucket Name
        agent_object.key,  # {4} Object Key
        region.region  # {5}
    )

    # Create an EC2 instance with user data
    instance = aws.ec2.Instance(
        "ec2-compromised-dev-machine",
        instance_type="t2.small",
        ami=ubuntu_ami.id,
        iam_instance_profile=instance_profile.name,
        vpc_security_group_ids=[sg.id],
        subnet_id=subnet_id,
        associate_public_ip_address=True,
        key_name=key_pair.key_name,
        user_data=user_data_script,
        user_data_replace_on_change=True,
        ebs_block_devices=[
            aws.ec2.InstanceEbsBlockDeviceArgs(
                device_name=ubuntu_ami.
                root_device_name,  # Finds the root device
                encrypted=True,  # Forces encryption
                volume_type="gp3"
                # You can also specify volume_size, volume_type, etc. here
            )
        ],
        tags={
            **default_tags, "UC-OWNER": "Osher",
            "Name": "Cobra Scenario 8 - Compromised Dev Machine"
        })

    print("Exporting Server Public IP...")
    pulumi.export("Server Public IP", instance.public_ip)

    print("Exporting Server Instance ID...")
    pulumi.export("Server Instance ID", instance.id)
