import json
import boto3
import requests
import urllib.parse
import uuid
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

def get_question(record):
    try:
        bucket = record['s3']["bucket"]["name"]
        file_name = record['s3']["object"]["key"]
        file_name = urllib.parse.unquote(file_name).replace("+", " ")
        print(file_name)
        params = {
            'bucket': bucket,
            "object_key": file_name
        }
        params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        try:
            r = requests.get("http://172.31.45.236:8000/get-question-json-s3", params=params, headers={
                'Content-Type': 'application/json'})
            r.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
        except requests.exceptions.RequestException as e:
            print(f"Error fetching question data: {e}")
            return None
        
        try:
            question = r.json()
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            return None

        question["id-question"] = str(uuid.uuid4())
        question["img_path"] = "s3://" + bucket + "/" + file_name
        if "embedding" in question:
            del question["embedding"]
            question["options"] = "&&".join(question["options"])
        print("question: ", question)
        return question
    except KeyError as e:
        print(f"Key error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def lambda_handler(event, context):
    print(event)
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table("aws-question-solution-architect-associate")
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error initializing DynamoDB resource: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error initializing DynamoDB resource'})
        }
    except Exception as e:
        print(f"Unexpected error initializing DynamoDB resource: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Unexpected error initializing DynamoDB resource'})
        }
    
    questions = []
    for r in event.get('Records', []):
        question = get_question(r)
        if question:
            try:
                response = table.put_item(Item=question)
                print(f"Successfully put item: {response}")
                questions.append(question["id-question"])
            except ClientError as e:
                print(f"ClientError saving question to DynamoDB: {e.response['Error']['Message']}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': f"ClientError saving question to DynamoDB: {e.response['Error']['Message']}"})
                }
            except Exception as e:
                print(f"Error saving question to DynamoDB: {e}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': f"Error saving question to DynamoDB: {e}"})
                }
    
    return {
        'statusCode': 200,
        'body': json.dumps(questions)
    }
