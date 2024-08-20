import json
import boto3

def lambda_handler(event, context):
    # Initialiser le client DynamoDB
    dynamodb = boto3.resource('dynamodb')
    
    # Nom de la table
    table_name = 'aws-question-solution-architect-associate'
    table = dynamodb.Table(table_name)
    
    try:
        # Scanner la table pour récupérer uniquement les valeurs de theme
        response = table.scan(
            ProjectionExpression='theme'
        )
        
        themes = set()
        
        # Ajouter chaque valeur de theme à l'ensemble pour obtenir des valeurs distinctes
        for item in response['Items']:
            themes.add(item['theme'])
        
        return {
            'statusCode': 200,
            'body': json.dumps(list(themes))
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
