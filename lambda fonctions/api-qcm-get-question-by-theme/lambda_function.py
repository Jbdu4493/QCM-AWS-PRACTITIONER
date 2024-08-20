import json
import boto3
from boto3.dynamodb.conditions import Attr

def lambda_handler(event, context):
    # Initialiser le client DynamoDB
    dynamodb = boto3.resource('dynamodb')
    
    # Nom de la table
    table_name = 'aws-question-solution-architect-associate'
    table = dynamodb.Table(table_name)
    
    # Récupérer l'id-question depuis l'événement
    theme = event['pathParameters']['theme']
    
    # Rechercher l'objet dans DynamoDB en utilisant Scan
    try:
        response = table.scan(
            FilterExpression=Attr('theme').eq(theme)
        )
        
        # Vérifier si l'élément existe dans la table
        if 'Items' in response and response['Items']:
            questions = response['Items']
            for i in range(len(questions)):
                questions[i]['options']= questions[i]['options'].split('&&')
            return {
                'statusCode': 200,
                'body': json.dumps(questions)
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
