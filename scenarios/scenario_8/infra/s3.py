import os
import pulumi
from pulumi_aws import s3


def create_s3_resources():
    bucket = s3.Bucket('cobra-scenario-8-bucket')

    source_dir = "bucket_files"

    strategy_doc = s3.BucketObject(
        "strategy-doc",
        bucket=bucket.id,
        key="confidential/project_cobra_confidential.txt",
        source=pulumi.FileAsset("./bucket_files/phase2_strategy.txt"),
        content_type="text/markdown")

    postmortem_doc = s3.BucketObject(
        "postmortem-doc",
        bucket=bucket.id,
        key="incidents/2024/incident_postmortem_sev1.txt",
        source=pulumi.FileAsset("./bucket_files/incident_report_2024.txt"),
        content_type="text/markdown")

    chat_log = s3.BucketObject(
        "chat-log",
        bucket=bucket.id,
        key="logs/slack_exports/chat_export_dev_ops.txt",
        source=pulumi.FileAsset("./bucket_files/chat_devops.txt"),
        content_type="text/markdown")

    pulumi.export('bucket_name', bucket.id)


def create_agent_installation():
    # force_destroy allows deleting the bucket even if it has files
    bucket = s3.Bucket('cobra-scenario-8-agent-installation-bucket')

    config = pulumi.Config()
    agent_installer_path = config.require("agentInstallerPath")

    installer_object = s3.BucketObject(
        "agent-installer-obj",
        bucket=bucket.id,
        key="agent_installer.zip",  # <--- The EC2 will download this key
        source=pulumi.FileArchive(agent_installer_path))

    return {"agent_bucket": bucket, "agent_installer_object": installer_object}
