import json
import boto3
import uuid
from datetime import datetime

def lambda_handler(event, context):
    # Initialiser le client DynamoDB
    dynamodb = boto3.resource('dynamodb')
    
    # Nom de la table
    table_name = 'qcm-event'
    table = dynamodb.Table(table_name)
    
    # Récupérer les paramètres de requête
    id_question = event["queryStringParameters"]["id-question"]
    event_type = event["queryStringParameters"]["event-type"]
    theme = event["queryStringParameters"]["theme"]
    # Générer un UUID pour id-event
    id_event = str(uuid.uuid4())
    
    # Obtenir le timestamp actuel
    timestamp = datetime.utcnow().isoformat()
    
    # Créer l'élément à insérer
    item = {
        'id-question': id_question,
        'timestamp': timestamp,
        'id-event': id_event,
        "event-type":event_type,
        "theme":theme
    }
    
    # Insérer l'élément dans DynamoDB
    try:
        table.put_item(Item=item)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Item added successfully', 'item': item})
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
