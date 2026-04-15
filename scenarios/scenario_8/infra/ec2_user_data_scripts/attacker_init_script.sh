#!/bin/bash
sudo apt update -y
sudo apt install jq -y
sudo snap install aws-cli --classic
sudo apt install tor -y
sudo apt install proxychains4 -y

cd /home/ubuntu/

# Tor Connection Loop (Sanity Check & Reconnect)
MAX_RETRIES=10
COUNT=0

while [ $COUNT -lt $MAX_RETRIES ]; do

    # Sanity Web Request: Check if we can reach the outside world via Tor
    CURRENT_IP=$(timeout 30 curl -x socks5h://localhost:9050 -s https://check.torproject.org/api/ip | jq '.IP')

    RET_CODE=$?
    
    if [ $RET_CODE -eq 0 ]; then
        echo "Tor connected successfully."
    elif [ $RET_CODE -eq 124 ]; then
        echo "Tor connection timed out (hung)."
        COUNT=$((COUNT+1))
        continue
    else
        echo "Tor curl command failed with exit code $RET_CODE."
        COUNT=$((COUNT+1))
        continue
    fi
    
    # Allow some time for the circuit to establish
    sleep 20
    

    # We use a short timeout so we don't hang forever
    if [ ! -z "$CURRENT_IP" ]; then
        echo "Tor verification successful! Attacker machine initialized with Tor's public IP: $CURRENT_IP" > /home/ubuntu/tor_status.txt
        break
    fi
    
    COUNT=$((COUNT+1))
done

if [ $COUNT -eq $MAX_RETRIES ]; then
    echo "WARNING: Could not establish stable Tor connection after $MAX_RETRIES attempts." > /home/ubuntu/tor_status.txt
fi
