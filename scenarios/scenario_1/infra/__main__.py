import pulumi
import pulumi_aws as aws
import os
import sys
import subprocess
import pdb

def read_public_key(pub_key_path):
    # Read the public key from the file
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

# User data script to be executed when the instance starts
user_data_script = """
IyEvYmluL2Jhc2gKc3VkbyBhcHQgdXBkYXRlIC15CnN1ZG8gYXB0IGluc3RhbGwgZG9ja2VyLmlvIC15CnN1ZG8gYXB0IGluc3RhbGwgcHl0aG9uMy1waXAgLXkKc3VkbyBwaXAzIGluc3RhbGwgYXdzLWV4cG9ydC1jcmVkZW50aWFscwpzdWRvIHBpcDMgaW5zdGFsbCBhd3NjbGkKc3VkbyBzeXN0ZW1jdGwgc3RhcnQgZG9ja2VyCnN1ZG8gc3lzdGVtY3RsIGVuYWJsZSBkb2NrZXIKc3VkbyBhcHQgaW5zdGFsbCB1bnppcApzdWRvIHN5c3RlbWN0bCBzdGFydCBkb2NrZXIKc3VkbyBzeXN0ZW1jdGwgZW5hYmxlIGRvY2tlcgpzdWRvIHN5c3RlbWN0bCBzdG9wIHRvbWNhdDkuc2VydmljZQpzdWRvIGFwdCAgaW5zdGFsbCBkb2NrZXItY29tcG9zZSAteQp3Z2V0IGh0dHBzOi8vbGFiLWZpbGVzLTAwZmZhYWJjYy5zMy5hbWF6b25hd3MuY29tL3B1bHVtaS9hcHAuemlwIC1QIC9ob21lL3VidW50dS8KY2QgL2hvbWUvdWJ1bnR1LyAmJiB1bnppcCAvaG9tZS91YnVudHUvYXBwLnppcApzdWRvIGRvY2tlci1jb21wb3NlIC1mIC9ob21lL3VidW50dS9hcHAvZG9ja2VyLWNvbXBvc2UueW1sIHVwIC0tYnVpbGQgLWQKc3VkbyBkb2NrZXIgcnVuIC1kIC1wIDgwODE6ODA4MCBhbmFuZGRvY2tlcmh1Yi9zcHJpbmc0c2hlbGw6bGF0ZXN0
"""

#Attacker Machine User Script
user_data_script_1 = """
IyEvYmluL2Jhc2gKc3VkbyBhcHQgdXBkYXRlIC15CnN1ZG8gYXB0IGluc3RhbGwgcHl0aG9uMy1waXAgLXkKc3VkbyBhcHQgaW5zdGFsbCB1bnppcCAgLXkKc3VkbyBhcHQgIGluc3RhbGwgYXdzY2xpIC15CnN1ZG8gYXB0IGluc3RhbGwgZ2l0IC15CnN1ZG8gcGlwMyBpbnN0YWxsIGJzNCAKc3VkbyBhcHQgaW5zdGFsbCBqcSAteQpzdWRvIHBpcDMgaW5zdGFsbCBwYWNrYWdpbmcKCndnZXQgaHR0cHM6Ly9sYWItZmlsZXMtMDBmZmFhYmNjLnMzLmFtYXpvbmF3cy5jb20vcHVsdW1pL2V4cGxvaXQucHkgLVAgL2hvbWUvdWJ1bnR1CmNobW9kICt4IC9ob21lL3VidW50dS9leHBsb2l0LnB5CmNob3duIHVidW50dTp1YnVudHUgL2hvbWUvdWJ1bnR1L2V4cGxvaXQucHkKCndnZXQgaHR0cHM6Ly9sYWItZmlsZXMtMDBmZmFhYmNjLnMzLmFtYXpvbmF3cy5jb20vcHVsdW1pL2V4cGxvaXQuc2ggLVAgL2hvbWUvdWJ1bnR1CmNobW9kICt4IC9ob21lL3VidW50dS9leHBsb2l0LnNoCmNob3duIHVidW50dTp1YnVudHUgL2hvbWUvdWJ1bnR1L2V4cGxvaXQuc2gKCndnZXQgaHR0cHM6Ly9naXRodWIuY29tL05vdFNvU2VjdXJlL2Nsb3VkLXNlcnZpY2UtZW51bS9hcmNoaXZlL3JlZnMvaGVhZHMvbWFzdGVyLnppcAp1bnppcCBtYXN0ZXIuemlwCnBpcDMgaW5zdGFsbCBjbG91ZC1zZXJ2aWNlLWVudW0tbWFzdGVyL2F3c19zZXJ2aWNlX2VudW0vcmVxdWlyZW1lbnRzLnR4dAoKY2QgL2hvbWUvdWJ1bnR1LwpnaXQgY2xvbmUgaHR0cHM6Ly9naXRodWIuY29tL1N1c21pdGhLcmlzaG5hbi90b3JnaG9zdC5naXQKbWtkaXIgL2hvbWUvdWJ1bnR1Ly5hd3MvCnRvdWNoIC9ob21lL3VidW50dS8uYXdzL2NyZWRlbnRpYWxzCmNob3duIC1SIHVidW50dTp1YnVudHUgL2hvbWUvdWJ1bnR1Ly5hd3MvCgpjZCAvaG9tZS91YnVudHUvdG9yZ2hvc3QvCmJhc2ggYnVpbGQuc2gKc3VkbyBweXRob24zIHRvcmdob3N0LnB5IC1zCnNsZWVwIDMwCnN1ZG8gcHl0aG9uMyB0b3JnaG9zdC5weSAtcw==
"""

instance_profile = aws.iam.InstanceProfile("my-instance-profile",
    role=role.name
)

# Create an EC2 instance with user data
instance = aws.ec2.Instance("web-server",
    instance_type="t2.micro",
    ami=ubuntu_ami.id,  
    iam_instance_profile=instance_profile.name,
    security_groups=[sg.name],
    user_data=user_data_script,
    key_name=key_pair.key_name,
    tags={
        "Name": "Cobra-Webserver"
    }
)

instance1 = aws.ec2.Instance("attacker-server",
    instance_type="t2.micro",
    ami=ubuntu_ami.id, 
    security_groups=[sg.name],
    user_data=user_data_script_1,
    key_name=key_pair.key_name,
    tags={
        "Name": "Cobra-Attacker"
    }
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

