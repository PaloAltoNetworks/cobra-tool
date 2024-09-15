import os
import pyfiglet
import time
import subprocess
import json
from tqdm import tqdm
from time import sleep
from termcolor import colored



def loading_animation():
    chars = "/—\\|"
    for _ in range(10):
        for char in chars:
            print(f"\rLoading {char}", end="", flush=True)
            time.sleep(0.1)


def generate_ssh_key():
    # Define the path to save the keys
    key_path = os.path.expanduser("./id_rsa")

    # Check if SSH key already exists
    if os.path.exists(key_path):
        print("SSH key already exists. Deleting the existing key...")
        os.remove(key_path)

    # Generate the SSH key pair
    with open(os.devnull, 'w') as devnull:
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", key_path], stdout=devnull, stderr=devnull)
    print("SSH Key Pair generated successfully!")

    return key_path, key_path + ".pub"

def upload_file_to_server(source_file, server_username, server_ip, server_directory):
    try:
        # Construct the scp command
        scp_command = f'scp -i id_rsa -r {source_file} {server_username}@{server_ip}:{server_directory}'
        
        # Execute the scp command
        subprocess.check_call(scp_command, shell=True)
        
        print(f"File '{source_file}' successfully uploaded to server '{server_ip}' in directory '{server_directory}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error uploading file: {e}")
