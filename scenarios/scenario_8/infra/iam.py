import pulumi
import pulumi_aws as aws
import json


def create_iam_resources():
    # Create an IAM role for EC2 instance
    ec2_role = aws.iam.Role("ec2-role",
                            name="cobra-scenario-8-ec2-role",
                            assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        }""")

    # Attach a policy to the role allowing minimal logging permissions
    ec2_role_policy = aws.iam.RolePolicy(
        "ec2-role-policy",
        name="cobra-scenario-8-ec2-role-policy",
        role=ec2_role.name,
        policy="""{
    "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "InstanceLogging",
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }""")

    # Create 'dev' user
    dev_user = aws.iam.User("dev-user",
                            name="cobra-scenario-8-dev-user",
                            path="/system/")
    dev_user_arn = dev_user.arn

    # Create access key for dev
    dev_access_key = aws.iam.AccessKey("dev-access-key", user=dev_user.name)

    # Attach lambda admin permissions to dev user
    dev_user_lambda_admin = aws.iam.UserPolicyAttachment(
        "dev-lambda-admin-policy-attachment",
        user=dev_user.name,
        policy_arn="arn:aws:iam::aws:policy/AWSLambda_FullAccess")

    # Allow lambda role to be assumed by dev as well as lambda service principal
    lambda_trust_policy = pulumi.Output.json_dumps({
        "Version":
        "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": dev_user.arn,
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    })

    # Lambda role creation
    lambda_role = aws.iam.Role("lambda-role",
                               name="cobra-scenario-8-lambda-role",
                               assume_role_policy=lambda_trust_policy)

    # Lambda role's over-permissive policy
    # This allows the Lambda to assume ANY role in the account
    lambda_role_policy = aws.iam.RolePolicy(
        "lambda-role-policy",
        name="cobra-scenario-8-lambda-role-policy",
        role=lambda_role.name,
        policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "sts:AssumeRole",
                    "Resource": "*"
                }
            ]
        }""")

    # IAM Monitor over-permissive role
    iam_monitor_trust_policy = pulumi.Output.json_dumps({
        "Version":
        "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "AWS": lambda_role.arn,
            },
            "Action": "sts:AssumeRole"
        }]
    })

    iam_monitor_role = aws.iam.Role(
        "iam-monitor-role",
        assume_role_policy=iam_monitor_trust_policy,
        name="cobra-scenario-8-iam-role")

    iam_monitor_role_policy = aws.iam.RolePolicyAttachment(
        "iam-monitor-full-acceass-policy-attachment",
        role=iam_monitor_role.name,
        policy_arn="arn:aws:iam::aws:policy/IAMFullAccess")

    return {
        "ec2_role": ec2_role,
        "lambda_role": lambda_role,
        "iam_monitor_role": iam_monitor_role,
        "dev_access_key": dev_access_key
    }


def add_agent_bucket_permission(ec2_role_name, agent_bucket):
    aws.iam.RolePolicy("agent-bucket-read-policy",
                       role=ec2_role_name,
                       policy=pulumi.Output.all(
                           agent_bucket.arn).apply(lambda args: json.dumps({
                               "Version":
                               "2012-10-17",
                               "Statement": [{
                                   "Effect": "Allow",
                                   "Action": ["s3:GetObject"],
                                   "Resource": [f"{args[0]}/*"]
                               }]
                           })))
