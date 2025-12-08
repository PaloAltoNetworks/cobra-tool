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


def generate_ssh_key(key_name="./id_rsa"):
    # Define the path to save the keys
    key_path = os.path.expanduser(key_name)

    # Check if SSH key already exists
    if os.path.exists(key_path):
        confirm = input(f"Warning: An SSH key already exists at '{key_path}'.\nDo you want to overwrite it? [y/N]: "
                        ).strip().lower()
        if confirm not in ('y', 'yes'):
            print("Operation cancelled. Existing key was not modified. Exiting...")
            exit(1)

        print("Deleting the existing key...")
        os.remove(key_path)

    # Generate the SSH key pair
    with open(os.devnull, 'w') as devnull:
        subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", key_path],
                       stdout=devnull,
                       stderr=devnull)
    print("SSH Key Pair generated successfully!")

    return key_path, key_path + ".pub"


def upload_file_to_server(source_file, server_username, server_ip, server_directory, key_path='./id_rsa'):
    try:
        # Construct the scp command
        scp_command = f'scp -i {key_path} -r {source_file} {server_username}@{server_ip}:{server_directory}'

        # Execute the scp command
        subprocess.check_call(scp_command, shell=True)

        print(f"File '{source_file}' successfully uploaded to server '{server_ip}' in directory '{server_directory}'.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error uploading file: {e}")

        # Re-raise the exception so the calling script knows it failed
        raise (e)


def run_subprocess(cmd, return_output=False, check=True, suppress_print=False):
    # If we want to return output, we must capture it (PIPE), this also means that the terminal will not display it.
    capture_target = subprocess.PIPE if (return_output or suppress_print) else None

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,  # Automatically raises CalledProcessError if True and exit code != 0
            stdout=capture_target,  # Controls capture vs print
            stderr=capture_target,  # Keep stderr combined with stdout logic
            text=True  # Auto-decodes bytes to string (utf-8)
        )

        # If we are here, the command succeeded (or check=False)
        if return_output:
            return result.stdout.strip()

        return result.returncode

    except subprocess.CalledProcessError as e:
        # This block is only reached if check=True AND the command failed.
        # The 'e' object contains e.returncode, e.stdout, and e.stderr
        print(f"Command failed with error code: {e.returncode}")
        if return_output and e.stdout:
            print(f"Captured Output before failure: {e.stdout}")

        # Re-raise the exception so the calling script knows it failed
        raise e
