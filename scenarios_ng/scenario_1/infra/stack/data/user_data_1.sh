#!/bin/bash
sudo apt update -y
sudo apt install docker.io -y
sudo apt install python3-pip -y
sudo pip3 install aws-export-credentials
sudo pip3 install awscli
sudo systemctl start docker
sudo systemctl enable docker
sudo apt install unzip
sudo systemctl start docker
sudo systemctl enable docker
sudo systemctl stop tomcat9.service
sudo apt  install docker-compose -y
wget https://lab-files-00ffaabcc.s3.amazonaws.com/pulumi/app.zip -P /home/ubuntu/
cd /home/ubuntu/ && unzip /home/ubuntu/app.zip
sudo docker-compose -f /home/ubuntu/app/docker-compose.yml up --build -d
