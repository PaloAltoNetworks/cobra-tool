#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Module providing a class for encapsulating COBRA scenarios."""
from termcolor import colored

from core.helpers import print_ascii_art, get_scenarios_config
from core.scenario import Scenario


def select_attack_scenario(cloud_provider):
    """Get attack scenario config."""
    scenarios_config = get_scenarios_config()
    keys = list(scenarios_config.keys())
    keys.sort()
    print(colored('Select Attack Scenario of %s:', color='yellow') % cloud_provider)
    choices = []
    for key in keys:
        index = int(key[-1:])
        choices.append(index)
        print(colored('{}. {}: {}'.format(
            index, scenarios_config[key]['title'], scenarios_config[key]['description']),
            color='green'))
    while True:
        try:
            choice = int(input(colored('Enter your choice: ', color='yellow')))
            if choice not in choices:
                raise ValueError(colored('Invalid choice.', color='red'))
            return choice
        except ValueError as e:
            print(e)


def main(cloud_provider, action, simulation, scenario):
    """Instantiate and run an attack scenario."""
    tool_name = 'C O B R A'
    print_ascii_art(tool_name)
    scenario_choice = select_attack_scenario(cloud_provider)
    scenario = Scenario(scenario_choice)
    if action == 'launch':
        if simulation:
            # TODO: what to do with cloud provider?
            scenario.setup()
            scenario.attack()
            # scenario.destroy()
            # TODO: ^^^ do we really want to destroy the infra immediately?
            #   there's a separate command for destroy
            scenario.generate_report()  # TODO: not implemented
    elif action == 'status':
        # TODO
        # subprocess.call('cd ./scenarios/scenario_2/infra/ && pulumi stack ls', shell=True)
        pass
    elif action == 'destroy':
        scenario.destroy()
        pass
    else:
        print('No options provided. --help to know more')


if __name__ == '__main__':
    main()
