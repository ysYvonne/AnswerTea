import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from flask import url_for, redirect, request
from app import s3_config
from app import app

# dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def create_table():
    try:
        # create orders table
        dynamodb.create_table(
            TableName='orders',
            KeySchema=[
                {
                    'AttributeName': 'userId',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'orderId',
                    'KeyType': 'RANGE'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': "orderPriceIndex",
                    'KeySchema': [
                        {
                            'KeyType': 'HASH',
                            'AttributeName': 'orderprice'
                        },
                        {
                            'KeyType': 'RANGE',
                            'AttributeName': 'orderId'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'INCLUDE',
                        'NonKeyAttributes': ['orderdetails', 'orderstatus']
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': "orderStatusIndex",
                    'KeySchema': [
                        {
                            'KeyType': 'HASH',
                            'AttributeName': 'orderstatus'
                        },
                        {
                            'KeyType': 'RANGE',
                            'AttributeName': 'orderId'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    },
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'orderId',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'orderprice',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'orderstatus',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        #create users table
        dynamodb.create_table(
         TableName= "users",
         KeySchema= [
            {
                'AttributeName': 'userId',
                'KeyType': 'HASH'
            }
             ],
         GlobalSecondaryIndexes = [
            {
                'IndexName': "EmailPasswordIndex",
                'KeySchema': [
                    {
                        'AttributeName': 'email',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'password',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }
            },
            {
                'IndexName': "EmailUserIdIndex",
                'KeySchema': [
                    {
                        'AttributeName': 'email',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'userId',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }

            },
            {
                'IndexName': "EmailFirstNameIndex",
                'KeySchema': [
                    {
                        'AttributeName': 'email',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'firstName',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'KEYS_ONLY',
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }

            },
            {
                'IndexName': "EmailAllIndex",
                'KeySchema': [
                    {
                        'AttributeName': 'email',
                        'KeyType': 'HASH'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'INCLUDE',
                    'NonKeyAttributes': ['userId', 'email', 'firstName', 'lastName', 'address1', 'address2', 'zipcode',
                                         'city', 'province', 'country', 'phone']
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }

            }
        ],
        AttributeDefinitions = [
            {
                'AttributeName': 'userId',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'password',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'email',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'firstName',
                'AttributeType': 'S'
            }

        ],
        ProvisionedThroughput= {
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
        )

        #create products table
        dynamodb.create_table(
         TableName= 'products',
         KeySchema= [
            {
                'AttributeName': 'productId',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'productName',
                'KeyType': 'RANGE'
            }
         ],
         GlobalSecondaryIndexes= [
            {
                'IndexName': "PriceIndex",
                'KeySchema': [
                    {
                        'KeyType': 'HASH',
                        'AttributeName': 'price'
                    },
                    {
                        'KeyType': 'RANGE',
                        'AttributeName': 'productId'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'INCLUDE',
                    'NonKeyAttributes': ['description', 'image', 'stock', 'categoryId','youtuberId','videolink','RGB']
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }
            },
            {
                'IndexName': "categoryIndex",
                'KeySchema': [
                    {
                        'KeyType': 'HASH',
                        'AttributeName': 'categoryId'
                    },
                    {
                        'KeyType': 'RANGE',
                        'AttributeName': 'productId'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }
            },
            {
                'IndexName': "youtuberIndex",
                'KeySchema': [
                    {
                        'KeyType': 'HASH',
                        'AttributeName': 'youtuberId'
                    },
                    {
                        'KeyType': 'RANGE',
                        'AttributeName': 'productId'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 2,
                    'WriteCapacityUnits': 2
                }
            }
         ],
         AttributeDefinitions= [
            {
                'AttributeName': 'productId',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'productName',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'price',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'categoryId',
                'AttributeType': 'N'
            },
            {
                'AttributeName': 'youtuberId',
                'AttributeType': 'N'
            }
         ],
         ProvisionedThroughput= {
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
         }
        )

        #create kart table
        dynamodb.create_table(
            TableName="kart",
            KeySchema=[
                {
                    'AttributeName': 'userId',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'productId',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'userId',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'productId',
                    'AttributeType':'N'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        #create categories table
        dynamodb.create_table(
            TableName="categories",
            KeySchema=[
                {
                    'AttributeName': 'categoryId',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'categoryName',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'categoryId',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'categoryName',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # create youtubers table
        dynamodb.create_table(
            TableName="youtubers",
            KeySchema=[
                {
                    'AttributeName': 'youtuberId',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'youtuberName',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'youtuberId',
                    'AttributeType': 'N'
                },
                {
                    'AttributeName': 'youtuberName',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'ResourceInUseException':
            print("Table already exists.")
        else:
            print("Unknown exception occurred while querying for the table. Printing full error:")
            print(ce.response)


create_table()