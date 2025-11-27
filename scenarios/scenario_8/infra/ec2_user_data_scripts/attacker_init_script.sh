#!/bin/bash
sudo apt update -y
sudo apt install python3-pip -y
sudo apt install cython3 -y
sudo apt install jq -y
sudo snap install aws-cli --classic

cd /home/ubuntu/
git clone https://github.com/SusmithKrishnan/torghost.git

cd /home/ubuntu/torghost/
pip install -r requirements.txt

bash build.sh

# Tor Connection Loop (Sanity Check & Reconnect)
MAX_RETRIES=10
COUNT=0

while [ $COUNT -lt $MAX_RETRIES ]; do

    # Stop any previous instances to be safe
    sudo python3 torghost.py -x
    sleep 2
    
    # Start TorGhost
    sudo timeout 30 python3 torghost.py -s > /home/ubuntu/torghost_start.log 2>&1 &

    RET_CODE=$?
    
    if [ $RET_CODE -eq 0 ]; then
        echo "TorGhost start command finished successfully."
    elif [ $RET_CODE -eq 124 ]; then
        echo "TorGhost start timed out (hung)."
        COUNT=$((COUNT+1))
        continue
    else
        echo "TorGhost start failed with exit code $RET_CODE."
        COUNT=$((COUNT+1))
        continue
    fi
    
    # Allow some time for the circuit to establish
    sleep 20
    
    # Sanity Web Request: Check if we can reach the outside world via Tor
    # We use a short timeout so we don't hang forever
    CURRENT_IP=$(curl -s --connect-timeout 10 https://api.ipify.org)
    
    if [ ! -z "$CURRENT_IP" ]; then
        echo "Tor verification successful! Current Public IP: $CURRENT_IP" > /home/ubuntu/tor_status.txt
        break
    fi
    
    COUNT=$((COUNT+1))
done

if [ $COUNT -eq $MAX_RETRIES ]; then
    echo "WARNING: Could not establish stable Tor connection after $MAX_RETRIES attempts." > /home/ubuntu/tor_status.txt
fi
