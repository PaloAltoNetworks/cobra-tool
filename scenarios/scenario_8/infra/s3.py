import os
import pulumi
from pulumi_aws import s3


def create_s3_resources():
    bucket = s3.Bucket("cobra-scenario-8-sensitive-bucket")

    source_dir = "bucket_files"

    s3_objects = []

    for i in range(6):
        s3_objects.append(
            s3.BucketObject(
                f"strategy-doc-{str(i)}",
                bucket=bucket.id,
                key=f"confidential/project_cobra_confidential_{str(i)}.txt",
                source=pulumi.FileAsset("./bucket_files/phase2_strategy.txt"),
                content_type="text/plain",
            )
        )

        s3_objects.append(
            s3.BucketObject(
                f"postmortem-doc-{str(i)}",
                bucket=bucket.id,
                key=f"incidents/2024/incident_postmortem_sev1_{str(i)}.txt",
                source=pulumi.FileAsset("./bucket_files/incident_report_2024.txt"),
                content_type="text/plain",
            )
        )

        s3_objects.append(
            s3.BucketObject(
                f"chat-log-{str(i)}",
                bucket=bucket.id,
                key=f"logs/slack_exports/chat_export_dev_ops_{str(i)}.txt",
                source=pulumi.FileAsset("./bucket_files/chat_devops.txt"),
                content_type="text/plain",
            )
        )

        s3_objects.append(
            s3.BucketObject(
                f"transactions-snippet-{str(i)}",
                bucket=bucket.id,
                key=f"logs/slack_exports/transactions_snippet_{str(i)}.csv",
                source=pulumi.FileAsset("./bucket_files/transactions_snippet.csv"),
                content_type="text/csv",
            )
        )

    pulumi.export("Bucket Name", bucket.id)


def create_agent_installation():
    # force_destroy allows deleting the bucket even if it has files
    bucket = s3.Bucket("cobra-scenario-8-agent-installation-bucket")

    config = pulumi.Config()
    agent_installer_path = config.require("agentInstallerPath")

    installer_object = s3.BucketObject(
        "agent-installer-obj",
        bucket=bucket.id,
        key="agent_installer.zip",  # <--- The EC2 will download this key
        source=pulumi.FileArchive(agent_installer_path),
    )

    return {"agent_bucket": bucket, "agent_installer_object": installer_object}
