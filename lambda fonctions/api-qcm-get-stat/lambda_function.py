import boto3
import json

def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    print(event)
    
    # Extract the theme from the Lambda event
    theme = event["queryStringParameters"].get('theme', "default_theme")
    
    try:
        # Execute the SQL-like statement on DynamoDB
        response = dynamodb.meta.client.execute_statement(
            Statement=f"SELECT * FROM \"qcm-event\" WHERE \"theme\" = '{theme}'",
        )
        print(response)
        
        # Return the result as a JSON dictionary
        return {
            'statusCode': 200,
            'body': json.dumps(response['Items'])
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }
