#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Module providing a class for encapsulating COBRA scenarios."""
import importlib
import json
import webbrowser
from pathlib import Path
from termcolor import colored

import yaml
from pulumi import automation as auto

from core.helpers import slugify, pbar_sleep
from core.report import get_report


class Scenario(object):
    """Class encapsulating all methods needed to run a scenario."""
    def __init__(self, scenario_id):
        self.scenario_id = scenario_id
        self.scenario_label = 'scenario_{}'.format(scenario_id)
        try:
            self.infra_mod = importlib.import_module(
                '.{}.infra.extra'.format(self.scenario_label), 'scenarios_ng')
        except ModuleNotFoundError:
            self.infra_mod = None
        self.attack_mod = importlib.import_module(
            '.{}.attack'.format(self.scenario_label), 'scenarios_ng')
        self.config = self._get_config()
        self.title = self.config['title']
        self.description = self.config['description']
        self.slug = slugify(self.title)  # e.g. title-of-scenario
        self.output_path = self._get_output_path()

    def setup(self):
        """Deploy resources needed for the scenario."""
        # TODO: logging instead of print here and elsewhere
        print(colored('Deploying scenario infrastructure', color='red'))
        self._deploy_infra()
        if self.infra_mod:
            self.infra_mod.deploy_additional_resources()

    def attack(self):
        """Run the attack scenario on the deployed infra/resources."""
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
        print(colored('Destroying scenario infrastructure', color='red'))
        self._destroy_infra()
        if self.infra_mod:
            with open(self.output_path, 'r') as f:
                data = json.load(f)
            print(colored("Deleting manually created resources not tracked by Pulumi's state", color="red"))
            self.infra_mod.destroy_additional_resources(data)

    def generate_report(self):
        """Generate report."""
        with open(self.output_path, 'r') as f:
            output_data = json.load(f)
        report = get_report(self.scenario_label, self.config, output_data)
        report_path = Path(__file__).parent.parent \
            / 'files' / 'var' / 'reports' / '{}_report.html'.format(
                self.scenario_label)
        with open(report_path, 'w+') as file:
            file.write(report)
        webbrowser.open_new_tab('file://{}'.format(report_path))

    def _get_stack(self):
        stack_dir = Path(__file__).parent.parent / 'scenarios_ng' / self.scenario_label / 'infra' / 'stack'
        stack = auto.create_or_select_stack(
            # TODO: support for Pulumi programs defined as a function
            # see https://www.pulumi.com/docs/reference/pkg/python/pulumi/#module-pulumi.automation
            # project_name='cobra',
            # program=self.infra_mod.pulumi_program
            stack_name=self.scenario_label,
            work_dir=stack_dir
        )
        stack.workspace.install_plugin('aws', 'v4.0.0')
        # stack.set_config('aws:region', auto.ConfigValue(value='us-east-2'))
        stack.refresh(on_output=print)
        return stack

    def _deploy_infra(self):
        """Deploy required IaC infrastructure."""
        stack = self._get_stack()
        stack.up(on_output=print)
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
        config_path = Path(__file__).parent.parent \
            / 'scenarios_ng' / self.scenario_label / '_files' / 'config.yaml'
        with open(config_path, 'r') as file_:
            config = yaml.load(file_, Loader=yaml.SafeLoader)
        return config

    def _get_output_path(self):
        output_path = Path(__file__).parent.parent \
            / 'files' / 'var' / 'output' / '{}.json'.format(
                self.scenario_label)
        return output_path
