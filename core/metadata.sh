#!/bin/bash
cd ../infra && pulumi stack -s dev output --json >> ../core/output.json
export ATTACKER_SERVER_INSTANCE_ID=$(jq -r '.["Attacker Server Instance ID"]' ../core/output.json)  
export ATTACKER_SERVER_PUBLIC_IP=$(jq -r '.["Attacker Server Public IP"]' ../core/output.json)
export WEB_SERVER_INSTANCE_ID=$(jq -r '.["Web Server Instance ID"]' ../core/output.json)
export WEB_SERVER_PUBLIC_IP=$(jq -r '.["Web Server Public IP"]' ../core/output.json)
