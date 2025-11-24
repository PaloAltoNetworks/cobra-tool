import json

import pulumi_aws as aws

demo_db_secret = aws.secretsmanager.Secret("secret-string", name="Cobra-8-Secret-String", description="A very well kept secret.")
aws.secretsmanager.SecretVersion("secret-string-version", secret_id=demo_db_secret.id, secret_string="VerySecure!")

demo_db2_secret = aws.secretsmanager.Secret("secret-map", name="Cobra-8-Secret-Map", description="Another well kept secret.")
aws.secretsmanager.SecretVersion("secret-map-version", secret_id=demo_db2_secret.id, secret_string=json.dumps({"username": "root", "password": "r00t9001!"}))
