import iam
import pulumi
import pulumi_aws as aws

region = aws.config.region

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

# #########################################################################
# # Create an HTTP API and attach the lambda function to it
# ##    /{proxy+} - passes all requests through to the lambda function
# ##
# #########################################################################

# http_endpoint = aws.apigatewayv2.Api("http-api-pulumi-example",
#     protocol_type="HTTP"
# )

# http_lambda_backend = aws.apigatewayv2.Integration("example",
#     api_id=http_endpoint.id,
#     integration_type="AWS_PROXY",
#     connection_type="INTERNET",
#     description="Lambda example",
#     integration_method="POST",
#     integration_uri=lambda_func.arn,
#     passthrough_behavior="WHEN_NO_MATCH"
# )

# url = http_lambda_backend.integration_uri

# http_route = aws.apigatewayv2.Route("example-route",
#     api_id=http_endpoint.id,
#     route_key="ANY /{proxy+}",
#     target=http_lambda_backend.id.apply(lambda targetUrl: "integrations/" + targetUrl)
# )

# http_stage = aws.apigatewayv2.Stage("example-stage",
#     api_id=http_endpoint.id,
#     route_settings= [
#         {
#             "route_key": http_route.route_key,
#             "throttling_burst_limit": 1,
#             "throttling_rate_limit": 0.5,
#         }
#     ],
#     auto_deploy=True
# )

# # Give permissions from API Gateway to invoke the Lambda
# http_invoke_permission = aws.lambda_.Permission("api-http-lambda-permission",
#     action="lambda:invokeFunction",
#     function=lambda_func.name,
#     principal="apigateway.amazonaws.com",
#     source_arn=http_endpoint.execution_arn.apply(lambda arn: arn + "*/*"),
# )

pulumi.export("apigateway-rest-endpoint", deployment.invoke_url.apply(lambda url: url + custom_stage_name))
#pulumi.export("apigatewayv2-http-endpoint", pulumi.Output.all(http_endpoint.api_endpoint, http_stage.name).apply(lambda values: values[0] + '/' + values[1] + '/'))