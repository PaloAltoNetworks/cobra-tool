import pulumi
import pulumi_aws as aws

import iam
from vpc import vpc_id, subnet_id
from utils import *


config = pulumi.Config()
region = aws.get_region()
pulumi.export("Region", region.region)

# ---------------------------------------------------------------------------
# Ubuntu AMI resolution
# ---------------------------------------------------------------------------
# To pin the kernel version, set "infra:ubuntuAmiId" in Pulumi config to a
# specific AMI ID (e.g. ami-0abcdef1234567890).  The ID is region-specific,
# so make sure it matches the target region.
#
# When no AMI ID is provided the latest Ubuntu 24.04 image is resolved
# automatically, which means the kernel version may change between runs.
# ---------------------------------------------------------------------------
_custom_ami_id = config.get("ubuntuAmiId")

if _custom_ami_id:
    ubuntu_ami = aws.ec2.get_ami(
        filters=[
            aws.ec2.GetAmiFilterArgs(
                name="image-id",
                values=[_custom_ami_id],
            ),
        ],
        owners=["099720109477"],  # Canonical
    )
else:
    # Warn when agent mode is enabled – the dynamically resolved AMI may ship
    # a kernel version that is not supported by the agent.
    if config.get_bool("includeAgent"):
        pulumi.log.warn(
            "No pinned AMI ID configured (infra:ubuntuAmiId). The latest "
            "Ubuntu 24.04 AMI will be used, which may include a kernel version "
            "not supported by the agent. Set 'infra:ubuntuAmiId' to a specific "
            "AMI ID to guarantee kernel compatibility."
        )

    ubuntu_ami = aws.ec2.get_ami(
        filters=[
            aws.ec2.GetAmiFilterArgs(
                name="name",
                values=["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"],
            ),
            aws.ec2.GetAmiFilterArgs(
                name="virtualization-type",
                values=["hvm"],
            ),
        ],
        owners=["099720109477"],  # Canonical
        most_recent=True,
    )


def create_ec2_attacker_machine():
    public_key_path = config.require("attackerPublicKeyPath")
    key_pair = aws.ec2.KeyPair(
        "attacker-machine-key-pair",
        key_name="cobra-scenario-8-attacker-ec2-key",
        public_key=read_public_key(public_key_path),
    )

    user_data_script = open(
        "./ec2_user_data_scripts/attacker_init_script.sh", "r"
    ).read()

    # Security group
    # NOTE: The attacker machine's ingress is restricted to the /24 CIDR block
    # of the deployer's current public IP. The machine will only be accessible
    # via SSH from that same IP range. If you run this from a different network
    # later, you will need to update the security group or redeploy.

    # Convert to /24 cidr block
    sg_cidr = ".".join(fetch_public_ip().split(".")[:-1]) + ".0/24"
    pulumi.log.warn(
        f"Attacker machine SSH access is restricted to {sg_cidr}. "
        "The machine will only be accessible from this CIDR block. "
        "If you need access from a different network, update the security "
        "group or redeploy from the desired network."
    )

    attacker_ec2_sg = aws.ec2.SecurityGroup(
        "ec2-security-group-attacker",
        name="cobra-scenario-8-sg-attacker",
        vpc_id=vpc_id,
        ingress=[
            {
                "protocol": "tcp",
                "fromPort": 22,
                "toPort": 22,
                "cidrBlocks": [sg_cidr],
            }
        ],
        egress=[
            {
                "protocol": "-1",
                "fromPort": 0,
                "toPort": 0,
                "cidrBlocks": ["0.0.0.0/0"],
            }
        ],
    )

    instance = aws.ec2.Instance(
        "ec2-attacker-dev-machine",
        instance_type="t2.small",
        ami=ubuntu_ami.id,
        vpc_security_group_ids=[attacker_ec2_sg.id],
        subnet_id=subnet_id,
        associate_public_ip_address=True,
        user_data=user_data_script,
        user_data_replace_on_change=True,
        key_name=key_pair.key_name,
        ebs_block_devices=[
            aws.ec2.InstanceEbsBlockDeviceArgs(
                device_name=ubuntu_ami.root_device_name,  # Finds the root device
                encrypted=True,  # Forces encryption
                volume_type="gp3",
                # You can also specify volume_size, volume_type, etc. here
            )
        ],
        tags={"Name": "Cobra Scenario 8 - Attacker Machine"},
    )

    pulumi.export("Attacker Server Public IP", instance.public_ip)
    pulumi.export("Attacker Server Instance ID", instance.id)


def create_ec2_compromised_machine(
    ec2_role, dev_access_key, lambda_role, agent_bucket, agent_object
):
    public_key_path = config.require("compromisedPublicKeyPath")
    key_pair = aws.ec2.KeyPair(
        "compromised-machine-key-pair",
        key_name="cobra-scenario-8-compromised-ec2-key",
        public_key=read_public_key(public_key_path),
    )

    instance_profile = aws.iam.InstanceProfile(
        "ec2-instance-profile",
        name="cobra-scenario-8-instance-profile",
        role=ec2_role.name,
    )

    user_data_script_template = open(
        "./ec2_user_data_scripts/compromised_init_script_template.sh", "r"
    ).read()

    user_data_script = pulumi.Output.format(
        user_data_script_template,
        dev_access_key.id,  # {0}
        dev_access_key.secret,  # {1}
        lambda_role.arn,  # {2}
        agent_bucket.bucket,  # {3} Bucket Name
        agent_object.key,  # {4} Object Key
        region.region,  # {5}
    )

    # Security group
    compromised_ec2_sg = aws.ec2.SecurityGroup(
        "ec2-security-group-compromised",
        name="cobra-scenario-8-sg-comrpomised",
        vpc_id=vpc_id,
        ingress=[
            {
                "protocol": "tcp",
                "fromPort": 22,
                "toPort": 22,
                "cidrBlocks": ["0.0.0.0/0"],
            }
        ],
        egress=[
            {
                "protocol": "-1",
                "fromPort": 0,
                "toPort": 0,
                "cidrBlocks": ["0.0.0.0/0"],
            }
        ],
    )

    # Create an EC2 instance with user data
    instance = aws.ec2.Instance(
        "ec2-compromised-dev-machine",
        instance_type="t2.small",
        ami=ubuntu_ami.id,
        iam_instance_profile=instance_profile.name,
        vpc_security_group_ids=[compromised_ec2_sg.id],
        subnet_id=subnet_id,
        associate_public_ip_address=True,
        key_name=key_pair.key_name,
        user_data=user_data_script,
        user_data_replace_on_change=True,
        ebs_block_devices=[
            aws.ec2.InstanceEbsBlockDeviceArgs(
                device_name=ubuntu_ami.root_device_name,  # Finds the root device
                encrypted=True,  # Forces encryption
                volume_type="gp3",
                # You can also specify volume_size, volume_type, etc. here
            )
        ],
        tags={"Name": "Cobra Scenario 8 - Compromised Dev Machine"},
    )

    pulumi.export("Compromised Server Public IP", instance.public_ip)
    pulumi.export("Compromised Server Instance ID", instance.id)
