import pulumi
import pulumi_aws as aws


def create_lambda(lambda_role):
    lambda_func = aws.lambda_.Function(
        "lambda_function",
        name="cobra-scenario-8-lambda",
        role=lambda_role.arn,
        runtime="python3.12",
        handler="lambda_test_function.handler",
        code=pulumi.AssetArchive({".": pulumi.FileArchive("./lambda_files")}),
    )

    # --- Lambda Scheduling Logic (Every 2 Hours) ---

    # Create the Event Rule
    lambda_cloudwatch_schedule = aws.cloudwatch.EventRule(
        "lambda_cloudwatch_schedule",
        name="cobra-scenario-8-lambda-schedule",
        description="Fires every 2 hours",
        schedule_expression="rate(2 hours)",
    )

    # Target the Lambda Function
    lambda_target = aws.cloudwatch.EventTarget(
        "lambda_event_target", rule=lambda_cloudwatch_schedule.name, arn=lambda_func.arn
    )

    # Give CloudWatch Permission to Invoke the Lambda
    allow_cloudwatch = aws.lambda_.Permission(
        "allow_cloudwatch_lambda_invoke",
        action="lambda:InvokeFunction",
        function=lambda_func.name,
        principal="events.amazonaws.com",
        source_arn=lambda_cloudwatch_schedule.arn,
    )
