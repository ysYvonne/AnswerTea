import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from app import s3_config

a3bucketName = 'ece1779a3itemsbucket'

# dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="http://localhost:8000")
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def max_userID():
    table = dynamodb.Table('users')
    records = []
    response = table.scan(
        ProjectionExpression="userId"
    )
    for i in response['Items']:
        records.append(i['userId'])

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ProjectionExpression="userId",
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for i in response['Items']:
            records.append(i['userId'])
    if len(records) != 0:
        return max(records)
    else:
        return 0

def users_put(password,email,firstName,userdetail):
    userId = max_userID()+1
    lastName = userdetail[0]
    address1 = userdetail[1]
    address2 = userdetail[2]
    zipcode = userdetail[3]
    city = userdetail[4]
    province = userdetail[5]
    country = userdetail[6]
    phone = userdetail[7]
    table = dynamodb.Table('users')
    table.put_item(
        Item={
            'userId': userId,
            'password': password,
            'email': email,
            'firstName': firstName,
            'lastName': lastName,
            'address1': address1,
            'address2': address2,
            'zipcode': zipcode,
            'city': city,
            'province': province,
            'country': country,
            'phone': phone
        }
    )

def products_put(productId,productName,price,description,image,stock,categoryId,youtuberId,videolink,RGB):
    table = dynamodb.Table('products')

    table.put_item(
        Item={
            'productId': productId,
            'productName': productName,
            'price': price,
            'description': description,
            'image': image,
            'stock': stock,
            'categoryId': categoryId,
            'youtuberId': youtuberId,
            'videolink': videolink,
            'RGB':RGB

        }
    )

def kart_getproductId_amount(userId,productId):
    table = dynamodb.Table('kart')
    response = table.query(
        KeyConditionExpression=Key('userId').eq(userId) & Key('productId').eq(productId)
    )
    records = []
    for i in response['Items']:
        records.append(i['amount'])
    return records


def kart_put(userId, productId,amount):
    current_amount = kart_getproductId_amount(userId,productId)
    if len(current_amount) != 0:
        amount = current_amount[0] + amount
    table = dynamodb.Table('kart')
    table.put_item(
        Item={
                'userId': userId,
                'productId': productId,
                'amount': amount
        }
    )


def userId_getMaxOrderId(userId):
    table = dynamodb.Table('orders')
    response = table.query(
        KeyConditionExpression=Key('userId').eq(userId)
    )
    records = []
    for i in response['Items']:
        records.append(i['orderId'])
    if len(records) != 0:
        return max(records)
    else:
        return 0


def order_put(userId, orderdetails, orderprice, orderstatus):
    current_orderId = userId_getMaxOrderId(userId)
    orderId = current_orderId + 1
    table = dynamodb.Table('orders')
    table.put_item(
        Item={
                'userId': userId,
                'orderId': orderId,
                'orderdetails': orderdetails,
                'orderprice': orderprice,
                'orderstatus': orderstatus
        }
    )

def orders_get(userId):
    table = dynamodb.Table('orders')
    response = table.query(
        KeyConditionExpression=Key('userId').eq(userId)
    )
    records = []
    for i in response['Items']:
        records.append([i['userId'],i['orderId'],i['orderdetails'],i['orderprice'],i['orderstatus']])
    return records

def orders_getall():
    table = dynamodb.Table('orders')
    records = []
    response = table.scan(
        ProjectionExpression="userId, orderId, orderdetails, orderprice, orderstatus"
    )
    for i in response['Items']:
        records.append([i['userId'],i['orderId'],i['orderdetails'],i['orderprice'],i['orderstatus']])

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ProjectionExpression="userId",
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for i in response['Items']:
            records.append([i['userId'],i['orderId'],i['orderdetails'],i['orderprice'],i['orderstatus']])
    return records


def orders_update(userId,orderId):
    table = dynamodb.Table('orders')
    table.update_item(
        Key={
            'userId': userId,
            'orderId': orderId
        },
        ConditionExpression = Key('userId').eq(userId) & Key('orderId').eq(orderId),
        UpdateExpression='SET orderstatus = :os',
        ExpressionAttributeValues ={
            ':os': "completed"
        }
    )

def kart_removeAll(userId,productId):
    table = dynamodb.Table('kart')
    table.delete_item(
        Key={
            'userId': userId,
            'productId': productId
        }
    )

def kart_removeOne(userId,productId):
    currentamount = kart_getproductId_amount(userId, productId)
    amount = currentamount[0] - 1
    if amount == 0:
        kart_removeAll(userId,productId)
    else:
        table = dynamodb.Table('kart')
        table.update_item(
            Key={
                    'userId': userId,
                    'productId': productId
                },
                ConditionExpression=Key('userId').eq(userId) & Key('productId').eq(productId),
                UpdateExpression='SET amount = :amt',
                ExpressionAttributeValues={
                    ':amt': amount
                }
            )

