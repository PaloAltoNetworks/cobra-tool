import argparse

from core import main
from core.helpers import get_scenario_list


def parse_arguments():
    scenarios = get_scenario_list()
    parser = argparse.ArgumentParser(description="Terminal-based option tool")
    parser.add_argument("cloud_provider", choices=["aws", "azure", "gcp"], help="Cloud provider (aws, azure, gcp)")
    parser.add_argument("action", choices=["launch", "status", "destroy"], help="Action to perform (launch, status, destroy)")
    parser.add_argument("--simulation", action="store_true", help="Enable simulation mode")
    parser.add_argument("--scenario", choices=scenarios, default=scenarios[0], help="Scenario selection")
    return parser.parse_args()


def main_function(cloud_provider, action, simulation, scenario):
    main.main(cloud_provider, action, simulation, scenario)


if __name__ == "__main__":
    args = parse_arguments()
    options = vars(args)
    main_function(**options)