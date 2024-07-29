import json

import pulumi
from pulumi_aws import s3

bucket = s3.Bucket('b', bucket_prefix='cobra-test-')
object = s3.BucketObject(
    'object',
    bucket=bucket.id,
    key='customers.csv',
    source=pulumi.FileAsset('./data/customers.csv')
)
# Allow public ACLs for the bucket
public_access_block = s3.BucketPublicAccessBlock(
    "exampleBucketPublicAccessBlock",
    bucket=bucket.id,
    block_public_acls=False,
)
# Set the access policy for the bucket so all objects are readable
s3.BucketPolicy(
    "bucket-policy",
    bucket=bucket.id,
    policy=bucket.id.apply(
        lambda id: json.dumps({
            "Version": "2012-10-17",
            "Statement": {
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                # Policy refers to bucket explicitly
                "Resource": [f"arn:aws:s3:::{id}/*"]
            },
        })),
    opts=pulumi.ResourceOptions(depends_on=[public_access_block])
)
pulumi.export('s3-bucket-arn', bucket.arn)
pulumi.export('s3-bucket-id', bucket.id)
pulumi.export('s3-object-arn', object.arn)
pulumi.export('s3-object-id', object.id)
