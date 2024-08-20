import json
import boto3
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    # Initialiser le client DynamoDB
    dynamodb = boto3.resource('dynamodb')
    
    # Nom de la table
    table_name = 'aws-question-solution-architect-associate'
    table = dynamodb.Table(table_name)
    
    # Récupérer l'id-question depuis l'événement
    id_question = event["pathParameters"]['id-question']
    
    # Rechercher l'objet dans DynamoDB en utilisant Query
    try:
        response = table.query(
            KeyConditionExpression=Key('id-question').eq(id_question)
        )
        
        # Vérifier si l'élément existe dans la table
        if 'Items' in response and response['Items']:
            question = response['Items'][0]
            question['options'] = question['options'].split('&&')
            return {
                'statusCode': 200,
                'body': json.dumps(question)
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Item not found'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
