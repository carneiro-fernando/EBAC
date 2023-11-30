# Importação de bibliotecas
import os
import json
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
import boto3
import pyarrow as pa
import pyarrow.parquet as pq

# Função padrão do AWS Lambda
def lambda_handler(event: dict, context: dict) -> bool:
    """
    Função de manipulação do AWS Lambda para processar o evento e o contexto.

    Parâmetros:
    event (dict): O evento do AWS Lambda.
    context (dict): O contexto do AWS Lambda.

    Retorna:
    bool: Verdadeiro se a operação foi bem-sucedida, Falso caso contrário.
    """
    # Recuperar variáveis de ambiente
    RAW_BUCKET = os.environ['AWS_S3_RAW']
    ENRICHED_BUCKET = os.environ['AWS_S3_ENRICHED']

    # Inicializar variáveis lógicas
    tzinfo = timezone(offset=timedelta(hours=-3))
    date = (datetime.now(tzinfo) - timedelta(days=1)).strftime('%Y-%m-%d')
    timestamp = datetime.now(tzinfo).strftime('%Y%m%d%H%M%S%f')

    table = None
    client = boto3.client('s3')

    try:
        # Listar objetos no bucket raw com o prefixo especificado
        response = client.list_objects_v2(Bucket=RAW_BUCKET, Prefix=f'whatsapp/context_date={date}')
        df = pd.DataFrame()

        # Percorrer o conteúdo da resposta
        for content in response['Contents']:
            key = content['Key']
            # Baixar o arquivo do bucket raw para um local temporário
            client.download_file(RAW_BUCKET, key, f"/tmp/{key.split('/')[-1]}")

            # Abrir o arquivo baixado e carregar seu conteúdo JSON
            with open(f"/tmp/{key.split('/')[-1]}", mode='r', encoding='utf8') as fp:
                data = json.load(fp)

            # Analisar os dados e anexá-los ao dataframe
            if df.empty:
                df = parse_data(data=data)
            else:
                new_df = parse_data(data=data)
                df = pd.concat([df, new_df], axis=0, join='outer')

        # Converter o dataframe para uma Tabela PyArrow
        table = pa.Table.from_pandas(df)
        # Escrever a tabela em um arquivo Parquet
        pq.write_table(table=table, where=f'/tmp/{timestamp}.parquet')
        # Carregar o arquivo Parquet no bucket enriquecido
        client.upload_file(f"/tmp/{timestamp}.parquet", ENRICHED_BUCKET, f"whatsapp/context_date={date}/{timestamp}.parquet")

        return True

    except Exception as exc:
        # Registrar o erro e imprimi-lo
        logging.error(msg=exc)
        print(f'Erro: {exc}')

        return False 
        
# Função para extrair os dados desejados e transformar o dicionário (JSON) em um DataFrame      
def parse_data(data: dict) -> pd.DataFrame:
    """
    Analisa os dados fornecidos em um DataFrame do pandas.

    Parâmetros:
    data (dict): Os dados para analisar.

    Retorna:
    pd.DataFrame: Os dados analisados.
    """
    # Inicializa uma lista vazia para armazenar os dados
    data_list = []

    # Verifica se os dados são um dicionário e contém 'entry'
    if isinstance(data, dict) and "entry" in data:
        # Percorre a lista 'entry'
        for i in range(len(data["entry"])):
            entry = data["entry"][i]

            # Verifica se a entrada é um dicionário e contém 'changes'
            if isinstance(entry, dict) and "changes" in entry:
                # Percorre a lista 'changes'
                for j in range(len(entry["changes"])):
                    change = entry["changes"][j]

                    # Verifica se a alteração é um dicionário e contém 'value'
                    if isinstance(change, dict) and "value" in change:
                        # Obtém o dicionário 'value'
                        value = change["value"]

                        # Verifica se o valor é um dicionário e contém 'contacts' que deve ser uma lista
                        if isinstance(value, dict) and "contacts" in value and isinstance(value["contacts"], list):
                            # Percorre a lista 'contacts'
                            for k in range(len(value["contacts"])):
                                # Obtém o dicionário 'contact'
                                contact = value["contacts"][k]

                                # Verifica se o valor é um dicionário e contém 'messages' que deve ser uma lista
                                if isinstance(value, dict) and "messages" in value and isinstance(value["messages"], list):
                                    # Percorre a lista 'messages'
                                    for l in range(len(value["messages"])):
                                        # Obtém o dicionário 'message'
                                        message = value["messages"][l]

                                        # Cria uma linha com as colunas necessárias
                                        row = {
                                            "name": contact["profile"]["name"],
                                            "from": message["from"],
                                            "body": message["text"]["body"],
                                            "timestamp": message["timestamp"],
                                            "type": message["type"]
                                        }

                                        # Anexa a linha à lista de dados
                                        data_list.append(row)

    # Cria um dataframe a partir da lista de dados
    parsed_data = pd.DataFrame(data_list)

    return parsed_data