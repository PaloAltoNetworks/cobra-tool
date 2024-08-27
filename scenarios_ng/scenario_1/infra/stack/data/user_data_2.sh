#!/bin/bash
sudo apt update -y
sudo apt install python3-pip -y
sudo apt  install awscli -y
sudo apt install git -y
sudo pip3 install bs4 
sudo apt install jq -y
sudo pip3 install packaging

wget https://lab-files-00ffaabcc.s3.amazonaws.com/pulumi/exploit.py -P /home/ubuntu
chmod +x /home/ubuntu/exploit.py
chown ubuntu:ubuntu /home/ubuntu/exploit.py

cd /home/ubuntu/
git clone https://github.com/SusmithKrishnan/torghost.git
mkdir /home/ubuntu/.aws/
touch /home/ubuntu/.aws/credentials
chown -R ubuntu:ubuntu /home/ubuntu/.aws/


cd /home/ubuntu/torghost/
sudo python3 torghost.py -s
sleep 30
sudo python3 torghost.py -s