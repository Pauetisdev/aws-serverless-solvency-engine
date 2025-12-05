# This is the initial placeholder Lambda function for the DocumentTriggerFunction.
# Its purpose is to allow the CI/CD pipeline (Fita 1) to deploy successfully.
# In later stages (Fita 4), this function will be updated to receive the S3 event
# and start the AWS Step Function State Machine.

import json
import os
import uuid
import boto3

# Initialize DynamoDB client using the standard AWS SDK (boto3)
# The table name is read from the environment variables (defined in template.yaml)
DYNAMODB_TABLE_NAME = os.environ.get('SOLVENCIA_RESULTS_TABLE', 'SolvenciaResultsTable')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


def handler(event, context):
    """
    Main handler function for the Lambda. Currently, it just logs the event
    and registers a placeholder item in DynamoDB for verification.
    """
    print("--- Document Trigger Function Started ---")
    print(f"Received event: {event}")

    # Placeholder logic to demonstrate DynamoDB access (Fita 1 verification)
    try:
        document_id = str(uuid.uuid4())
        
        # Write a simple placeholder entry to the DynamoDB table
        table.put_item(
            Item={
                'DocumentId': document_id,
                'Status': 'INITIALIZED_PLACEHOLDER',
                'Timestamp': context.get_remaining_time_in_millis()
            }
        )
        print(f"Successfully recorded placeholder ID: {document_id} in DynamoDB.")
        
        # In a real scenario (Fita 4), this Lambda would start the Step Function here.
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Lambda executed successfully (Placeholder)',
                'document_id': document_id
            })
        }

    except Exception as e:
        print(f"ERROR: Could not process request or write to DynamoDB. {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }