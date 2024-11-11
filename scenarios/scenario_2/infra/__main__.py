import iam
import pulumi
import pulumi_aws as aws

current = aws.get_region()
region = current.name

custom_stage_name = 'example'

lambda_func = aws.lambda_.Function("mylambda",
    role=iam.lambda_role.arn,
    runtime="python3.12",
    handler="hello.handler",
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda')
    })
)

def swagger_route_handler(arn):
    return ({
        "x-amazon-apigateway-any-method": {
            "x-amazon-apigateway-integration": {
                "uri": pulumi.Output.format('arn:aws:apigateway:{0}:lambda:path/2015-03-31/functions/{1}/invocations', region, arn),
                "passthroughBehavior": "when_no_match",
                "httpMethod": "POST",
                "type": "aws_proxy",
            },
        },
    })

rest_api = aws.apigateway.RestApi("api",
    body=pulumi.Output.json_dumps({
        "swagger": "2.0",
        "info": {"title": "api", "version": "1.0"},
        "paths": {
            "/": swagger_route_handler(lambda_func.arn),
        },
    }))

deployment = aws.apigateway.Deployment("api-deployment",
    rest_api=rest_api.id,
    stage_name="",
)

stage = aws.apigateway.Stage("api-stage",
    rest_api=rest_api.id,
    deployment=deployment.id,
    stage_name=custom_stage_name,
)

rest_invoke_permission = aws.lambda_.Permission("api-rest-lambda-permission",
    action="lambda:invokeFunction",
    function=lambda_func.name,
    principal="apigateway.amazonaws.com",
    source_arn=deployment.execution_arn.apply(lambda arn: arn + "*/*"),
)

pulumi.export("api-gateway-id", rest_api.id)
pulumi.export("apigateway-rest-endpoint", deployment.invoke_url.apply(lambda url: url + custom_stage_name))
pulumi.export("lambda-role-name", iam.lambda_role.name)
pulumi.export("lambda-func-name", lambda_func.arn)