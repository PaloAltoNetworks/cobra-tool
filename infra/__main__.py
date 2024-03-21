import pulumi
import pulumi_aws as aws

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
IyEvYmluL2Jhc2gKc3VkbyBhcHQgdXBkYXRlIC15CnN1ZG8gYXB0IGluc3RhbGwgZG9ja2VyLmlvIC15CnN1ZG8gYXB0IGluc3RhbGwgcHl0aG9uMy1waXAgLXkKc3VkbyBwaXAzIGluc3RhbGwgYXdzLWV4cG9ydC1jcmVkZW50aWFscwpzdWRvIHBpcDMgaW5zdGFsbCBhd3NjbGkKc3VkbyBzeXN0ZW1jdGwgc3RhcnQgZG9ja2VyCnN1ZG8gc3lzdGVtY3RsIGVuYWJsZSBkb2NrZXIKc3VkbyBhcHQgaW5zdGFsbCB1bnppcApzdWRvIHN5c3RlbWN0bCBzdGFydCBkb2NrZXIKc3VkbyBzeXN0ZW1jdGwgZW5hYmxlIGRvY2tlcgpzdWRvIHN5c3RlbWN0bCBzdG9wIHRvbWNhdDkuc2VydmljZQpzdWRvIGFwdCAgaW5zdGFsbCBkb2NrZXItY29tcG9zZSAteQp3Z2V0IGh0dHBzOi8vbGFiLWZpbGVzLTAwZmZhYWJjYy5zMy5hbWF6b25hd3MuY29tL3B1bHVtaS92dWxuX2FwcC0yMDI0MDMyMVQwNjUxMzNaLTAwMS56aXAgLVAgL2hvbWUvdWJ1bnR1LwpjZCAvaG9tZS91YnVudHUvICYmIHVuemlwIC9ob21lL3VidW50dS92dWxuX2FwcC0yMDI0MDMyMVQwNjUxMzNaLTAwMS56aXAKc3VkbyBkb2NrZXItY29tcG9zZSAtZiAvaG9tZS91YnVudHUvdnVsbl9hcHAvZG9ja2VyLWNvbXBvc2UueW1sIHVwIC0tYnVpbGQgLWQK
"""

instance_profile = aws.iam.InstanceProfile("my-instance-profile",
    role=role.name
)

# Create an EC2 instance with user data
instance = aws.ec2.Instance("web-server",
    instance_type="t2.micro",
    ami="ami-06aa3f7caf3a30282",  # Replace with your desired AMI ID
    iam_instance_profile=instance_profile.name,
    security_groups=[sg.name],
    user_data=user_data_script
)

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

