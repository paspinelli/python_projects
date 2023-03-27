#!/usr/bin/env python
#-*- encoding: utf-8 -*-

import pysftp as sftp
import boto3
import botocore
import json
import os
import urllib

def get_secret_pem():
    secret_name=os.environ['pem_secret_name']
    client = boto3.client(service_name= 'secretsmanager',region_name= 'us-east-1')
    credentials = client.get_secret_value(SecretId=secret_name)
    return credentials['SecretString']

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

def lambda_handler(event,context):

    sftp_user_name = os.environ['sftp_user_name'] 
    sftp_url = os.environ['sftp_url']

    print("Received event: " + json.dumps(event, indent=2))
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    bucket_key_name = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    local_file = bucket_key_name.split("/")[-1]
 
    print(f"Downloading file from bucket: {bucket_name} and key: {bucket_key_name}")
    S3_download_file(bucket_name,bucket_key_name,local_file)
    
    #Setting options for sftp connection
    cnopts = sftp.CnOpts()
    cnopts.hostkeys = None
    #Creating pem file
    with open('/tmp/idemia.pem', 'w') as file:
        file.write(f"{get_secret_pem()}")
    #Atempting sftp connection
    try:
        s = sftp.Connection(host=f'{sftp_url}', username=f'{sftp_user_name}', port=22, private_key='/tmp/idemia.pem', cnopts=cnopts)
    except Exception as e:
        print (e)
    try:
        s.put(f'/tmp/{local_file}', preserve_mtime=True)
        print ("file uploaded")
    except Exception as e:
        print (e)

    print(f"Deleting local file: {local_file}")
    os.remove(f'/tmp/{local_file}')