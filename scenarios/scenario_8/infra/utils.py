import pulumi
from taggable import is_taggable
import sys

default_tags = {"Owner": "Osher", "Team": "Sparrow", "Project": "Cobra"}


# registerAutoTags registers a global stack transformation that merges a set
# of tags with whatever was also explicitly added to the resource definition.
def register_auto_tags(auto_tags):

    pulumi.runtime.register_stack_transformation(
        lambda args: auto_tag(args, auto_tags))


# auto_tag applies the given tags to the resource properties if applicable.
def auto_tag(args, auto_tags):
    if is_taggable(args.type_):
        args.props['tags'] = {**(args.props['tags'] or {}), **auto_tags}
        return pulumi.ResourceTransformationResult(args.props, args.opts)


def read_public_key(pub_key_path):
    # Read the public key from the file
    try:
        with open(pub_key_path, "r") as f:
            public_key = f.read().strip()
        return public_key
    except FileNotFoundError:
        print(f"Error: Public key file not found at {pub_key_path}",
              file=sys.stderr)
        print(
            "Please ensure the path '../../../id_rsa.pub' is correct relative to where you run 'pulumi up'.",
            file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading public key: {e}", file=sys.stderr)
        sys.exit(1)


# Make sure resources will be tagged with our default tags
register_auto_tags(default_tags)
