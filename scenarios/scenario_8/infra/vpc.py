import pulumi
import pulumi_aws as aws


config = pulumi.Config()
region = aws.get_region()

vpc_id_config = config.get("vpcId")
subnet_id_config = config.get("subnetId")

# --- Network Logic ---
# If configuration for networking is present, use it. Otherwise, create a new network stack.
if vpc_id_config and subnet_id_config:
    print(f"Using specified VPC: {vpc_id_config} and Subnet: {subnet_id_config}")
    vpc_id = vpc_id_config
    subnet_id = subnet_id_config
else:
    print("VPC or Subnet config missing. Creating new network stack...")

    # Create VPC
    vpc = aws.ec2.Vpc(
        "cobra-vpc",
        cidr_block="10.0.0.0/16",
        enable_dns_hostnames=True,
        enable_dns_support=True,
        tags={"Name": "Cobra Scenario 8 VPC"},
    )

    # Create Internet Gateway (Required for public access)
    igw = aws.ec2.InternetGateway(
        "cobra-igw", vpc_id=vpc.id, tags={"Name": "Cobra Scenario 8 IGW"}
    )

    # Create Subnet
    subnet = aws.ec2.Subnet(
        "cobra-subnet",
        vpc_id=vpc.id,
        cidr_block="10.0.1.0/24",
        availability_zone=f"{region.name}a",
        tags={"Name": "Cobra Scenario 8 Subnet"},
    )

    # Create Route Table & Association (Routes traffic to Internet Gateway)
    route_table = aws.ec2.RouteTable(
        "cobra-rt",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                gateway_id=igw.id,
            )
        ],
        tags={"Name": "Cobra Scenario 8 RT"},
    )

    aws.ec2.RouteTableAssociation(
        "cobra-rta",
        route_table_id=route_table.id,
        subnet_id=subnet.id,
    )

    # Assign the IDs from the newly created resources
    vpc_id = vpc.id
    subnet_id = subnet.id
