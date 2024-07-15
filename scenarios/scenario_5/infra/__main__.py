import pulumi
import pulumi_aws as aws
import os
import sys
import subprocess

def read_public_key(pub_key_path):
    with open(pub_key_path, "r") as f:
        public_key = f.read().strip()

    return public_key

current = aws.get_region()

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
                    "ec2:StartInstances",
                    "ec2:StopInstances",
                    "ec2:ModifyInstanceAttribute"

                ],
                "Resource": "*"
            }
        ]
    }"""
)

sg = aws.ec2.SecurityGroup("web-sg",
    ingress=[
        {
            "protocol": "tcp",
            "fromPort": 8000,
            "toPort": 8000,
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

# User data script to be executed when the instance starts
user_data_script = """
IyEvYmluL2Jhc2gKc3VkbyBhcHQgdXBkYXRlCnN1ZG8gYXB0IGluc3RhbGwgYXdzY2xpIC15CndnZXQgLVAgL2hvbWUvdWJ1bnR1LyBodHRwczovL2xhYi1maWxlcy0wMGZmYWFiY2MuczMuYW1hem9uYXdzLmNvbS91ZWJhLWxhYi9zZXJ2ZXIucHkKc3VkbyBjaG93biB1YnVudHU6dWJ1bnR1IC9ob21lL3VidW50dS9zZXJ2ZXIucHkKd2dldCAtUCAvaG9tZS91YnVudHUvIGh0dHBzOi8vY29icmEtdG9vbC1maWxlcy5zMy5hcC1zb3V0aC0xLmFtYXpvbmF3cy5jb20vc2NlbmFyaW8tNC91c2VyZGF0YS50eHQK
"""

instance_profile = aws.iam.InstanceProfile("my-instance-profile",
    role=role.name
)

# Create an EC2 instance with user data
instance = aws.ec2.Instance("attacker",
    instance_type="t2.micro",
    ami=ubuntu_ami.id,  
    iam_instance_profile=instance_profile.name,
    security_groups=[sg.name],
    #user_data=user_data_script,
    key_name=key_pair.key_name
 
)

s3_bucket = aws.s3.Bucket("bucket",
    bucket="my-tf-test-bucket",
    acl=aws.s3.CannedAcl.PRIVATE,
    tags={
        "Name": "My bucket",
        "Environment": "Dev",
})

# Export the public IP of the EC2 instance
print("Attacker Server Public IP")
pulumi.export("Attacker Server Public IP", instance.public_ip)


print("Attacker Server Role Name")
pulumi.export("role_name", role.name)


# Export the policy name
pulumi.export("policy_name", policy.name)

# Export the security group name
pulumi.export("security_group_name", sg.name)

# Export the instance profile name
print("Attacker Server Role")
pulumi.export("Attacker Server Role", instance_profile.name)

# Export the instance ID
print("Attacker Server Instance ID")
pulumi.export("Attacker Server Instance ID", instance.id)

pulumi.export("AMI ID", ubuntu_ami.id)

pulumi.export("Subnet ID", instance.subnet_id)

pulumi.export("Key Pair Name", key_pair.key_name)

pulumi.export("Region", current.name)

pulumi.export("Bucket Name", s3_bucket.name)

