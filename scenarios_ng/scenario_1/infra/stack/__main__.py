import base64
from pathlib import Path

import pulumi
import pulumi_aws as aws


def read_public_key(pub_key_path):
    # Read the public key from the file
    with open(pub_key_path, "r") as f:
        public_key = f.read().strip()
    return public_key


# FIXME: use helper function to get files path instead of parent*5
key_path = Path(__file__).parent.parent.parent.parent.parent / 'files' / 'var' / 'ssh' / 'id_rsa.pub'
# User data script to be executed when the instance starts
# TODO: OS-independent path traversal
user_data_path = './data/user_data_1.sh'
with open(user_data_path, 'rb') as f:
    user_data_script = base64.b64encode(f.read())

# Attacker Machine User Script
user_data_path = './data/user_data_2.sh'
with open(user_data_path, 'rb') as f:
    user_data_script_1 = base64.b64encode(f.read())

# import sys;sys.exit()

current = aws.get_region()

key_pair = aws.ec2.KeyPair('my-key-pair', public_key=read_public_key(key_path))

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
role = aws.iam.Role(
    "ec2-role",
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
policy = aws.iam.RolePolicy(
    "ec2-role-policy",
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

sg = aws.ec2.SecurityGroup(
    "web-sg",
    ingress=[
        {
            "protocol": "tcp",
            "fromPort": 8080,
            "toPort": 8080,
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

instance_profile = aws.iam.InstanceProfile(
    "my-instance-profile",
    role=role.name
)

# Create an EC2 instance with user data
instance = aws.ec2.Instance(
    "web-server",
    instance_type="t2.micro",
    ami=ubuntu_ami.id,  
    iam_instance_profile=instance_profile.name,
    security_groups=[sg.name],
    user_data=user_data_script.decode(),
    tags={
        "Name": "Cobra-Webserver"
    }
)

instance1 = aws.ec2.Instance(
    "attacker-server",
    instance_type="t2.micro",
    ami=ubuntu_ami.id, 
    security_groups=[sg.name],
    user_data=user_data_script_1.decode(),
    key_name=key_pair.key_name,
    tags={
        "Name": "Cobra-Attacker"
    }
)

# Export Pulmui outputs
print("Web Server Public IP")
pulumi.export("Web Server Public IP", instance.public_ip)
print("Attacker Server Public IP")
pulumi.export("Attacker Server Public IP", instance1.public_ip)
pulumi.export("role_name", role.name)
pulumi.export("policy_name", policy.name)
pulumi.export("security_group_name", sg.name)
pulumi.export("instance_profile_name", instance_profile.name)
print("Web Server Instance ID")
pulumi.export("Web Server Instance ID", instance.id)
print("Attacker Server Instance ID")
pulumi.export("Attacker Server Instance ID", instance1.id)
pulumi.export("AMI ID", ubuntu_ami.id)
pulumi.export("Subnet ID", instance.subnet_id)
pulumi.export("Key Pair Name", key_pair.key_name)
pulumi.export("Region", current.name)
