#!/usr/bin/env python
#-*- encoding: utf-8 -*-

import boto3
import botocore
import gnupg
import os
import sys
import json
import urllib
from pprint import pprint


def get_secret():
    secret_name=os.environ['secret_name']
    client = boto3.client(service_name= 'secretsmanager',region_name= 'us-east-1')
    credentials = client.get_secret_value(SecretId=secret_name)
    return credentials['SecretString']
   
def import_key():
    gpg = gnupg.GPG(gnupghome='/tmp/')
    key_data = get_secret()
    import_result = gpg.import_keys(f'''{key_data}''')
    pprint(import_result.results)

def encrypt_file(local_file):
    
    INPUT=local_file
    OUTPUT=local_file.split(".")[0]
    gpg_key_id=os.environ['gpg_key_id']
    gpg = gnupg.GPG(gnupghome='/tmp/')
    with open(f"/tmp/{INPUT}", 'rb') as f:
        status = gpg.encrypt_file(f, recipients=[f'{gpg_key_id}'], output=f"/tmp/{OUTPUT}.txt.gpg",always_trust=True)
        print ('ok: ', status.ok)
        print ('status: ', status.status)
        print ('stderr: ', status.stderr)
        
def S3_download_file(bucket_name,bucket_key_name,local_file):
    
    session = boto3.session.Session(region_name='us-east-1')
    s3 = session.resource('s3')
    try:
        s3.Bucket(bucket_name).download_file(bucket_key_name, '/tmp/' f'{local_file}') 
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

def S3_upload_file(file_name, bucket, object_name):
    # Upload a file to an S3 bucket
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
    # Upload the file
    session = boto3.session.Session(region_name='us-east-1')
    s3_client = session.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True 

def lambda_handler(event, context):
    
    print("Received event: " + json.dumps(event, indent=2))
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    bucket_key_name = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    local_file = bucket_key_name.split("/")[-1]
    basename_file = local_file.split(".")[0]
    dst_prefix = os.environ['dst_prefix']
    file_to_upload = f"/tmp/{basename_file}.txt.gpg"
    object_name = f"{dst_prefix}/{basename_file}.txt.gpg"
 
    print(f"Downloading unecrypted file from bucket: {bucket_name} and key: {bucket_key_name} ")
    S3_download_file(bucket_name,bucket_key_name,local_file)
    print("Importing private key")
    import_key()
    print(f"Encrypting file {basename_file}.txt")
    encrypt_file(local_file)
    print(f"Uploading encrypted file to bucket: {bucket_name} in {object_name}")
    S3_upload_file(file_to_upload,bucket_name,object_name)
