#!/bin/bash
# 1. Install Dependencies
sudo snap install aws-cli --classic
sudo apt-get update
sudo apt-get install -y unzip

# 2. Download Agent
# CRITICAL: We do this BEFORE writing the specific user credentials below.
# This command uses the EC2 Instance Profile (which has S3 read access).
echo "Downloading agent from S3..."
aws s3 cp s3://{3}/{4} /home/ubuntu/agent_installer.zip

# 3. Extract & Install Agent 
echo "Extracting agent..."
unzip /home/ubuntu/agent_installer.zip -d /home/ubuntu/agent
chown -R ubuntu:ubuntu /home/ubuntu/agent
sudo mkdir -p /etc/panw
sudo cp  /home/ubuntu/agent/cortex.conf /etc/panw/
chmod +x  /home/ubuntu/agent/cortex-*.sh
sudo /home/ubuntu/agent/cortex-*.sh

# 4. Configure 'Dev User' Credentials
# Now we write the keys for the 'dev-user'. Future AWS commands run by the user
# will use these keys (which have Lambda Admin access but NO S3 access).
mkdir -p /home/ubuntu/.aws

cat <<EOF > /home/ubuntu/.aws/credentials
[default]
aws_access_key_id = {0}
aws_secret_access_key = {1}
EOF

cat <<EOF > /home/ubuntu/.aws/config
[default]
region = {5}

[profile lambda-role]
role_arn = {2}
source_profile = default
EOF

# 5. Fix permissions
chown -R ubuntu:ubuntu /home/ubuntu/.aws
chmod 600 /home/ubuntu/.aws/credentials
chmod 600 /home/ubuntu/.aws/config

echo "Setup complete."
