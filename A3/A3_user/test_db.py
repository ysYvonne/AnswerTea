import boto3
db3 = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name='us-west-2')

db3.meta.client.list_tables()
