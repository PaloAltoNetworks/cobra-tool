import json
import pulumi
import pulumi_aws as aws


config = pulumi.Config()
extra_region = config.require("extraRegion")
pulumi.export("ExtraRegion", extra_region)


def create_secrets():
    demo_secret_string = aws.secretsmanager.Secret(
        "secret-string",
        name="Cobra-8-Secret-String",
        recovery_window_in_days=0,
        description="A very well kept secret.",
    )

    aws.secretsmanager.SecretVersion(
        "secret-string-version",
        secret_id=demo_secret_string.id,
        secret_string="VerySecure!",
    )

    demo_secret_additional_string = aws.secretsmanager.Secret(
        "secret-string-2",
        name="Cobra-8-Secret-String-2",
        recovery_window_in_days=0,
        description="Another very well kept secret.",
    )

    aws.secretsmanager.SecretVersion(
        "other-secret-string-version",
        secret_id=demo_secret_additional_string.id,
        secret_string="AlsoSecure!",
    )

    # This secret will be created in another region
    extra_region_provider = aws.Provider(
        "extra-region-provider",
        region=extra_region,
    )

    demo_secret_map = aws.secretsmanager.Secret(
        "secret-map",
        name="Cobra-8-Secret-Map",
        recovery_window_in_days=0,
        description="Another well kept secret.",
        opts=pulumi.ResourceOptions(provider=extra_region_provider),
    )
    aws.secretsmanager.SecretVersion(
        "secret-map-version",
        secret_id=demo_secret_map.id,
        secret_string=json.dumps({"username": "root", "password": "r00t9001!"}),
        opts=pulumi.ResourceOptions(provider=extra_region_provider),
    )
