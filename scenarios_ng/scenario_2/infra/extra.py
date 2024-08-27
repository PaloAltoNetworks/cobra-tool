import subprocess


def deploy_additional_resources():
    pass


def destroy_additional_resources(data):    
    LAMBDA_ROLE_NAME = data["lambda-role-name"]
    
    # TODO: consider doing programatically via boto3 vs. subprocess
    subprocess.call("aws iam detach-user-policy --user-name devops --policy-arn arn:aws:iam::aws:policy/AdministratorAccess", shell=True)
    subprocess.call("aws iam list-access-keys --user-name devops | jq -r '.AccessKeyMetadata[0].AccessKeyId' | xargs -I {} aws iam delete-access-key --user-name devops --access-key-id {}", shell=True)
    subprocess.call("aws iam delete-user --user-name devops", shell=True)

    subprocess.call("aws iam list-role-policies --role-name "+LAMBDA_ROLE_NAME+" | jq -r '.PolicyNames[]' | xargs -I {} aws iam delete-role-policy --role-name "+LAMBDA_ROLE_NAME+" --policy-name {}", shell=True)
    subprocess.call("aws iam detach-role-policy --role-name "+LAMBDA_ROLE_NAME+" --policy-arn arn:aws:iam::aws:policy/AdministratorAccess", shell=True)
