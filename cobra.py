import argparse
from core import main

def parse_arguments():
    parser = argparse.ArgumentParser(description="Terminal-based option tool")
    parser.add_argument("action", choices=["launch", "status", "destroy", "post-launch"], help="Action to perform (launch, status, destroy)")
    parser.add_argument("--simulation", action="store_true", help="Enable simulation mode")
    parser.add_argument("--scenario", choices=["cobra-scenario-1", "cobra-scenario-2", "cobra-scenario-3", "cobra-scenario-4", "cobra-scenario-5"], default="cobra-scenario-1", help="Scenario selection")
    parser.add_argument("--manual", action="store_true", help="Perform attack manually through post-launch")
    return parser.parse_args()

def main_function(action, simulation, scenario, manual):
    # Call the main function from the imported module and pass the options
    if not scenario:
        scenario = "none"
    main.main(action, simulation, scenario, manual)

if __name__ == "__main__":
    args = parse_arguments()
    
    # Convert argparse Namespace to dictionary
    options = vars(args)
    
    # Call the main function with options
    main_function(**options)
