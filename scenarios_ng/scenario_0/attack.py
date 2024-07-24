from core.helpers import http_request


def attack(output):
    """Exfiltrate an S3 object from a public bucket."""
    url = 'https://{}.s3.amazonaws.com/{}'.format(
        output['s3-bucket-id'], output['s3-object-id'])
    print('Running attack scenario on {}'.format(url))
    # TODO: replace print with logging
    resp = http_request(url)
    if resp.status_code == 200:
        # TODO: is this the right way to check for attack success?
        return True
    else:
        # TODO: how to flag failed attack? raise custom exception?
        return False
