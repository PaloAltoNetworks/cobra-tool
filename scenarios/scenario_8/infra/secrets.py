import json

import pulumi_aws as aws


def create_secrets():
    demo_secret_string = aws.secretsmanager.Secret(
        "secret-string",
        name="Cobra-8-Secret-String",
        recovery_window_in_days=0,
        description="A very well kept secret.")
    aws.secretsmanager.SecretVersion("secret-string-version",
                                     secret_id=demo_secret_string.id,
                                     secret_string="VerySecure!")

    demo_secret_map = aws.secretsmanager.Secret(
        "secret-map",
        name="Cobra-8-Secret-Map",
        recovery_window_in_days=0,
        description="Another well kept secret.")
    aws.secretsmanager.SecretVersion("secret-map-version",
                                     secret_id=demo_secret_map.id,
                                     secret_string=json.dumps({
                                         "username":
                                         "root",
                                         "password":
                                         "r00t9001!"
                                     }))
