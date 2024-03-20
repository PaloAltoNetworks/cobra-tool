import pyfiglet
from termcolor import colored
#import scenario_module  # Import the scenario module

def print_ascii_art(text):
    ascii_art = pyfiglet.figlet_format(text)
    print(colored(ascii_art, color="cyan"))

def select_cloud_provider():
    print(colored("Select Cloud Provider:", color="yellow"))
    print(colored("1. AWS", color="green"))
    print(colored("2. Azure", color="green"))
    print(colored("3. GCP", color="green"))
    while True:
        try:
            choice = int(input(colored("Enter your choice (1/2/3): ", color="yellow")))
            if choice not in [1, 2, 3]:
                raise ValueError(colored("Invalid choice. Please enter 1, 2, or 3.", color="red"))
            return choice
        except ValueError as e:
            print(e)

def select_attack_scenario():
    print(colored("Select Attack Scenario:", color="yellow"))
    print(colored("1. XYZ (replace with actual scenario)", color="green"))
    print(colored("2. Coming Soon", color="green"))
    while True:
        try:
            choice = int(input(colored("Enter your choice: ", color="yellow")))
            if choice not in [1, 2]:
                raise ValueError(colored("Invalid choice. Please enter 1 or 2.", color="red"))
            return choice
        except ValueError as e:
            print(e)

def get_credentials():
    while True:
        try:
            access_key = input(colored("Enter Access Key: ", color="yellow"))
            if not access_key:
                raise ValueError(colored("Access Key cannot be empty.", color="red"))
            secret_key = input(colored("Enter Secret Key: ", color="yellow"))
            if not secret_key:
                raise ValueError(colored("Secret Key cannot be empty.", color="red"))
            return access_key, secret_key
        except ValueError as e:
            print(e)

def execute_scenario(access_key, secret_key, scenario):
    try:
        # Call the scenario function from the imported module
        scenario.execute(access_key, secret_key)
        print(colored("Scenario executed successfully!", color="green"))
    except Exception as e:
        print(colored("Error executing scenario:", color="red"), str(e))

def main():
    tool_name = "C N B A S"
    print_ascii_art(tool_name)

    cloud_choice = select_cloud_provider()
    scenario_choice = select_attack_scenario()
    access_key, secret_key = get_credentials()

    if scenario_choice == 1:
        # Pass the selected scenario module to execute
        execute_scenario(access_key, secret_key, scenario_module)
    elif scenario_choice == 2:
        print(colored("Scenario coming soon!", color="yellow"))

if __name__ == "__main__":
    main()

