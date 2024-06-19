import argparse
from core import main
import pyfiglet
from termcolor import colored

def display_banner():
    ascii_art = pyfiglet.figlet_format("COBRA")
    print(colored(ascii_art, color="cyan"))

def parse_arguments():
    parser = argparse.ArgumentParser(description="Terminal-based option tool")
    parser.add_argument("cloud_provider", choices=["aws", "azure", "gcp"], help="Cloud provider (aws, azure, gcp)")
    parser.add_argument("action", choices=["launch", "status", "destroy"], help="Action to perform (launch, status, destroy)")
    parser.add_argument("--simulation", action="store_true", help="Enable simulation mode")
    parser.add_argument("--scenario", choices=["scenario-1", "scenario-2"], default="scenario-1", help="Scenario selection")
    return parser.parse_args()

def main_function(cloud_provider, action, simulation, scenario):
    # Call the main function from the imported module and pass the options
    main.main(cloud_provider, action, simulation, scenario)

if __name__ == "__main__":
    display_banner()
    args = parse_arguments()
    
    # Convert argparse Namespace to dictionary
    options = vars(args)
    
    # Call the main function with options
    main_function(**options)