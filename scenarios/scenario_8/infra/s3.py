import os
import pulumi
from pulumi_aws import s3

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
