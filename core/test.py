import json

with open("./core/aws-scenario-2-output.json", "r") as file:
    data = json.load(file)

API_GW_URL = data["apigateway-rest-endpoint"]
LAMBDA_ROLE_NAME = data["lambda-role-name"]

print(LAMBDA_ROLE_NAME)