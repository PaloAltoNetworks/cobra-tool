from pathlib import Path
from string import Template

# data = {
#     'title': 'This is the title',
#     'subtitle': 'And this is the subtitle',
#     'list': '\n'.join(['first', 'second', 'third'])
# }


def _format_attack_steps(steps):
    html_steps = []
    for step in steps:
        html_steps.append('<p>{}</p>'.format(step))
    return ''.join(html_steps)


def _format_resources(resources):
    html_resources = []
    for key in resources.keys():
        html_resources.append(
            '<tr><td class="resource-type">{}</td><td>{}</td></tr>'.format(
                key, resources[key]
            )
        )
    return ''.join(html_resources)


def _format_controls(controls):
    html_controls = []
    for control in controls:
        html_controls.append('<tr><td>{}</td></tr>'.format(control))
    return ''.join(html_controls)


def get_report(scenario_label, config, output_data):
    template_path = Path(__file__).parent.parent / 'files' / 'templates' / 'report.html'
    report_image_path = Path(__file__).parent.parent / 'scenarios_ng' / scenario_label / '_files'
    report_data = {
        'attack_explanation': config['attack_explanation'],
        'attack_steps': _format_attack_steps(config['attack_steps']),
        'resources': _format_resources(output_data),
        'controls': _format_controls(config['post_attack_controls_eval_steps']),
        'path': report_image_path
    }
    with open(template_path, 'r') as f:
        src = Template(f.read())
        result = src.substitute(report_data)
    return result
