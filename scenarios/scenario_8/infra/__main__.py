import pulumi
import pulumi_aws as aws

from utils import *

import iam
import lambda_function
import s3
import ec2
import secrets

aws.Provider("default",
             default_tags=aws.ProviderDefaultTagsArgs(tags=default_tags))

config = pulumi.Config()

iam_resources = iam.create_iam_resources()
ec2_role = iam_resources['ec2_role']
dev_access_key = iam_resources['dev_access_key']
lambda_role = iam_resources['lambda_role']

lambda_function.create_lambda(iam_resources['lambda_role'])

if config.require_bool("includeAgent") == True:
    s3_agent_assets = s3.create_agent_installation()
    agent_bucket = s3_agent_assets['agent_bucket']
    agent_installer_object = s3_agent_assets['agent_installer_object']

    iam.add_agent_bucket_permission(ec2_role, agent_bucket)

    ec2.create_ec2_resources(ec2_role, dev_access_key, lambda_role,
                             agent_bucket, agent_installer_object)

secrets.create_secrets()
s3.create_s3_resources()
