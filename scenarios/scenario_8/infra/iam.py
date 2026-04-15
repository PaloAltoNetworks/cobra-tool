import pulumi
import pulumi_aws as aws
import pulumi_random
import json


def create_ec2_role():
    # Create an IAM role for EC2 instance
    ec2_role = aws.iam.Role(
        "ec2-role",
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
        }""",
    )

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
        }""",
    )

    return ec2_role


def create_iam_resources():
    config = pulumi.Config()
    user_prefix = config.get("userPrefix") or ""

    # Create RandomInteger for dev user suffix
    dev_user_suffix = pulumi_random.RandomInteger(
        "dev-user-suffix",
        min=0,
        max=1000
    )

    # Create 'dev' user
    dev_user = aws.iam.User(
        "dev-user",
        name=dev_user_suffix.result.apply(
            lambda n: f"{user_prefix}-cobra-scenario-8-developer-user--{n}" if user_prefix else f"cobra-scenario-8-developer-user--{n}"
        ),
    )
    dev_user_arn = dev_user.arn

    # Create access key for dev
    dev_access_key = aws.iam.AccessKey("dev-access-key", user=dev_user.name)

    # Attach lambda admin permissions to dev user
    dev_user_lambda_admin = aws.iam.UserPolicyAttachment(
        "dev-lambda-admin-policy-attachment",
        user=dev_user.name,
        policy_arn="arn:aws:iam::aws:policy/AWSLambda_FullAccess",
    )

    # Allow lambda role to be assumed by dev as well as lambda service principal
    lambda_trust_policy = pulumi.Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": dev_user.arn,
                        "Service": "lambda.amazonaws.com",
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    )

    # Lambda role creation
    lambda_role = aws.iam.Role(
        "lambda-role",
        name="cobra-scenario-8-lambda-role",
        assume_role_policy=lambda_trust_policy,
    )

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
        }""",
    )

    # IAM Monitor over-permissive role
    iam_monitor_trust_policy = pulumi.Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": lambda_role.arn,
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    )

    # Create RandomInteger for IAM monitor role suffix
    iam_monitor_suffix = pulumi_random.RandomInteger(
        "iam-monitor-suffix",
        min=0,
        max=1000
    )

    iam_monitor_role = aws.iam.Role(
        "iam-monitor-role",
        assume_role_policy=iam_monitor_trust_policy,
        name=iam_monitor_suffix.result.apply(lambda n: f"cobra-scenario-8-iam-monitoring-{n}-role"),  # Randomized to avoid skewing the analytics baselines with recurrent executions
    )

    iam_monitor_role_policy = aws.iam.RolePolicyAttachment(
        "iam-monitor-full-access-policy-attachment",
        role=iam_monitor_role.name,
        policy_arn="arn:aws:iam::aws:policy/AdministratorAccess",
    )

    return {
        "lambda_role": lambda_role,
        "iam_monitor_role": iam_monitor_role,
        "dev_access_key": dev_access_key,
        "user_prefix": user_prefix,
    }


def add_agent_bucket_permission(ec2_role_name, agent_bucket):
    aws.iam.RolePolicy(
        "agent-bucket-read-policy",
        role=ec2_role_name,
        policy=pulumi.Output.all(agent_bucket.arn).apply(
            lambda args: json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["s3:GetObject"],
                            "Resource": [f"{args[0]}/*"],
                        }
                    ],
                }
            )
        ),
    )
