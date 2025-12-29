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


def run_command(cmd: str, check: bool = True) -> int:
    """
    Execute a shell command and return exit code.
    Output is printed to terminal.
    
    Args:
        cmd: Shell command to execute
        check: If True, raise exception on non-zero exit code
        
    Returns:
        Exit code (0 = success)
        
    Raises:
        CalledProcessError: If check=True and command fails
    """
    result = subprocess.run(cmd, shell=True, check=check, text=True)
    return result.returncode


def run_command_capture(cmd: str, check: bool = True, include_stderr: bool = True) -> str:
    """
    Execute a shell command and capture output.
    
    Args:
        cmd: Shell command to execute
        check: If True, raise exception on non-zero exit code
        include_stderr: If True, include stderr in output
        
    Returns:
        Command output (stdout, optionally with stderr)
        
    Raises:
        CalledProcessError: If check=True and command fails
    """
    stderr_target = subprocess.STDOUT if include_stderr else subprocess.PIPE
    
    result = subprocess.run(
        cmd,
        shell=True,
        check=check,
        stdout=subprocess.PIPE,
        stderr=stderr_target,
        text=True
    )
    
    return result.stdout.strip() if result.stdout else ""
