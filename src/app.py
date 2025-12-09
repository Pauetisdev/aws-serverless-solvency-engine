import json
import os
import uuid
import boto3

# Initialize the Step Functions client
sfn_client = boto3.client('stepfunctions')

# Read the State Machine ARN from the environment variables (set in template.yaml)
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN'] 

def handler(event, context):
    """
    Handler function invoked by the API Gateway (/documents POST).
    It initiates the Step Function workflow for document analysis (Fita 2).
    """
    print("--- Document Trigger Function Started ---")
    
    # 1. Generate a unique ID for this document/execution
    document_id = 'DOC-' + str(uuid.uuid4())
    execution_name = 'Execution-' + document_id
    
    # --- Input Data for the Step Function ---
    # This data is passed to the first state (StartOCR).
    # We use hardcoded S3 URIs for testing.
    input_data = {
        "DocumentId": document_id,
        "Documents": [
            {"Type": "Nomina", "S3Uri": "s3://pv-solvency-documents-2025/nomina.pdf"},
            {"Type": "Extracte", "S3Uri": "s3://pv-solvency-documents-2025/extracte.pdf"}
        ]
    }
    
    # 2. Start the Step Function execution
    try:
        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=execution_name,
            input=json.dumps(input_data)
        )
        
        # 3. Return success to the API Gateway caller (frontend)
        print(f"Workflow initiated successfully. Execution ARN: {response['executionArn']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # CORS header
            },
            'body': json.dumps({
                'message': 'Analysis initiated. Check Step Functions for status.',
                'execution_id': document_id
            })
        }

    except Exception as e:
        print(f"ERROR initiating Step Function: {e}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }