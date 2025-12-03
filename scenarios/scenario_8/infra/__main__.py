import pulumi
import pulumi_aws as aws

from utils import *

import iam
import lambda_function
import s3
import ec2
import secrets

config = pulumi.Config()

# Make sure resources will be tagged with our default configurable tags
default_tags = config.require_object("tags")
aws.Provider("default", default_tags=aws.ProviderDefaultTagsArgs(tags=default_tags))
register_auto_tags(default_tags)

# IAM Resources
iam_resources = iam.create_iam_resources()
dev_access_key = iam_resources['dev_access_key']
lambda_role = iam_resources['lambda_role']
iam_monitor_role = iam_resources['iam_monitor_role']

pulumi.export("Dev Access Key ID", dev_access_key.id)
pulumi.export("Dev Access Key Secret", dev_access_key.secret)
pulumi.export("IAM Monitor Role ARN", iam_monitor_role.arn)

# Lambda
lambda_function.create_lambda(iam_resources['lambda_role'])
pulumi.export("Lambda Role ARN", iam_resources['lambda_role'].arn)

# Track when scenario includes agent, and add agent machine if it does
agent_included = config.require_bool("includeAgent")
pulumi.export("Agent Included", agent_included)

if agent_included == True:
    # Assets required for agent installation
    s3_agent_assets = s3.create_agent_installation()
    agent_bucket = s3_agent_assets['agent_bucket']
    agent_installer_object = s3_agent_assets['agent_installer_object']

    # Assets for the EC2 machine with the agent
    ec2_role = iam.create_ec2_role()
    iam.add_agent_bucket_permission(ec2_role, agent_bucket)
    ec2.create_ec2_compromised_machine(ec2_role, dev_access_key, lambda_role, agent_bucket, agent_installer_object)

# Secrets and S3 for impact stage
secrets.create_secrets()
s3.create_s3_resources()

# Attacker machine
ec2.create_ec2_attacker_machine()
