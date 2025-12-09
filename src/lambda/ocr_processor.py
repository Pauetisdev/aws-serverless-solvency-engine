import json
import os
import boto3

# Initialize Textract client
textract_client = boto3.client('textract')

def handler(event, context):
    """
    Lambda function invoked by Step Functions (StartOCR state).
    It calls Amazon Textract to extract structured data from the input document URI.
    """
    print("--- OCR Processing Started ---")
    
    # --- 1. Input Validation and URI Extraction ---
    if 'Documents' not in event or not event['Documents']:
        raise ValueError("Input does not contain a 'Documents' list with S3 URIs.")

    # Get the URI for the first document (Nomina)
    nomina_document = event['Documents'][0]
    s3_uri = nomina_document['S3Uri']
    document_id = event["DocumentId"]
    
    # Extract Bucket and Key
    try:
        bucket_name = s3_uri.split('/')[2]
        key = '/'.join(s3_uri.split('/')[3:])
    except IndexError:
        raise ValueError(f"Invalid S3 URI format: {s3_uri}")

    # --- 2. Call to Textract (AnalyzeDocument) ---
    try:
        response = textract_client.analyze_document(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': key
                }
            },
            FeatureTypes=['FORMS', 'TABLES'] 
        )

        # --- 3. Return Result ---
        print(f"Textract analysis succeeded for {key}.")
        
        return {
            "DocumentId": document_id,
            "AnalysisStatus": "OCR_COMPLETED",
            "TextractRawResult": response 
        }

    except Exception as e:
        print(f"ERROR calling Textract for {key}: {e}")
        raise e