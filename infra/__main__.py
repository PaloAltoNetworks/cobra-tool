import pulumi
import pulumi_aws as aws

key_pair = aws.ec2.KeyPair("my-key-pair", public_key="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDNviNnByH5MaYiImlzXJ2LzGR+V4KY1SPAjQZQB/Uy6UFTtfeywltUcHWPJjMSuGKfPJe17Zw+/ny27iCzzIbVBrJlxFG54gTovYom7fZ/yvp7pCBOrSYEx0WLiMM35qatkkhrGwm51nz5oFaFhNMLcH4IVYYr7tVtD+SRtKjdtMyTjtJjvPwalPPquTCO56FP48WRbyp2UsMhoTcHg1zjyGei8xktQaYNLVuklEPOw8M28PQBg3OGFAKspRtR3SCaWZbyGugqDZKW/kU8rzB7CHwmJs5mlGEpPzXAaOkQO/R4/ihdlQUJGa4+kL1zAfs2nD/tNwWbH8A1h5f36QntRLr7540jm1xiDSyocgB8fL7hT93GYPGoB1M5mLnvejWVSMBKHtoiXzkl0FwPy79K5FpnRwm/JOYUecrA+jVtpYbkHU1U23K4HWSYzZ/2uKgUo90Z4XRoVzCAa1SJnuF1CXmG3bBQWhwjvR60Bk8cj6NfHfwdPDDdeJWCKUjtF10=")

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
    owners=["099720109477"],  # Canonical's official owner ID for Ubuntu images
    most_recent=True,
    # Uncomment and replace YOUR_REGION with the AWS region
    # opts=pulumi.InvokeOptions(region="YOUR_REGION")
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

# Create a security group allowing inbound traffic on port 8080
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
IyEvYmluL2Jhc2gKc3VkbyBhcHQgdXBkYXRlIC15CnN1ZG8gYXB0IGluc3RhbGwgZG9ja2VyLmlvIC15CnN1ZG8gYXB0IGluc3RhbGwgcHl0aG9uMy1waXAgLXkKc3VkbyBwaXAzIGluc3RhbGwgYXdzLWV4cG9ydC1jcmVkZW50aWFscwpzdWRvIHBpcDMgaW5zdGFsbCBhd3NjbGkKc3VkbyBzeXN0ZW1jdGwgc3RhcnQgZG9ja2VyCnN1ZG8gc3lzdGVtY3RsIGVuYWJsZSBkb2NrZXIKc3VkbyBhcHQgaW5zdGFsbCB1bnppcApzdWRvIHN5c3RlbWN0bCBzdGFydCBkb2NrZXIKc3VkbyBzeXN0ZW1jdGwgZW5hYmxlIGRvY2tlcgpzdWRvIHN5c3RlbWN0bCBzdG9wIHRvbWNhdDkuc2VydmljZQpzdWRvIGFwdCAgaW5zdGFsbCBkb2NrZXItY29tcG9zZSAteQp3Z2V0IGh0dHBzOi8vbGFiLWZpbGVzLTAwZmZhYWJjYy5zMy5hbWF6b25hd3MuY29tL3B1bHVtaS9hcHAuemlwIC1QIC9ob21lL3VidW50dS8KY2QgL2hvbWUvdWJ1bnR1LyAmJiB1bnppcCAvaG9tZS91YnVudHUvYXBwLnppcApzdWRvIGRvY2tlci1jb21wb3NlIC1mIC9ob21lL3VidW50dS9hcHAvZG9ja2VyLWNvbXBvc2UueW1sIHVwIC0tYnVpbGQgLWQK
"""

#Attacker Machine User Script
user_data_script_1 = """
IyEvYmluL2Jhc2gKc3VkbyBhcHQgdXBkYXRlIC15CnN1ZG8gYXB0IGluc3RhbGwgcHl0aG9uMy1waXAgLXkKc3VkbyBwaXAzIGluc3RhbGwgYXdzY2xpIC15CnN1ZG8gYXB0IGluc3RhbGwgZ2l0IC15CnN1ZG8gcGlwMyBpbnN0YWxsIGJzNCAKc3VkbyBhcHQgaW5zdGFsbCBqcSAteQpzdWRvIHBpcDMgaW5zdGFsbCBwYWNrYWdpbmcKCndnZXQgaHR0cHM6Ly9jbG91ZGxhYnNkZW1vOTkuczMuYW1hem9uYXdzLmNvbS9leHBsb2l0LnB5IC1QIC9ob21lL3VidW50dQpjaG1vZCAreCAvaG9tZS91YnVudHUvZXhwbG9pdC5weQoKZ2l0IGNsb25lIGh0dHBzOi8vZ2l0aHViLmNvbS9TdXNtaXRoS3Jpc2huYW4vdG9yZ2hvc3QuZ2l0CgpjZCB+L3Rvcmdob3N0LwpzdWRvIHB5dGhvbjMgdG9yZ2hvc3QucHkgLXMKc2xlZXAgMzAKc3VkbyBweXRob24zIHRvcmdob3N0LnB5IC1zCg=="
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
    user_data=user_data_script
)

instance1 = aws.ec2.Instance("attacker-server",
    instance_type="t2.micro",
    ami=ubuntu_ami.id, 
    security_groups=[sg.name],
    user_data=user_data_script_1,
    key_name=key_pair.key_name)


# Export the public IP of the EC2 instance
pulumi.export("public_ip", instance.public_ip)

pulumi.export("role_name", role.name)

# Export the policy name
pulumi.export("policy_name", policy.name)

# Export the security group name
pulumi.export("security_group_name", sg.name)

# Export the instance profile name
pulumi.export("instance_profile_name", instance_profile.name)

# Export the instance ID
pulumi.export("instance_id", instance.id)

