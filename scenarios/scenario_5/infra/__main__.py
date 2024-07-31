import pulumi
import pulumi_aws as aws
import os
import sys
import subprocess
from pulumi_random import RandomPet
import pulumi_synced_folder
from pulumi_aws import s3
import json

def read_public_key(pub_key_path):
    with open(pub_key_path, "r") as f:
        public_key = f.read().strip()

    return public_key

region = aws.get_region()

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
                    "s3:*"
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
IyEvYmluL2Jhc2gKc3VkbyBhcHQgdXBkYXRlIC15CnN1ZG8gYXB0IGluc3RhbGwgdW56aXAgLXkKc3VkbyBhcHQgaW5zdGFsbCBweXRob24zLXBpcCAteQpzdWRvIHBpcCBpbnN0YWxsIGJvdG8zCnN1ZG8gYXB0IGluc3RhbGwgYXdzY2xpIC15CndnZXQgLVAgL2hvbWUvdWJ1bnR1LyBodHRwczovL2NvYnJhLXRvb2wtZmlsZXMuczMuYXAtc291dGgtMS5hbWF6b25hd3MuY29tL3NjZW5hcmlvLTUvYXR0YWNrLnB5CnN1ZG8gY2hvd24gdWJ1bnR1OnVidW50dSAvaG9tZS91YnVudHUvYXR0YWNrLnB5CndnZXQgLVAgL2hvbWUvdWJ1bnR1IGh0dHBzOi8vY29icmEtdG9vbC1maWxlcy5zMy5hcC1zb3V0aC0xLmFtYXpvbmF3cy5jb20vc2NlbmFyaW8tNS9jb250YWN0LnNoCmNobW9kICt4IGNvbnRhY3Quc2gKc3VkbyBjaG93biB1YnVudHU6dWJ1bnR1IC9ob21lL3VidW50dS9jb250YWN0LnNoCg==
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
    user_data=user_data_script,
    key_name=key_pair.key_name
 
)
bucket_suffix = RandomPet("bucketSuffix", length=2)
s3_bucket = aws.s3.Bucket("bucket",
    bucket=bucket_suffix.id.apply(lambda suffix: f"my-unique-bucket-{suffix}"),
    acl=aws.s3.CannedAcl.PRIVATE,
    tags={
        "Environment": "Dev"
})

folder = pulumi_synced_folder.S3BucketFolder(
    "synced-folder",
    path="./s3_files",
    bucket_name=s3_bucket.bucket,
    acl=s3.CannedAcl.PRIVATE,
)

current = aws.get_caller_identity()
kmskey = aws.kms.Key("example",
    description="An example symmetric encryption KMS key",
    enable_key_rotation=True,
    deletion_window_in_days=20,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Id": "key-default-1",
        "Statement": [
            {
                "Sid": "Enable IAM User Permissions",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{current.account_id}:root",
                },
                "Action": "kms:*",
                "Resource": "*",
            },
            {
                "Sid": "Allow administration of the key",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::{current.account_id}:role/aws-service-role/sso.amazonaws.com/AWSServiceRoleForSSO",
                },
                "Action": [
                    "kms:ReplicateKey",
                    "kms:Create*",
                    "kms:Describe*",
                    "kms:Enable*",
                    "kms:List*",
                    "kms:Put*",
                    "kms:Update*",
                    "kms:Revoke*",
                    "kms:Disable*",
                    "kms:Get*",
                    "kms:Delete*",
                    "kms:ScheduleKeyDeletion",
                    "kms:CancelKeyDeletion",
                ],
                "Resource": "*",
            },
            {
                "Sid": "Allow use of the key",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*",
                },
                "Action": [
                    "kms:DescribeKey",
                    "kms:Encrypt",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey"
                ],
                "Resource": "*",
            },
        ],
    }))


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

pulumi.export("Region", region.name)

pulumi.export("Bucket Name", s3_bucket.bucket)

pulumi.export("KMS Key", kmskey.arn)

