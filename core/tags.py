"""
Global resource tags loader.

Reads tags from the project-root tags.yaml and exposes them as a dictionary
that can be merged into any cloud resource's tags parameter.

Usage in Pulumi infra code (AWS):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from core.tags import get_global_tags

    global_tags = get_global_tags()
    # Merge with resource-specific tags:
    tags = {**global_tags, "Name": "my-resource"}

Usage in Pulumi infra code (GCP - labels must be lowercase):
    from core.tags import get_global_labels
    global_labels = get_global_labels()
"""

import os
import re
import yaml


_TAGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'tags.yaml')


def _load_raw_tags() -> dict:
    """Load raw tags from tags.yaml.

    Returns:
        Dictionary of raw tag key-value pairs, or empty dict on error.
    """
    tags_path = os.path.abspath(_TAGS_FILE)

    if not os.path.exists(tags_path):
        print(f"[WARNING] Global tags file not found at {tags_path}. No global tags will be applied.")
        return {}

    try:
        with open(tags_path, 'r') as f:
            raw = yaml.safe_load(f)

        if not isinstance(raw, dict):
            print(f"[WARNING] tags.yaml is not a valid YAML mapping. No global tags will be applied.")
            return {}

        return {str(k): str(v) for k, v in raw.items()}

    except Exception as e:
        print(f"[WARNING] Failed to read tags.yaml: {e}. No global tags will be applied.")
        return {}


def get_global_tags() -> dict:
    """Load global tags for AWS/Azure resources.

    Returns:
        Dictionary of tag key-value pairs (all values as strings).
    """
    return _load_raw_tags()


def get_global_labels() -> dict:
    """Load global tags as GCP-compatible labels.

    GCP labels must:
    - Have lowercase keys and values
    - Use hyphens instead of special characters
    - Start with a letter

    Returns:
        Dictionary of GCP-compatible label key-value pairs.
    """
    raw = _load_raw_tags()
    labels = {}
    for k, v in raw.items():
        # Convert to lowercase, replace non-alphanumeric chars with hyphens
        label_key = re.sub(r'[^a-z0-9_-]', '-', k.lower()).strip('-')
        label_val = re.sub(r'[^a-z0-9_-]', '-', v.lower()).strip('-')
        if label_key:
            labels[label_key] = label_val
    return labels
