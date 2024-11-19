import pulumi
import pulumi_eks as eks
import pulumi_aws as aws
 
# Create an EKS cluster with the default configuration.
current = aws.get_region()
region = current.name


cluster = eks.Cluster("cluster", 
                      tags={
        'Name': 'backend-cluster',
    },)
#print(cluster.resource_name)

# Export the cluster's kubeconfig.
#pulumi.export("kubeconfig", cluster.kubeconfig)
pulumi.export("Region", region)
pulumi.export("ClusterData", cluster.core)