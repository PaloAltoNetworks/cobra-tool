import pulumi
import pulumi_aws as aws

from utils import *

import iam
import ec2
import s3
import secrets

aws.Provider("default",
             default_tags=aws.ProviderDefaultTagsArgs(tags=default_tags))

config = pulumi.Config()

if config.require_bool("include_agent") == True:
    # --- Use Pulumi Config to get VPC and Subnet IDs ---
    vpc_id = config.require("vpcId")
    subnet_id = config.require("subnetId")
    public_key_path = config.require("publicKeyPath")

    ec2.include_agent_machine(vpc_id, subnet_id, public_key_path)

lambda_func = aws.lambda_.Function("lambda_function",
                                   name="cobra-scenario-8-lambda",
                                   role=iam.lambda_role.arn,
                                   runtime="python3.12",
                                   handler="lambda_test_function.handler",
                                   code=pulumi.AssetArchive(
                                       {'.': pulumi.FileArchive('./lambda')}))

# --- Lambda Scheduling Logic (Every 2 Hours) ---

# 1. Create the Event Rule
lambda_cloudwatch_schedule = aws.cloudwatch.EventRule(
    "lambda_cloudwatch_schedule",
    name="cobra-scenario-8-lambda-schedule",
    description="Fires every 24 hours",
    schedule_expression="rate(24 hours)")

# 2. Target the Lambda Function
lambda_target = aws.cloudwatch.EventTarget(
    "lambda_event_target",
    rule=lambda_cloudwatch_schedule.name,
    arn=lambda_func.arn)

# 3. Give CloudWatch Permission to Invoke the Lambda
allow_cloudwatch = aws.lambda_.Permission(
    "allow_cloudwatch_lambda_invoke",
    action="lambda:InvokeFunction",
    function=lambda_func.name,
    principal="events.amazonaws.com",
    source_arn=lambda_cloudwatch_schedule.arn)
