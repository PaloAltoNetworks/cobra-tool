import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()
NODE_COUNT = config.get_int('node_count') or 1
NODE_MACHINE_TYPE = config.get('node_machine_type') or 'e2-medium'
MASTER_VERSION = config.get('master_version') 

# Defining the GKE Cluster
gke_cluster = gcp.container.Cluster('cluster-1', 
    name = "cluster-1",
    location = "us-central1",
    initial_node_count = NODE_COUNT,
    remove_default_node_pool = True,
    min_master_version = MASTER_VERSION,
    deletion_protection = False
)

gke_nodepool = gcp.container.NodePool("nodepool-1",
    name = "nodepool-1",
    location = "us-central1",
    node_locations = ["us-central1-a"],
    cluster = gke_cluster.id,
    node_count = NODE_COUNT,
    node_config = gcp.container.NodePoolNodeConfigArgs(
        preemptible = False,
        machine_type = NODE_MACHINE_TYPE,
        disk_size_gb = 20,
        oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"],
        shielded_instance_config = gcp.container.NodePoolNodeConfigShieldedInstanceConfigArgs(
            enable_integrity_monitoring = True,
            enable_secure_boot = True
        )
    ),
    
    autoscaling = gcp.container.NodePoolAutoscalingArgs(
        min_node_count = 1,
        max_node_count = 3
    ),
    
    management = gcp.container.NodePoolManagementArgs(
        auto_repair  = True,
        auto_upgrade = True
    )
)

pulumi.export("cluster-name", gke_cluster.name)

