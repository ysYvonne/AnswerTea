import boto3
import botocore
import os.path

# creating the connection for Amazon s3 and create a bucket to store all contents
def create_connection():
    s3 = boto3.resource('s3')
    return s3


# creating a bucket
def create_bucket(s3, Bucketname):
    s3.create_bucket(Bucket=Bucketname)


# Storing Data
def store_data(s3, Bucketname, filename, file):
    s3.Bucket(Bucketname).put_object(Key = filename,Body=file)

# Delete Key
def delete_key(s3,Bucketname, key):
    s3.Object(Bucketname, 'products/'+key).delete()

# Validate whether a bucket exists
def validate_bucket_exists(s3, Bucketname):
    bucket = s3.Bucket(Bucketname)
    exists = True
    try:
        s3.meta.client.head_bucket(Bucket=Bucketname)
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exists.
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            exists = False
    return exists


# Delete a Bucket
# All of the keys in a bucket must be deleted before the bucket itself can be deleted
def delete_bucket(s3, Bucketname):
    bucket = s3.Bucket(Bucketname)
    for key in bucket.objects.all():
        key.delete()
    bucket.delete()


# Iteration of Buckets and Keys, return list of all keys in buckets
def iterate_bucket(s3, Bucketname):
    keylist = []
    for bucket in s3.buckets.all():
        for key in bucket.objects.all():
            print(key.key)
            keylist.append(key)
    return keylist


# get one element from Bucket
def get_element_from_bucket(Bucketname, key):
    s3 = boto3.client('s3')
    s3_key = 'products/' + key
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': Bucketname, 'Key': s3_key})
    return url


# Download the file from S3
def download_file(s3, Bucketname,filename,username):
    if not(os.path.exists("app/static/user_upload/"+username+"/"+filename)):
        try:
            s3.Bucket(Bucketname).download_file("user_upload/"+username+"/"+filename,
                                                "app/static/user_upload/"+username+"/"+filename)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("user_upload/"+username+"/" + filename + "The object does not exist.")
            else:
                raise
