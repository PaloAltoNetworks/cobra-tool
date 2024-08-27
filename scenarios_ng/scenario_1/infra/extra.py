import boto3


def deploy_additional_resources():
    pass


def destroy_additional_resources(data):
    # TODO: previously this was "imported" into the Pulumi stack using pulumi 
    # command line invocation (via subprocess) and thus could be deleted by
    # destroying the stack. TODO is to figure out how to do this without
    # subprocess and not need this additional code.
    INSTANCE_NAME = 'Cobra-Anomalous'
    ec2_client = boto3.client('ec2', region_name=data['Region'])
    instances = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [INSTANCE_NAME]}])
    instance_id = [i for i in instances['Reservations'][0]['Instances']][0]['InstanceId']
    ec2_client.terminate_instances(InstanceIds=[instance_id])
