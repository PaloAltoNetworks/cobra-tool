import os
import pulumi
from pulumi_aws import s3

DEFAULT_EXFIL_BUCKET_COUNT = 16


def _populate_bucket(bucket, bucket_index):
    """Populate a single bucket with sensitive files.

    Args:
        bucket: The S3 bucket resource to populate.
        bucket_index: Index of the bucket, used to create unique resource names.
    """
    s3_objects = []


    s3_objects.append(
        s3.BucketObject(
            f"strategy-doc-b{bucket_index}",
            bucket=bucket.id,
            key=f"confidential/project_cobra_confidential-b{bucket_index}.txt",
            source=pulumi.FileAsset("./bucket_files/phase2_strategy.txt"),
            content_type="text/plain",
        )
    )

    s3_objects.append(
        s3.BucketObject(
            f"postmortem-doc-b{bucket_index}",
            bucket=bucket.id,
            key=f"incidents/2024/incident_postmortem_sev1-b{bucket_index}.txt",
            source=pulumi.FileAsset("./bucket_files/incident_report_2024.txt"),
            content_type="text/plain",
        )
    )

    s3_objects.append(
        s3.BucketObject(
            f"chat-log-b{bucket_index}",
            bucket=bucket.id,
            key=f"logs/slack_exports/chat_export_dev_ops-b{bucket_index}.txt",
            source=pulumi.FileAsset("./bucket_files/chat_devops.txt"),
            content_type="text/plain",
        )
    )

    s3_objects.append(
        s3.BucketObject(
            f"transactions-snippet-b{bucket_index}",
            bucket=bucket.id,
            key=f"logs/slack_exports/sensitive_info-b{bucket_index}.txt",
            source=pulumi.FileAsset("./bucket_files/sensitive_info.txt"),
            content_type="text/plain",
        )
    )

    s3_objects.append(
        s3.BucketObject(
            f"users-b{bucket_index}",
            bucket=bucket.id,
            key=f"data/users-b{bucket_index}.csv",
            source=pulumi.FileAsset("./bucket_files/users.csv"),
            content_type="text/csv",
        )
    )

    return s3_objects


def create_s3_resources():
    config = pulumi.Config()
    bucket_count = config.get_int("exfilBucketCount") or DEFAULT_EXFIL_BUCKET_COUNT

    buckets = []
    for idx in range(bucket_count):
        bucket = s3.Bucket(f"cobra-scenario-8-sensitive-bucket-{idx}")
        _populate_bucket(bucket, idx)
        buckets.append(bucket)

    bucket_names = [b.id for b in buckets]
    pulumi.export("Exfil Bucket Names", pulumi.Output.all(*bucket_names))


def create_agent_installation():
    # force_destroy allows deleting the bucket even if it has files
    bucket = s3.Bucket("cobra-scenario-8-agent-installation-bucket")

    config = pulumi.Config()
    agent_installer_path = config.require("agentInstallerPath")

    installer_object = s3.BucketObject(
        "agent-installer-obj",
        bucket=bucket.id,
        key="agent_installer.zip",
        source=pulumi.FileArchive(agent_installer_path),
    )

    return {"agent_bucket": bucket, "agent_installer_object": installer_object}
