#!/usr/bin/env python
#-*- encoding: utf-8 -*-

import boto3
import botocore
import os
import json
import urllib

        
def S3_copy_file(src_bucket,src_key,dst_bucket,dst_key):
    
    session = boto3.session.Session(region_name='us-east-1')
    s3 = session.resource('s3')
    copy_source = {
      'Bucket': f'{src_bucket}',
      'Key': f'{src_key}'
        }
    try:
        bucket = s3.Bucket(dst_bucket)
        bucket.copy(copy_source, dst_key) 
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise


def lambda_handler(event,context):
    
    print("Received event: " + json.dumps(event, indent=2))
    src_bucket = event['Records'][0]['s3']['bucket']['name']
    src_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    environment = os.environ['environment']
    dst_bucket = f"uala-col-integrator-datalake-{environment}"
    provider_name = src_bucket.split("-")[-2]
    file_name = src_key.split("/")[-1]
    dst_key  = f"{provider_name}/{file_name}"
 
    print(f"Copying unencrypted file from bucket: {src_bucket} to: {dst_bucket}")
    S3_copy_file(src_bucket,src_key,dst_bucket,dst_key)
