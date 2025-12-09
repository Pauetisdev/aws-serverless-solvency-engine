import json
import os
import boto3

# Initialize Bedrock Runtime client and DynamoDB client
bedrock_client = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

# Table name is read directly from the environment context
DYNAMODB_TABLE_NAME = 'solvency-results-table' 
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def handler(event, context):
    """
    Lambda function invoked by Step Functions (Final Decision).
    It uses Bedrock to make the final decision and writes to DynamoDB.
    """
    print("--- Final Decision Logic (Bedrock) Started ---")
    
    # --- 1. Get Data from Step Functions Input ---
    if 'TextractResult' not in event:
        # This means the OCR step failed or input was malformed
        raise ValueError("Input missing TextractResult from previous step.")

    document_id = event["DocumentId"]
    
    # --- 2. Simulate Metric Extraction & Ratio Calculation ---
    # These values would typically be extracted from the complex TextractRawResult JSON.
    try:
        sou_net = 2100.00 
        deute_mensual_fix = 650.00
        ingressos_nets_banc = 2100.00
        ratio = (deute_mensual_fix / sou_net) * 100
        
    except Exception:
        ratio = 999 

    # --- 3. Prepare the Prompt for Bedrock (using Claude Haiku) ---
    prompt_text = f"""
    You are a professional financial risk analyst. Based on the extracted data, make a final decision.
    
    RULES:
    1. If Calculated_Ratio > 40%, the decision is REJECTED.
    2. If Calculated_Ratio is between 25% and 40%, the decision is MANUAL_REVIEW.
    3. If Calculated_Ratio is < 25% AND Bank_Income matches Net_Salary, the decision is APPROVED.
    4. If Bank_Income != Net_Salary (Possible fraud/mismatch), the decision is MANUAL_REVIEW (Alert).
    
    DATA:
    - Net_Salary_Nomina: {sou_net}
    - Total_Fixed_Debt: {deute_mensual_fix}
    - Bank_Income: {ingressos_nets_banc}
    - Calculated_Ratio: {ratio:.2f}%
    
    Provide the final output as a JSON object, following this strict schema:
    {{
        "Decision": "APPROVED" | "REJECTED" | "MANUAL_REVIEW",
        "Ratio": "{ratio:.2f}%",
        "Reasoning": "Brief explanation based on the rules."
    }}
    """
    
    # --- 4. Call Bedrock ---
    final_decision_data = {"Decision": "MANUAL_REVIEW", "Ratio": f"{ratio:.2f}%", "Reasoning": "LLM failed to return valid JSON structure."}
    try:
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "prompt": prompt_text,
                "max_tokens_to_sample": 500,
                "temperature": 0.0
            })
        )
        
        response_body = json.loads(response['body'].read())
        llm_output_text = response_body['completion'].strip()
        
        # Clean and parse JSON from LLM
        if llm_output_text.startswith('```json'):
            llm_output_text = llm_output_text.strip('```json').strip('```')
        
        final_decision_data = json.loads(llm_output_text)
        
    except Exception as e:
        print(f"Bedrock/Parsing Error: {e}")

    # --- 5. Store Final Result in DynamoDB (Fita 4) ---
    try:
        table.put_item(
            Item={
                'DocumentId': document_id,
                'Status': final_decision_data['Decision'],
                'Ratio': final_decision_data['Ratio'],
                'DecisionReason': final_decision_data['Reasoning'],
                'Timestamp': context.get_remaining_time_in_millis()
            }
        )
        
    except Exception as e:
        print(f"DynamoDB Write Error: {e}")
        
    # Return the output for the Step Function (Fita 5/Notificació)
    return final_decision_data