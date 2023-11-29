import json
import os
import logging
import boto3
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
   
    # Variáveis de ambiente
    BUCKET = os.environ['AWS_S3_BUCKET']
    
    # Declaração de variáveis
    tzinfo = timezone(offset=timedelta(hours=-3))
    date = datetime.now(tzinfo).strftime('%Y-%m-%d')
    timestamp = datetime.now(tzinfo).strftime('%Y%m%d%H%M%S%f')
    filename = f'{timestamp}.json'
    
    # Instanciando client S3
    client = boto3.client('s3')
    
    try:
        message = json.loads(event["body"])
        
        with open(f"/tmp/{filename}", mode='w', encoding='utf8') as fp:
            json.dump(message, fp)
        
        client.upload_file(f'/tmp/{filename}', BUCKET, f'whatsapp/context_date={date}/{filename}')
    
    except Exception as exc:
        logging.error(msg=exc)
        return dict(statusCode="500")
    

    # Verificação do Webhook
    VERIFY_TOKEN = 'verificacao'   
    # Check if 'queryStringParameters' is in the event and is not None
    if event.get('queryStringParameters'):
        mode = event['queryStringParameters'].get('hub.mode')
        token_sent = event['queryStringParameters'].get('hub.verify_token')
        
        if mode == 'subscribe' and token_sent == VERIFY_TOKEN:
            return {
                'statusCode': 200,
                'body': event['queryStringParameters']['hub.challenge']
            }
        else:
            return {
                'statusCode': 403,
                'body': 'Nao corresponde'
            }

    response_body = {
        'status': 'success',
        'message': 'Success, but queryStringParameters is not present',
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response_body)
    }