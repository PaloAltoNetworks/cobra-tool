import argparse
import os
from pathlib import Path, PurePath

from core import main_ng as main
from core.helpers import get_scenario_list, get_scenarios_config


def parse_arguments():
    scenarios = get_scenario_list()
    parser = argparse.ArgumentParser(description="Terminal-based option tool")
    parser.add_argument("cloud_provider", choices=["aws", "azure", "gcp"], help="Cloud provider (aws, azure, gcp)")
    parser.add_argument("action", choices=["launch", "status", "destroy"], help="Action to perform (launch, status, destroy)")
    parser.add_argument("--simulation", action="store_true", help="Enable simulation mode")
    parser.add_argument("--scenario", choices=scenarios, default=scenarios[0], help="Scenario selection")
    return parser.parse_args()


def main_function(cloud_provider, action, simulation, scenario):
    # Call the main function from the imported module and pass the options
    main.main(cloud_provider, action, simulation, scenario)


if __name__ == "__main__":
    args = parse_arguments()
    
    # Convert argparse Namespace to dictionary
    options = vars(args)
    
    # Call the main function with options
    main_function(**options)
