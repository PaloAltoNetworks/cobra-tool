#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Module providing a class for encapsulating COBRA scenarios."""
import importlib
import json
import os
from termcolor import colored

import yaml
from pulumi import automation as auto

from core.helpers import slugify, pbar_sleep


class Scenario(object):
    """Class encapsulating all methods needed to run a scenario."""
    def __init__(self, scenario_id):
        self.scenario_id = scenario_id
        self.scenario_label = 'scenario_{}'.format(scenario_id)
        self.infra_mod = importlib.import_module(
            '.{}.infra.main'.format(self.scenario_label), 'scenarios_ng')
        self.attack_mod = importlib.import_module(
            '.{}.attack'.format(self.scenario_label), 'scenarios_ng')
        config = self._get_config()
        self.title = config['title']
        self.description = config['description']
        self.slug = slugify(self.title)  # e.g. title-of-scenario
        self.output_path = self._get_output_path()

    def setup(self):
        """Deploy resources needed for the scenario."""
        self._deploy_infra()
        # TODO: execute extra resources module if exists

    def attack(self):
        """Run the attack scenario on the deployed infra/resources."""
        # TODO: logging instead of print here and elsewhere
        print(colored("Executing attack...", color="red"))
        # TODO: sleep to ensure deployed resources are available?
        #   Need more reliable way to do this?  (e.g. Pulumi API callback?)
        pbar_sleep(10)
        # TODO: Exception handling if no data
        with open(self.output_path, 'r') as f:
            data = json.load(f)
        result = self.attack_mod.attack(data)
        if (result):
            # TODO: logging instead of print
            print(colored('Attack succeeded', color='red'))
        else:
            print(colored('Attack failed', color='red'))

    def destroy(self):
        """Destroy scenario resources and clean up."""
        self._destroy_infra()
        # TODO: logic to destroy additional resources not managed by Pulumi

    def generate_report(self):
        """Generate report."""
        print('Reporting not yet implemented.')
        # TODO
        # html_template = ''
        # with open('cobra-report-{}.html'.format(self.slug), 'w+') as file:
        #     file.write(html_template)
        # webbrowser.open_new_tab(
        #     'file://{}/cobra-report-{}.html'.format(str(Path.cwd()), self.slug)
        # )

    def _get_stack(self):
        project_name = 'cobra'
        stack = auto.create_or_select_stack(
            stack_name=self.scenario_label,
            project_name=project_name,
            program=self.infra_mod.pulumi_program
        )
        stack.workspace.install_plugin('aws', 'v4.0.0')
        # stack.set_config('aws:region', auto.ConfigValue(value='us-east-2'))
        stack.refresh(on_output=print)
        return stack

    def _deploy_infra(self):
        """Deploy required IaC infrastructure."""
        stack = self._get_stack()
        up_res = stack.up(on_output=print)
        # TODO: is this the right way to handle Pulumi outputs?
        outputs = stack.outputs()
        outputs_dict = {}
        for key in outputs.keys():
            outputs_dict[key] = outputs[key].value
        with open(self.output_path, 'w') as file_:
            file_.write(json.dumps(outputs_dict))

    def _destroy_infra(self):
        """Destroy the IaC stack."""
        stack = self._get_stack()
        stack.destroy(on_output=print)

    def _get_config(self):
        config_path = os.path.join(  # FIXME: use pathlib instead
            os.path.dirname(__file__),
            '..', 'scenarios_ng', self.scenario_label, '_files', 'config.yaml')
        with open(config_path, 'r') as file_:
            config = yaml.load(file_, Loader=yaml.SafeLoader)
        return config

    def _get_output_path(self):
        output_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'files', 'var', 'output',
            '{}.json'.format(self.scenario_label),
        )
        return output_path
