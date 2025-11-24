import pulumi
import pulumi_aws as aws

import iam
from utils import *


def include_agent_machine(vpc_id, subnet_id, public_key_path):
    region = aws.get_region()
    pulumi.export("Region", region.region)

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
        role=iam.ec2_role.name)

    user_data_script = pulumi.Output.format(
        """#!/bin/bash
    # 1. Install AWS CLI via Snap
    sudo snap install aws-cli --classic

    # 2. Create the .aws directory
    mkdir -p /home/ubuntu/.aws

    # 3. Write the credentials file
    # This sets up the 'default' profile using the Dev User's keys
    cat <<EOF > /home/ubuntu/.aws/credentials
    [default]
    aws_access_key_id = {0}
    aws_secret_access_key = {1}
    EOF

    # 4. Write the config file
    # This defines the region and a profile to assume the Lambda Role
    cat <<EOF > /home/ubuntu/.aws/config
    [default]
    region = {3}

    [profile lambda-role]
    role_arn = {2}
    source_profile = default
    EOF

    # 5. Update file permissions
    chown -R ubuntu:ubuntu /home/ubuntu/.aws
    chmod 600 /home/ubuntu/.aws/credentials
    chmod 600 /home/ubuntu/.aws/config

    echo "AWS CLI installed and credentials configured."
    """, iam.dev_access_key.id, iam.dev_access_key.secret, iam.lambda_role.arn,
        region.region)

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