def get_productId_stock_amount(productId):
    table = dynamodb.Table('products')
    response = table.query(
        KeyConditionExpression=Key('productId').eq(productId)
    )
    records = []
    for i in response['Items']:
        records.append(i['stock'])
    return records


def restock_update(productId, new_amount):
    product_detail = products_productId_search(int(productId))
    productName = product_detail[0]['productName']
    table = dynamodb.Table("products")
    table.update_item(
        Key={
            'productId': int(productId),
            'productName': productName
        },
        ConditionExpression=Key('productId').eq(int(productId)) & Key('productName').eq(productName),
        UpdateExpression='SET stock = :stk',
        ExpressionAttributeValues={
            ':stk': int(new_amount)
        }
    )


def stock_update(productId, change_amount):
    current_stock_amount = get_productId_stock_amount(productId)[0]
    product_detail = products_productId_search(productId)
    productName = product_detail[0]['productName']
    if current_stock_amount <= 0:
        return  [-1, productName + " item out of Stock! Please check your order"]
    new_amount = current_stock_amount - change_amount
    if new_amount < 0:
        table = dynamodb.Table("products")
        table.update_item(
            Key={
                'productId': productId,
                'productName': productName
            },
            ConditionExpression=Key('productId').eq(productId) & Key('productName').eq(productName),
            UpdateExpression='SET stock = :stk',
            ExpressionAttributeValues={
                ':stk': 0
            }
        )
        return [current_stock_amount, productName + " current stock amount is: " + str(current_stock_amount) + " Your order has amount: " \
                + str(change_amount) + ". All stock amount has been placed in your order. "]
    else:
        table = dynamodb.Table("products")
        table.update_item(
            Key={
                'productId': productId,
                'productName': productName
            },
            ConditionExpression=Key('productId').eq(productId) & Key('productName').eq(productName),
            UpdateExpression='SET stock = :stk',
            ExpressionAttributeValues={
                ':stk': new_amount
            }
        )
        return [0]


def users_email_password(email):
    table = dynamodb.Table('users')

    response = table.query(
        IndexName='EmailPasswordIndex',
        KeyConditionExpression=Key('email').eq(email)
    )
    records = []
    for i in response['Items']:
        records.append([i['email'],i['password']])
    return records

def users_email_userId(email):
    table = dynamodb.Table('users')

    response = table.query(
        IndexName='EmailUserIdIndex',
        KeyConditionExpression=Key('email').eq(email)
    )
    records = []
    for i in response['Items']:
        records.append([i['email'],i['userId']])
    return records

def users_getemail(userId):
    table = dynamodb.Table('users')
    response = table.query(
        KeyConditionExpression=Key('userId').eq(userId)
    )
    records = []
    for i in response['Items']:
        records.append(i['email'])
    return records


def kart_userId_productId(userId):
    table = dynamodb.Table('kart')

    response = table.query(
        KeyConditionExpression=Key('userId').eq(userId)
    )
    records = []
    for i in response['Items']:
        records.append(i)
    return records

def kart_get(userId):
    table = dynamodb.Table('kart')

    response = table.query(
        KeyConditionExpression=Key('userId').eq(userId)
    )
    records = []
    for i in response['Items']:

        product_detail = products_productId_search(i['productId'])
        imageurl = s3_config.get_element_from_bucket(a3bucketName, product_detail[0]['image'])
        records.append([i['userId'], i['productId'], i['amount'],product_detail[0]['productName'],imageurl,
                        product_detail[0]['price'],format(int(i['amount'])*float(product_detail[0]['price']),'.2f')])
    return records


def users_email_firstName(email):
    table = dynamodb.Table('users')

    response = table.query(
        IndexName='EmailFirstNameIndex',
        KeyConditionExpression=Key('email').eq(email)
    )
    records = []
    for i in response['Items']:
        records.append([i['email'],i['firstName']])
    return records


def users_email_all(email):
    table = dynamodb.Table('users')

    response = table.query(
        IndexName='EmailAllIndex',
        KeyConditionExpression=Key('email').eq(email)
    )
    records = []
    for i in response['Items']:
        records.append([i['userId'],i['email'],i['firstName'],i['lastName'],i['address1'],i['address2'],
                       i['zipcode'],i['city'],i['province'],i['country'],i['phone']])
    return records


def users_update_password_userId(userId,password):
    table = dynamodb.Table('users')
    table.update_item(
        Key={
            'userId': userId
        },
        ConditionExpression = Key('userId').eq(userId),
        UpdateExpression='SET password = :r',
        ExpressionAttributeValues ={
            ':r': password
        }
    )


def users_update_all_userId(userId,email,firstName,userdetail):
    table = dynamodb.Table('users')
    lastName = userdetail[0]
    address1 = userdetail[1]
    address2 = userdetail[2]
    zipcode = userdetail[3]
    city = userdetail[4]
    province = userdetail[5]
    country = userdetail[6]
    phone = userdetail[7]
    table.update_item(
        Key={
            'userId': userId
        },
        ConditionExpression=Key('userId').eq(userId),
        UpdateExpression='SET firstName = :fn, lastName = :ln, address1 = :a1, address2 = :a2, zipcode = :zp, city = :ct, province = :pn, country = :cy,  phone = :ph' ,
        ExpressionAttributeValues={
            ':fn': firstName,
            ':ln': lastName,
            ':a1': address1,
            ':a2': address2,
            ':zp': zipcode,
            ':ct': city,
            ':pn': province,
            ':cy': country,
            ':ph': phone
        }
    )


def check_table_availability(table_name):
    try:
        table = dynamodb.Table(table_name)
        is_table_existing = table.table_status in ("CREATING", "UPDATING","DELETING", "ACTIVE")
    except ClientError:
        is_table_existing = False
        print("Table %s doesn't exist." % table.name)
        return is_table_existing

    if is_table_existing and table.table_status == "CREATING":
        print("Table %s is creating." % table.name)
        table.wait_until_exists()
        return is_table_existing
    elif table.table_status == "DELETING":
        is_table_existing = False
        print("Table %s is deleting." % table.name)
        return is_table_existing

    else:
        return is_table_existing


def products_list_all():
    records = []
    if check_table_availability('products'):
        table = dynamodb.Table('products')
        response = table.scan(
            ProjectionExpression="productId, productName, price, description, image, stock"
        )

        for i in response['Items']:
            imageurl = s3_config.get_element_from_bucket(a3bucketName, i['image'])
            records.append([[i['productId'], i['productName'], i['price'], i['description'], imageurl,i['stock']]])

        while 'LastEvaluatedKey' in response:
            response=table.scan(
                ProjectionExpression="productId, productName, price, description, image, stock",
                ExclusiveStartKey=response['LastEvaluatedKey']
            )

            for i in response['Items']:
                imageurl = s3_config.get_element_from_bucket(a3bucketName, i['image'])
                records.append([[i['productId'], i['productName'], i['price'], i['description'], imageurl,i['stock']]])
        return records
    else:
        return records


def max_productID():
    table = dynamodb.Table('products')
    records = []
    response = table.scan(
        ProjectionExpression="productId"
    )
    for i in response['Items']:
        records.append(i['productId'])

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ProjectionExpression="productId",
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        for i in response['Items']:
            records.append(i['productId'])
    if len(records) != 0:
        return max(records)
    else:
        return 0


def products_productId_search(productId):
    table = dynamodb.Table('products')
    response = table.query(
        KeyConditionExpression=Key('productId').eq(productId)
    )
    records = []
    for i in response['Items']:
        records.append(i)

    return records

def products_in_category(categoryId):
    table = dynamodb.Table('products')
    response = table.query(
        IndexName='categoryIndex',
        KeyConditionExpression=Key('categoryId').eq(categoryId)
    )
    records = []

    for i in response['Items']:
        imageurl = s3_config.get_element_from_bucket(a3bucketName, i['image'])
        records.append([[i['productId'],i['productName'],i['price'],imageurl]])
    return records


def get_category_name(categoryId):
    table = dynamodb.Table('categories')
    response = table.query(
        KeyConditionExpression=Key('categoryId').eq(categoryId)
    )
    records = []

    for i in response['Items']:
        records.append(i['categoryName'])
    return records


def products_delete_productId(productId):
    table = dynamodb.Table('products')
    result = products_productId_search(productId)
    table.delete_item(
        Key = {
            'productId': productId,
            'productName':result[0]['productName']
        }
    )
    print(result[0]['image'])
    s3 = s3_config.create_connection()
    s3_config.delete_key(s3, a3bucketName, result[0]['image'])



def categories_list_all():
    records = []
    if check_table_availability('categories'):
        table = dynamodb.Table('categories')
        response = table.scan(
            ProjectionExpression="categoryId, categoryName"
        )

        for i in response['Items']:
            records.append([i['categoryId'],i['categoryName']])

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression="categoryId,categoryName",
                ExclusiveStartKey=response['LastEvaluatedKey']
            )

            for i in response['Items']:
                records.append([i['categoryId'],i['categoryName']])
        return records
    else:
        return records



def youtuber_list_all():
    records = []
    if check_table_availability('youtubers'):
        table = dynamodb.Table('youtubers')
        response = table.scan(
            ProjectionExpression="youtuberId, youtuberName"
        )

        for i in response['Items']:
            records.append([i['youtuberId'],i['youtuberName']])

        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression="youtuberId,youtuberName",
                ExclusiveStartKey=response['LastEvaluatedKey']
            )

            for i in response['Items']:
                records.append([i['youtuberId'],i['youtuberName']])
        return records
    else:
        return records